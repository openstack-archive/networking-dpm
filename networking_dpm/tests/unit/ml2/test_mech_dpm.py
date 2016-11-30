# Copyright (c) 2015 IBM Corp.
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

from networking_dpm.ml2 import mech_dpm

from neutron.extensions import portbindings
from neutron.plugins.ml2 import driver_api as api
from neutron.plugins.ml2.drivers.macvtap.mech_driver import mech_macvtap
from neutron.tests.unit.plugins.ml2 import _test_mech_agent as base


class DPMMechanismBaseTestCase(base.AgentMechanismBaseTestCase):
    VIF_TYPE = mech_dpm.VIF_TYPE_DPM
    CAP_PORT_FILTER = False
    AGENT_TYPE = mech_dpm.AGENT_TYPE_DPM

    GOOD_MAPPINGS = {'fake_physical_network': 'fake_if'}
    GOOD_CONFIGS = {'adapter_mappings': GOOD_MAPPINGS}

    BAD_MAPPINGS = {'wrong_physical_network': 'wrong_if'}
    BAD_CONFIGS = {'adapter_mappings': BAD_MAPPINGS}

    AGENT = {'alive': True,
             'configurations': GOOD_CONFIGS,
             'host': 'host'}
    AGENTS = [AGENT]

    AGENTS_DEAD = [{'alive': False,
                    'configurations': GOOD_CONFIGS,
                    'host': 'dead_host'}]
    AGENTS_BAD = [{'alive': False,
                   'configurations': GOOD_CONFIGS,
                   'host': 'bad_host_1'},
                  {'alive': True,
                   'configurations': BAD_CONFIGS,
                   'host': 'bad_host_2'}]

    def setUp(self):
        super(DPMMechanismBaseTestCase, self).setUp()
        self.driver = mech_dpm.DPMMechanismDriver()
        self.driver.initialize()


class DPMMechanismGenericTestCase(DPMMechanismBaseTestCase,
                                  base.AgentMechanismGenericTestCase):
    pass


class MacvtapMechanismFlatTestCase(DPMMechanismBaseTestCase,
                                   base.AgentMechanismFlatTestCase):
    MIGRATION_SEGMENT = {api.ID: 'flat_segment_id',
                         api.NETWORK_TYPE: 'flat',
                         api.PHYSICAL_NETWORK: 'fake_physical_network'}

    def test_type_flat_vif_details(self):
        context = base.FakePortContext(self.AGENT_TYPE,
                                  self.AGENTS,
                                  self.FLAT_SEGMENTS,
                                  vnic_type=self.VNIC_TYPE)
        self.driver.bind_port(context)
        vif_details = context._bound_vif_details
        self.assertIsNone(vif_details.get(portbindings.VIF_DETAILS_VLAN))
        self.assertEqual("fake_if",
                         vif_details.get(mech_dpm.VIF_DETAILS_VSWITCH_ID))


class DPMMechanismVlanTestCase(DPMMechanismBaseTestCase,
                               base.AgentMechanismVlanTestCase):

    def test_type_vlan_vif_details(self):
        context = base.FakePortContext(self.AGENT_TYPE,
                                  self.AGENTS,
                                  self.VLAN_SEGMENTS,
                                  vnic_type=self.VNIC_TYPE)
        self.driver.bind_port(context)
        vif_details = context._bound_vif_details

        self.assertEqual(1234, vif_details.get(portbindings.VIF_DETAILS_VLAN))
        self.assertEqual("fake_if",
                         vif_details.get(mech_dpm.VIF_DETAILS_VSWITCH_ID))
