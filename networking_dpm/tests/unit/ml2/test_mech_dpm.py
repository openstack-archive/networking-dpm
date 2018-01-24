# Copyright (c) 2016 IBM Corp.
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

from neutron.tests.unit.plugins.ml2 import _test_mech_agent as base
from neutron_lib.api.definitions import portbindings


class DPMMechanismBaseTestCase(base.AgentMechanismBaseTestCase):
    VIF_TYPE = mech_dpm.VIF_TYPE_DPM_VSWITCH
    CAP_PORT_FILTER = False
    AGENT_TYPE = mech_dpm.AGENT_TYPE_DPM

    GOOD_MAPPINGS = {'fake_physical_network': ['fake_vswitch1',
                                               'fake_vswitch2']}
    GOOD_CONFIGS = {'adapter_mappings': GOOD_MAPPINGS}
    NO_VSWITCH_CONFIGS = {'adapter_mappings': {'fake_physical_network': []}}

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

    AGENTS_NO_VSWITCH = [{'alive': True,
                          'configurations': NO_VSWITCH_CONFIGS,
                          'host': 'host'}]

    def setUp(self):
        super(DPMMechanismBaseTestCase, self).setUp()
        self.driver = mech_dpm.DPMMechanismDriver()
        self.driver.initialize()


class DPMMechanismGenericTestCase(DPMMechanismBaseTestCase,
                                  base.AgentMechanismGenericTestCase):
    pass


class DPMMechanismFlatTestCase(DPMMechanismBaseTestCase,
                               base.AgentMechanismFlatTestCase):

    def test_type_flat_vif_details(self):
        context = base.FakePortContext(self.AGENT_TYPE,
                                       self.AGENTS,
                                       self.FLAT_SEGMENTS,
                                       vnic_type=self.VNIC_TYPE)
        self.driver.bind_port(context)
        vif_details = context._bound_vif_details
        self.assertIsNone(vif_details.get('vlan'))
        self.assertEqual("fake_vswitch1",
                         vif_details.get('object_id'))

    def test_no_vswitch_ids(self):

        context = base.FakePortContext(self.AGENT_TYPE,
                                       self.AGENTS_NO_VSWITCH,
                                       segments=self.FLAT_SEGMENTS,
                                       vnic_type=self.VNIC_TYPE)
        self.driver.bind_port(context)
        self._check_unbound(context)


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
        self.assertEqual("fake_vswitch1",
                         vif_details.get('object_id'))

    def test_no_vswitch_ids(self):
        context = base.FakePortContext(self.AGENT_TYPE,
                                       self.AGENTS_NO_VSWITCH,
                                       segments=self.VLAN_SEGMENTS,
                                       vnic_type=self.VNIC_TYPE)
        self.driver.bind_port(context)
        self._check_unbound(context)


class DPMMechanismMixedTestCase(DPMMechanismBaseTestCase):
    def test_vlan_flat_mixed(self):
        """Ensure that vif_details are unique per vif"""

        driver = mech_dpm.DPMMechanismDriver()
        flat_segment = DPMMechanismFlatTestCase.FLAT_SEGMENTS[1]
        vlan_segment = DPMMechanismVlanTestCase.VLAN_SEGMENTS[1]

        context = base.FakePortContext(self.AGENT_TYPE,
                                       self.AGENTS,
                                       segments=[vlan_segment, flat_segment],
                                       vnic_type=self.VNIC_TYPE)

        result = driver.try_to_bind_segment_for_agent(context, vlan_segment,
                                                      self.AGENT)
        self.assertTrue(result)
        self.assertEqual(1234, context._bound_vif_details.get("vlan"))

        result = driver.try_to_bind_segment_for_agent(context, flat_segment,
                                                      self.AGENT)
        self.assertTrue(result)
        self.assertIsNone(context._bound_vif_details.get("vlan"))
