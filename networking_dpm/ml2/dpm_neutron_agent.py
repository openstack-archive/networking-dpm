# Copyright (c) 2016 IBM Corp.
#
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import re
from requests.packages import urllib3
import sys

from oslo_log import log as logging
import oslo_messaging
from oslo_service import service
import zhmcclient

from networking_dpm.ml2 import config
from networking_dpm.ml2 import constants as const
from networking_dpm.ml2.mech_dpm import AGENT_TYPE_DPM

from neutron._i18n import _LE
from neutron._i18n import _LI
from neutron._i18n import _LW
from neutron.api.rpc.handlers import securitygroups_rpc as sg_rpc
from neutron.common import config as common_config
from neutron.common import topics
from neutron.plugins.ml2.drivers.agent import _agent_manager_base as amb
from neutron.plugins.ml2.drivers.agent import _common_agent as ca

CONF = config.cfg.CONF
LOG = logging.getLogger(__name__)

NIC_OWNER_OPENSTACK = 'OpenStack'
DPM_AGENT_BINARY = "neutron-dpm-agent"
EXTENSION_DRIVER_TYPE = 'dpm'
ADAPTER_URI = "/api/adapters/"

# TODO(andreas_s): Suppressing the following warning thrown by urllib3 used by
# zhmcclient: "InsecureRequestWarning: Unverified HTTPS request is being made.
# Adding certificate verification is strongly advised. See:
# https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings"
urllib3.disable_warnings()


class PhysicalNetworkMapping(object):
    """Mapping of physical networks to vswitches

    Used by
    * the regular notifications sent to the Neutron server
    * the polling against the HMC for new NICs
    """

    def __init__(self, cpc):
        self._cpc = cpc
        self._vswitches = []
        self._physnet_mapping = {}

    def _get_vswitch(self, adapter_id, port):
        try:
            # TODO(andreas_s): Optimize in zhmcclient - For 'find' the
            # whole list of items is retrieved
            return self._cpc.vswitches.find(**{
                'backing-adapter-uri': ADAPTER_URI + adapter_id,
                'port': port
            })
        except zhmcclient.NotFound:
            LOG.error(
                _LE("No vswitch object for adapter/port combination "
                    "%(adapt)s/%(port)s found. Agent terminated!"),
                {'adapt': adapter_id, 'port': port}
            )
            sys.exit(1)

    def _add_vswitch(self, physnet, adapter_id, port):
        vswitch = self._get_vswitch(adapter_id, port)
        self._vswitches.append(vswitch)
        if self._physnet_mapping.get(physnet):
            # TODO(andreas_s): Lift this restriction
            LOG.error(_LE("Multiple vswitches for physical network "
                          "%(net)s defined but only a single vswitch "
                          "definition per physical network is supported."
                          "Agent terminated!"),
                      {'net': physnet})
            sys.exit(1)
        self._physnet_mapping[physnet] = [vswitch.get_property('object-id')]

    def _get_adapter(self, adapter_id):
        try:
            # TODO(andreas_s): Optimize in zhmcclient - For 'find' the
            # whole list of items is retrieved
            return self._cpc.adapters.find(**{'object-id': adapter_id})
        except zhmcclient.NotFound:
            LOG.error(_LE("Configured adapter %s could not be "
                          "found. Please update the agent "
                          "configuration. Agent terminated!"),
                      adapter_id)
            sys.exit(1)

    @staticmethod
    def _validate_adapter_type(adapter):
        adapt_type = adapter.get_property('type')
        if adapt_type not in ['osd', 'hipersockets']:
            LOG.error(_LE("Configured adapter %s is not an OSA "
                          "or a hipersockets adapter. Please update "
                          "the agent configuration. Agent "
                          "terminated!"), adapter)
            sys.exit(1)

    @staticmethod
    def _validate_adapter_port(adapter, port):
        try:
            # TODO(andreas_s): Optimize in zhmcclient - For 'find' the
            # whole list of items is retrieved
            # TODO(andreas_s): zhmcclient requires the port-element-id as
            # string. Int results in an NotFound Error.
            # See https://github.com/zhmcclient/python-zhmcclient/issues/125
            adapter.ports.find(**{'element-id': str(port)})
        except zhmcclient.NotFound:
            LOG.error(_LE("Configured port %(port)s for adapter "
                          "%(adapt)s does not exist. Please update "
                          "the agent configuration. Agent "
                          "terminated!"), {'adapt': adapter,
                                           'port': port})
            sys.exit(1)

    @staticmethod
    def _parse_config_line(line):
        result = line.split(":")
        # TODO(andreas_s): Validate line
        net = result[0]
        adapter_id = result[1]
        # If no port-element-id was defined, default to 0
        # result[2] can also be '' - handled by 'and result[2]'
        port = int(result[2] if len(result) == 3 and result[2] else 0)
        return net, adapter_id, port

    @staticmethod
    def _get_interface_mapping_conf():
        interface_mappings = CONF.dpm.physical_network_adapter_mappings

        if not interface_mappings:
            LOG.error(_LE("physical_adapter_mappings dpm configuration not "
                          "specified or empty value provided. Agent "
                          "terminated!"))
            sys.exit(1)

        return interface_mappings

    @staticmethod
    def create_mapping(cpc):
        mapping = PhysicalNetworkMapping(cpc)
        interface_mappings = mapping._get_interface_mapping_conf()

        for entry in interface_mappings:
            net, adapter_uuid, port = \
                PhysicalNetworkMapping._parse_config_line(entry)

            adapter = mapping._get_adapter(adapter_uuid)
            mapping._validate_adapter_type(adapter)
            mapping._validate_adapter_port(adapter, port)
            mapping._add_vswitch(net, adapter_uuid, port)
        return mapping

    def get_all_vswitches(self):
        """Get a list of all vswitch objects

        :return : list of zhmcclient vswitch objects
        """
        return self._vswitches

    def get_mapping(self):
        """Get the physnet/vswitch mapping for reports to the Neutron server

        :return : physical network / list of vswitch_ids mapping
        :rtype : dict of lists of strings
        """
        return self._physnet_mapping


class DPMRPCCallBack(sg_rpc.SecurityGroupAgentRpcCallbackMixin,
                     amb.CommonAgentManagerRpcCallBackBase):
    target = oslo_messaging.Target(version='1.4')

    def port_update(self, context, **kwargs):
        port = kwargs['port']
        LOG.debug("port_update received for port %s ", port)
        mac = port['mac_address']
        # Put the device name in the updated_devices set.
        # Do not store port details, as if they're used for processing
        # notifications there is no guarantee the notifications are
        # processed in the same order as the relevant API requests.
        self.updated_devices.add(mac)


class DPMManager(amb.CommonAgentManagerBase):
    def __init__(self, physnet_mapping, cpc, vswitches):
        self.physnet_map = physnet_mapping
        self.vswitches = vswitches
        self.cpc = cpc

    def ensure_port_admin_state(self, device, admin_state_up):
        # Setting a port up/down is not supported by Neutron DPM agent. Ports
        # are always up.
        pass

    def get_agent_configurations(self):
        return {'adapter_mappings': self.physnet_map}

    def get_agent_id(self):
        return 'dpm-%s' % CONF.host

    def get_devices_modified_timestamps(self, devices):
        # TODO(andreas_s): this should be implemented to detect
        # rapid Nova instance rebuilds.
        return {}

    @staticmethod
    def _managed_by_agent(nic):
        """Verifies if a NIC is supposed to be managed by this agent

        On NIC creation, Nova adds the following to the NICs description
        * Identifier 'OpenStack' at the beginning
        * Neutron ports MAC 'mac=xx:xx:xx:xx:xx:xx'
        * Host identifier of the CPCSubset 'host-id=foo'

        This method is able determine along those parameters if a NIC
        object should be managed by this agent or not.

        :param nic: The nic that should be checked
        :type nic: zhmcclient._NIC
        :return: True if NIC is supposed to be managed by this agent
        :rtype: bool
        """
        # Nova sets the Name of the NIC object to the UUID of the Neutron port
        description = nic.get_property('description')
        if not description.startswith(NIC_OWNER_OPENSTACK):
            LOG.debug("NIC %(nic)s seems not managed by OpenStack, as its "
                      "description %(desc)s does not start with the NIC OWNER "
                      "identifier %(noo)s!",
                      {'nic': nic, 'desc': description,
                       'noo': NIC_OWNER_OPENSTACK})
            return False

        # Nova adds the host identifier to the NICs description attribute
        if CONF.host not in nic.get_property('description'):
            LOG.debug("NIC %(nic)s not managed by this host %(host)s. "
                      "Skipping.", {'nic': nic, 'host': CONF.host})
            return False

        # check if mac is present
        if not DPMManager._extract_mac(nic):
            LOG.debug("Description of NIC %s does not contain a valid mac "
                      "address. Therefore it seems not to be managed by this"
                      "Neutron agent. Skipping!", nic)
            return False
        return True

    @staticmethod
    def _extract_mac(nic):
        description = nic.get_property('description')
        mac_regex = 'mac=(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))'
        match = re.search(mac_regex, description)
        if match:
            return match.group(1)
        # TODO(andreas_s): throw exception

    def _filter_agent_managed_nic_macs(self, nics):
        macs = set()
        for nic in nics:
            try:
                if self._managed_by_agent(nic):
                    macs.add(self._extract_mac(nic))
            except zhmcclient.HTTPError as http_error:
                if (http_error.http_status ==
                        const.HTTP_STATUS_NOT_FOUND):
                    LOG.debug("NIC %s got deleted concurrently."
                              "Continuing...", nic)
                else:
                    LOG.warning(_LW("NIC %(nic)s will be reported as "
                                    "'DOWN' due to error: %(err)s"),
                                {'nic': nic, 'err': http_error})
        return macs

    def get_all_devices(self):
        """Getting all NICs that are managed by this agent

        :return: List of Neutron port MACs for which NICs exist
        """
        devices = set()

        for vswitch in self.vswitches:
            try:
                nics = vswitch.get_connected_nics()
                devices = devices.union(
                    self._filter_agent_managed_nic_macs(nics))
            except zhmcclient.ConnectionError as con_err:
                LOG.error(_LE(
                    "%(message)s, %(details)s. Lost connection to HMC of "
                    "CPC %(cpc)s. All NICs of this CPC and its corresponding "
                    "Neutron ports wil be reported as 'DOWN'."),
                    {"cpc": self.cpc, "message": con_err,
                     "details": con_err.details})

            except zhmcclient.HTTPError as http_error:
                if http_error.http_status == const.HTTP_STATUS_NOT_FOUND:
                    LOG.error(_LE(
                        "An unrecoverable error occurred: %(err)s "
                        "DPM vSwitch object %(vswitch)s is "
                        "not available anymore. This can happen if "
                        "the corresponding adapter got removed "
                        "from the system or the corresponding "
                        "hipersockets network got deleted. Please "
                        "check the physical_network_adapter_mappings "
                        "configuration and start the "
                        "agent again. Agent terminated!"),
                        {'vswitch': vswitch, 'err': http_error})
                    # Need to exit with sys.exit, as calling code catches
                    # exceptions
                    sys.exit(1)

                LOG.warning(_LW("An error occurred while retrieving the "
                                "connected nics of vswitch %(vswitch)s: "
                                "%(err)s. All NICs of this vswitch will "
                                "be reported as 'DOWN'."),
                            {'vswitch': vswitch, 'err': http_error})
        return devices

    def get_extension_driver_type(self):
        return EXTENSION_DRIVER_TYPE

    def get_rpc_callbacks(self, context, agent, sg_agent):
        return DPMRPCCallBack(context, agent, sg_agent)

    def get_rpc_consumers(self):
        # TODO(andreas_s): remove security group update?
        consumers = [[topics.PORT, topics.UPDATE],
                     [topics.SECURITY_GROUP, topics.UPDATE]]
        return consumers

    def plug_interface(self, network_id, network_segment, device,
                       device_owner):
        return True

    def setup_arp_spoofing_protection(self, device, device_details):
        # Arp spoofing protection is not supported by Neutron DPM agent
        pass

    def delete_arp_spoofing_protection(self, devices):
        # Arp spoofing protection is not supported by Neutron DPM agent
        pass

    def delete_unreferenced_arp_protection(self, current_devices):
        # Arp spoofing protection is not supported by Neutron DPM agent
        pass


def _validate_firewall_driver():
    fw_driver = CONF.SECURITYGROUP.firewall_driver
    supported_fw_drivers = ['neutron.agent.firewall.NoopFirewallDriver',
                            'noop']
    if fw_driver not in supported_fw_drivers:
        LOG.error(_LE('Unsupported configuration option for "SECURITYGROUP.'
                      'firewall_driver"! Only the NoopFirewallDriver is '
                      'supported by DPM agent, but "%s" is configured. '
                      'Set the firewall_driver to "noop" and start the '
                      'agent again. Agent terminated!'),
                  fw_driver)
        sys.exit(1)


def _get_cpc(client, cpc_oid):
    try:
        cpc = client.cpcs.find(**{'object-id': cpc_oid})
        if cpc.dpm_enabled:
            return cpc
        LOG.error(_LE("CPC %s not in DPM mode.") % cpc_oid)
    except zhmcclient.NotFound:
        LOG.error(_LE("Could not find CPC with object-id %s") % cpc_oid)
    sys.exit(1)


def setup_logging():
    """Sets up the logging options."""

    # We use the oslo.log default log levels but set the log level for
    # zhmcclient library to warning
    logging.set_defaults(default_log_levels=logging.get_default_log_levels() +
                         ["zhmcclient=WARNING"])
    logging.setup(CONF, 'neutron')
    LOG.info(_LI("Logging enabled!"))
    LOG.info(_LI("%(prog)s"), {'prog': sys.argv[0]})
    LOG.debug("command line: %s", " ".join(sys.argv))


def main():
    common_config.init(sys.argv[1:])
    setup_logging()

    hmc = CONF.dpm.hmc
    userid = CONF.dpm.hmc_username
    password = CONF.dpm.hmc_password
    cpc_oid = CONF.dpm.cpc_object_id

    session = zhmcclient.Session(hmc, userid, password)
    client = zhmcclient.Client(session)
    cpc = _get_cpc(client, cpc_oid)

    physnet_vswitch_map = PhysicalNetworkMapping.create_mapping(cpc)
    manager = DPMManager(physnet_vswitch_map.get_mapping(), cpc,
                         physnet_vswitch_map.get_all_vswitches())

    polling_interval = CONF.AGENT.polling_interval
    quitting_rpc_timeout = CONF.AGENT.quitting_rpc_timeout
    agent = ca.CommonAgentLoop(manager, polling_interval,
                               quitting_rpc_timeout,
                               AGENT_TYPE_DPM,
                               DPM_AGENT_BINARY)
    LOG.info(_LI("Agent initialized successfully, now running... "))
    service.launch(CONF, agent).wait()
