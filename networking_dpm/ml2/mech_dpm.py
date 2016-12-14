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

from oslo_log import log

from neutron.extensions import portbindings
from neutron.plugins.common import constants as p_constants
from neutron.plugins.ml2 import driver_api as api
from neutron.plugins.ml2.drivers import mech_agent

LOG = log.getLogger(__name__)

AGENT_TYPE_DPM = 'DPM agent'
VIF_TYPE_DPM = 'dpm'
VIF_DETAILS_VSWITCH_ID = 'vswitch_id'
VLAN_MODE = 'vlan_mode'
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
            VIF_TYPE_DPM,
            {portbindings.CAP_PORT_FILTER: False})

    def get_allowed_network_types(self, agent):
        return [p_constants.TYPE_FLAT, p_constants.TYPE_VLAN]

    def get_mappings(self, agent):
        return agent['configurations'].get('adapter_mappings', {})

    def check_vlan_transparency(self, context):
        """DPM driver vlan transparency support."""
        return False

    def try_to_bind_segment_for_agent(self, context, segment, agent):
        if self.check_segment_for_agent(segment, agent):
            vif_details_segment = self.vif_details
            mappings = self.get_mappings(agent)
            vswitch_ids = mappings[segment['physical_network']]
            # TODO(andreas_s): In the first release only a single adapter
            # per physical network is supported
            vswitch_id = vswitch_ids[0]
            network_type = segment[api.NETWORK_TYPE]

            if network_type == p_constants.TYPE_VLAN:
                vlan_id = segment[api.SEGMENTATION_ID]
                vif_details_segment['vlan'] = vlan_id
                # In the initial release only inband VLANs are supported.
                # Nova uses this field to setup the VLANs accordingly.
                vif_details_segment[VLAN_MODE] = VLAN_MODE_INBAND

            vif_details_segment[VIF_DETAILS_VSWITCH_ID] = vswitch_id
            LOG.debug("DPM vif_details added to context binding: %s",
                      vif_details_segment)
            context.set_binding(segment[api.ID], self.vif_type,
                                vif_details_segment)
            return True
        return False
