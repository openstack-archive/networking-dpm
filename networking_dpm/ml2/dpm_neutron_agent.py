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

from requests.packages import urllib3
import sys


from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging
from oslo_service import service
from oslo_utils import uuidutils
import zhmcclient

from networking_dpm.ml2 import config  # noqa
from networking_dpm.ml2.mech_dpm import AGENT_TYPE_DPM

from neutron._i18n import _LE
from neutron._i18n import _LI
from neutron.api.rpc.handlers import securitygroups_rpc as sg_rpc
from neutron.common import config as common_config
from neutron.common import topics
from neutron.plugins.ml2.drivers.agent import _agent_manager_base as amb
from neutron.plugins.ml2.drivers.agent import _common_agent as ca

LOG = logging.getLogger(__name__)

DPM_AGENT_BINARY = "neutron-dpm-agent"
EXTENSION_DRIVER_TYPE = 'dpm'
ADAPTER_URI = "/api/adapters/"

# TODO(andreas_s): Suppressing the following warning thrown by urllib3 used by
# zhmcclient: "InsecureRequestWarning: Unverified HTTPS request is being made.
# Adding certificate verification is strongly advised. See:
# https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings"
urllib3.disable_warnings()


class DPMRPCCallBack(sg_rpc.SecurityGroupAgentRpcCallbackMixin,
                     amb.CommonAgentManagerRpcCallBackBase):
    # Set RPC API version to 1.0 by default.
    # history
    #   1.1 Support Security Group RPC
    #   1.3 Added param devices_to_update to security_groups_provider_updated
    #   1.4 Added support for network_update
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
    def __init__(self, physnet_adapter_map, cpc):
        self.physnet_adapter_map = physnet_adapter_map
        self.mac_device_name_mappings = dict()
        self.cpc = cpc

    def ensure_port_admin_state(self, device, admin_state_up):
        # Setting a port up/down is not supported by Neutron DPM agent. Ports
        # are always up.
        pass

    def get_agent_configurations(self):
        return {'adapter_mappings': self.physnet_adapter_map}

    def get_agent_id(self):
        return 'dpm-%s' % cfg.CONF.host

    def get_devices_modified_timestamps(self, devices):
        # TODO(kevinbenton): this should be implemented to detect
        # rapid Nova instance rebuilds.
        return {}

    @staticmethod
    def _managed_by_agent(nic):
        """Verifies if a NIC is supposed to be managed by this agent

        On NIC creation, Nova adds the
        * Neutron ports UUID as NICs name (exact match)
        * Host identifier of the CPCSubset to the NICs description

        This method is able determine along those parameters if a NIC
        object should be managed by this agent or not.

        :param nic: The nic object returned by hmc client
        :return: True if NIC is supposed to be managed by this agent
        :rtype: bool
        """
        if not uuidutils.is_uuid_like(nic.get_property('name')):
            LOG.debug("NIC %(nic)s seems not managed by OpenStack, as name "
                      "%(name)s is not a UUID. Skipping.",
                      {'nic': nic, 'name': nic.get_property('name')})
            return False

        # Nova adds the host identifier to the NICs description attribute
        if cfg.CONF.host not in nic.get_property('description'):
            LOG.debug("NIC %(nic)s not managed by this host %(host)s. "
                      "Skipping.", {'nic': nic, 'host': cfg.CONF.host})
            return False
        return True

    def get_all_devices(self):
        """Getting all NICs that are managed by this agent

        :return: List of Neutron port UUID for which NICs exist
        """
        devices = set()
        for physnet_vswitches in self.physnet_adapter_map.values():
            for vswitch_id in physnet_vswitches:
                vswitch = self.cpc.vswitches.find(**{'object-id': vswitch_id})
                for nic in vswitch.get_connected_nics():
                    try:
                        # Nova stores the Neutron Port ID in the NICs name
                        # field
                        if self._managed_by_agent(nic):
                            devices.add(nic.get_property('name'))
                    except zhmcclient._exceptions.HTTPError:
                        # NIC got deleted concurrently
                        pass
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


def _get_physnet_vswitch_map(cpc):
    """Building the physical network - vswitch map

    It contains for each physical network a list of vswitch uuids. At the
    moment the list of vswitch uuids can contain only a single id. This shall
    be lifted in the future.

    :param cpc: A zhmcclient cpc object
    :return: Dict {physnet1:[vswitch_id],..}
    """
    interface_mappings = cfg.CONF.dpm.physical_adapter_mappings

    if not interface_mappings:
        LOG.error(_LE("physical_adapter_mappings dpm configuration not "
                      "specified or empty value provided. Agent terminated!"))
        sys.exit(1)

    mappings = {}

    for physnet, adapter_port_dict in interface_mappings.items():
        # TODO(andreas_s): Lift this restriction
        if len(adapter_port_dict) != 1:
            LOG.error(_LE("Multiple vswitches for physical network "
                          "%(net)s defined but only a single vswitch "
                          "definition per physical network is supported. "
                          "Agent terminated!"),
                      {'net': physnet})
            sys.exit(1)
        for adapter_uuid, port in adapter_port_dict.items():
            # If no port-element-id was defined, default to 0
            if not port:
                port = 0

            try:
                # As RoCE is not supported, we can directly work with the
                # virtual switch object
                # TODO(andreas_s): Optimize - For each vswitch the whole list
                # of vswitches and details for each vswitch are retrieved.
                vswitch = cpc.vswitches.find(**{
                    'backing-adapter-uri': ADAPTER_URI + adapter_uuid,
                    'port': port
                })
                if not mappings.get(physnet):
                    mappings[physnet] = []
                mappings[physnet].append(vswitch.get_property('object-id'))
            except zhmcclient._exceptions.NotFound:
                LOG.error(_LE("No vswitch object for adapter/port combination "
                              "%(adapt)s/%(port)s for physical network "
                              "%(net)s found. Agent terminated!"),
                          {'adapt': adapter_uuid, 'port': port, 'net': physnet}
                          )
                sys.exit(1)
    return mappings


def _validate_firewall_driver():
    fw_driver = cfg.CONF.SECURITYGROUP.firewall_driver
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


def _get_cpc(client, cpc_name):
    try:
        cpc = client.cpcs.find(name=cpc_name)
        if cpc.dpm_enabled:
            return cpc
        LOG.error(_LE("CPC %s not in DPM mode.") % cpc_name)
    except zhmcclient.NotFound:
        LOG.error(_LE("Could not find CPC %s") % cpc_name)
    sys.exit(1)


def setup_logging():
    """Sets up the logging options."""

    # We use the oslo.log default log levels but set the log level for
    # zhmcclient library to warning
    logging.set_defaults(default_log_levels=logging.get_default_log_levels() +
                         ["zhmcclient=WARNING"])
    logging.setup(cfg.CONF, 'neutron')
    LOG.info(_LI("Logging enabled!"))
    LOG.info(_LI("%(prog)s"), {'prog': sys.argv[0]})
    LOG.debug("command line: %s", " ".join(sys.argv))


def main():
    common_config.init(sys.argv[1:])
    setup_logging()

    hmc = cfg.CONF.dpm.hmc
    userid = cfg.CONF.dpm.hmc_username
    password = cfg.CONF.dpm.hmc_password
    cpc_name = cfg.CONF.dpm.cpc_name

    session = zhmcclient.Session(hmc, userid, password)
    client = zhmcclient.Client(session)
    cpc = _get_cpc(client, cpc_name)

    physnet_vswitch_map = _get_physnet_vswitch_map(cpc)
    manager = DPMManager(physnet_vswitch_map, cpc)

    polling_interval = cfg.CONF.AGENT.polling_interval
    quitting_rpc_timeout = cfg.CONF.AGENT.quitting_rpc_timeout
    agent = ca.CommonAgentLoop(manager, polling_interval,
                               quitting_rpc_timeout,
                               AGENT_TYPE_DPM,
                               DPM_AGENT_BINARY)
    LOG.info(_LI("Agent initialized successfully, now running... "))
    service.launch(cfg.CONF, agent).wait()
