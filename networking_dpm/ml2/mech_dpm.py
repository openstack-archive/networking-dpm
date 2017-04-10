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

from neutron_lib.api.definitions import portbindings
from oslo_log import log

from neutron._i18n import _LW
from neutron.plugins.common import constants as p_constants
from neutron.plugins.ml2 import driver_api as api
from neutron.plugins.ml2.drivers import mech_agent

LOG = log.getLogger(__name__)

AGENT_TYPE_DPM = 'DPM agent'
VIF_TYPE_DPM_VSWITCH = 'dpm_vswitch'
VIF_TYPE_DPM_ADAPTER = 'dpm_adapter'
VIF_DETAILS_OBJECT_ID = 'object_id'
VLAN_MODE_INBAND = 'inband'


class DPMMechanismDriver(mech_agent.SimpleAgentMechanismDriverBase):
    """Attach to networks using DPM L2 Agent.

    The DPMMechanismDriver integrates the ml2 plugin with the
    DPM L2 agent. Port binding with this driver requires the
    dpm agent to be running on the port's host, and that agent
    to have connectivity to at least one segment of the port's
    network.
    """

    def __init__(self):
        super(DPMMechanismDriver, self).__init__(
            AGENT_TYPE_DPM,
            [VIF_TYPE_DPM_VSWITCH, VIF_TYPE_DPM_ADAPTER],
            {portbindings.CAP_PORT_FILTER: False})

    def get_allowed_network_types(self, agent):
        return [p_constants.TYPE_FLAT]

    def get_mappings(self, agent):
        return agent.get('configurations', {}).get('adapter_mappings', {})

    def check_vlan_transparency(self, context):
        """DPM driver vlan transparency support."""
        return False

    def try_to_bind_segment_for_agent(self, context, segment, agent):
        if not self.check_segment_for_agent(segment, agent):
            return False
        physnet = segment['physical_network']

        object_ids = self.get_mappings(agent)[physnet]
        if not object_ids:
            LOG.warning(_LW("No Object-IDs found in agents %(agent)s mapping "
                            "for physical network %(net)s."), {'agent': agent,
                                                               'net': physnet})
            return False
        if len(object_ids) > 1:
            LOG.warning(_LW("More than one Object-ID for physical network "
                            "%(net)s on agent %(agent)s found but only a "
                            "single Object-ID is supported. Therefore the "
                            "first one is being chosen!"), {'agent': agent,
                                                            'net': physnet})
        # TODO(andreas_s): In the first release only a single adapter/vswitch
        # per physical network is supported
        object_id = object_ids[0]

        vif_details_segment = self.vif_details

        vif_details_segment[VIF_DETAILS_OBJECT_ID] = object_id
        # TODO(andreas_s): For RoCE Support add the port-element-id to the
        # vif_details
        LOG.debug("DPM vif_details added to context binding: %s",
                  vif_details_segment)
        # TODO(andreas_s) For RoCE Support VIF_TYPE_DPM_ADAPTER is required
        context.set_binding(segment[api.ID], VIF_TYPE_DPM_VSWITCH,
                            vif_details_segment)
        return True
