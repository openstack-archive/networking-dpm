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

import sys

import mock
from oslo_config import cfg
from oslo_utils import uuidutils
from zhmcclient import HTTPError

from networking_dpm.ml2 import dpm_neutron_agent as dpm_agt
from networking_dpm.tests.unit import fake_zhmcclient

from neutron.common import topics
from neutron.tests import base


class TestPhysnetMapping(base.BaseTestCase):
    def test_get_all_vswitch_ids(self):
        mapping = dpm_agt.PhysicalNetworkMapping()
        vswitch1 = fake_zhmcclient._VSwitch({'object-id': 'id1'})
        vswitch2 = fake_zhmcclient._VSwitch({'object-id': 'id2'})
        vswitch3 = fake_zhmcclient._VSwitch({'object-id': 'id3'})
        mapping.add_vswitch('physnet1', vswitch1)
        mapping.add_vswitch('physnet1', vswitch2)
        mapping.add_vswitch('physnet2', vswitch3)
        self.assertItemsEqual([vswitch1, vswitch2, vswitch3],
                              mapping.get_all_vswitches())
        expected = {'physnet1': ['id1', 'id2'], 'physnet2': ['id3']}
        self.assertEqual(expected, mapping.get_mapping())


class TestDPMRPCCallbacks(base.BaseTestCase):
    def setUp(self):
        super(TestDPMRPCCallbacks, self).setUp()

        agent = mock.Mock()
        agent.mgr = mock.Mock()
        agent.mgr.interface_mappings = 'mappings'
        self.rpc = dpm_agt.DPMRPCCallBack(mock.Mock(), agent, mock.Mock())

    def test_port_update(self):
        port = {'id': 'port-id123', 'mac_address': 'mac1'}
        self.rpc.port_update(context=None, port=port)
        self.assertEqual(set(['mac1']), self.rpc.updated_devices)


class TestDPMManager(base.BaseTestCase):
    def setUp(self):
        super(TestDPMManager, self).setUp()
        self.mgr = dpm_agt.DPMManager(dpm_agt.PhysicalNetworkMapping(), 'cpc')

    def test_ensure_port_admin_state_up(self):
        pass

    def test__managed_by_agent_uuid(self):
        cfg.CONF.set_override('host', 'foo-host')
        # UUID with dashes
        self.assertTrue(self.mgr._managed_by_agent(fake_zhmcclient._NIC(
            {'name': 'a424c858-c006-421b-b0c2-5b9fa1a7a8af',
             'description': 'foo-host'})))
        # No dashes
        self.assertTrue(self.mgr._managed_by_agent(fake_zhmcclient._NIC(
            {'name': 'a424c858c006421bb0c25b9fa1a7a8af',
             'description': 'foo-host'})))
        # Generated uuid
        self.assertTrue(self.mgr._managed_by_agent(fake_zhmcclient._NIC(
            {'name': uuidutils.generate_uuid(),
             'description': 'foo-host'})))
        # Invalid uuid
        self.assertFalse(self.mgr._managed_by_agent(fake_zhmcclient._NIC(
            {'name': 'foo', 'description': 'foo-host'})))

    def test__managed_by_agent_host(self):
        cfg.CONF.set_override('host', 'foo-host')
        # Host part of description
        self.assertTrue(self.mgr._managed_by_agent(fake_zhmcclient._NIC(
            {'name': 'a424c858-c006-421b-b0c2-5b9fa1a7a8af',
             'description': 'contains-foo-host-in-description'})))

        # Exact match
        self.assertTrue(self.mgr._managed_by_agent(fake_zhmcclient._NIC(
            {'name': 'a424c858-c006-421b-b0c2-5b9fa1a7a8af',
             'description': 'foo-host'})))

        # No match
        self.assertFalse(self.mgr._managed_by_agent(fake_zhmcclient._NIC(
            {'name': 'a424c858-c006-421b-b0c2-5b9fa1a7a8af',
             'description': 'not-managed'})))

        # No description
        self.assertFalse(self.mgr._managed_by_agent(fake_zhmcclient._NIC(
            {'name': 'a424c858-c006-421b-b0c2-5b9fa1a7a8af',
             'description': ''})))

    def test_get_all_devices(self):
        hmc = {"cpcs": [{"object-id": "cpcpid", "vswitches": [
            {"backing-adapter-uri": "/api/adapters/uuid-1",
             "object-id": "vswitch-uuid-1",
             "port": 0,
             "nics": [{"name": "port-id-1"}, {"name": "port-id-3"}]},
            {"backing-adapter-uri": "/api/adapters/uuid-2",
             "object-id": "vswitch-uuid-2",
             "port": 1,
             "nics": [{"name": "port-id-2"}]},
            {"backing-adapter-uri": "/api/adapters/uuid-3",
             "object-id": "vswitch-uuid-3",
             "port": 0},
            {"backing-adapter-uri": "/api/adapters/not-configured",
             "object-id": "not-configured",
             "port": 1,
             "nics": [{"name": "not-configured"}]},
        ]}]}

        cpc = fake_zhmcclient.get_cpc(hmc)
        mapping = dpm_agt.PhysicalNetworkMapping()
        mapping.add_vswitch('physnet1', cpc.vswitches._get('vswitch-uuid-1'))
        mapping.add_vswitch('physnet1', cpc.vswitches._get('vswitch-uuid-2'))
        mapping.add_vswitch('physnet2', cpc.vswitches._get('vswitch-uuid-3'))

        self.mgr.cpc = cpc
        self.mgr.physnet_map = mapping
        with mock.patch.object(self.mgr, '_managed_by_agent',
                               return_value=True) as is_uuid:
            devices = self.mgr.get_all_devices()
            self.assertEqual(3, is_uuid.call_count)
        expected = ['port-id-1', 'port-id-2', 'port-id-3']
        self.assertItemsEqual(expected, devices)

    def test_get_all_devices_deleted_concurrently(self):
        hmc = {"cpcs": [{"object-id": "cpcpid", "vswitches": [
            {"backing-adapter-uri": "/api/adapters/uuid-1",
             "object-id": "vswitch-uuid-1",
             "port": 0,
             "nics": [{"name": "port-id-1"}]},
        ]}]}
        cpc = fake_zhmcclient.get_cpc(hmc)
        mapping = dpm_agt.PhysicalNetworkMapping()
        mapping.add_vswitch('physnet1', cpc.vswitches._get('vswitch-uuid-1'))

        self.mgr.cpc = cpc
        self.mgr.physnet_map = mapping
        with mock.patch.object(fake_zhmcclient._NIC, 'get_property',
                               side_effect=HTTPError(mock.Mock())):
            devices = self.mgr.get_all_devices()
            self.assertEqual(0, len(devices))

    @mock.patch.object(sys, 'exit')
    def test_get_all_devices_vswitch_failed(self, m_exit):
        hmc = {"cpcs": [{"object-id": "cpcpid"}]}

        self.mgr.cpc = fake_zhmcclient.get_cpc(hmc)
        vswitch = mock.Mock()
        self.mgr.physnet_map._vswitches = [vswitch]
        with mock.patch.object(vswitch, 'get_connected_nics',
                               side_effect=HTTPError(mock.Mock())):
            self.mgr.get_all_devices()
            m_exit.assert_called_with(1)

    def test_get_agent_configurations(self):
        mapping = dpm_agt.PhysicalNetworkMapping()
        vswitch1 = fake_zhmcclient._VSwitch({'object-id': 'id1'})
        vswitch2 = fake_zhmcclient._VSwitch({'object-id': 'id2'})
        vswitch3 = fake_zhmcclient._VSwitch({'object-id': 'id3'})
        mapping.add_vswitch('physnet1', vswitch1)
        mapping.add_vswitch('physnet1', vswitch2)
        mapping.add_vswitch('physnet2', vswitch3)
        self.assertItemsEqual([vswitch1, vswitch2, vswitch3],
                              mapping.get_all_vswitches())

        self.mgr.physnet_map = mapping
        expected = {'adapter_mappings':
                    {'physnet1': ['id1', 'id2'], 'physnet2': ['id3']}}
        self.assertEqual(expected, self.mgr.get_agent_configurations())

    def test_get_agent_id(self):
        cfg.CONF.set_override('host', 'foo')
        self.assertEqual("dpm-foo", self.mgr.get_agent_id())

    def test_get_extension_driver_type(self):
        self.assertEqual('dpm', self.mgr.get_extension_driver_type())

    def test_get_rpc_callbacks(self):
        context = mock.Mock()
        agent = mock.Mock()
        sg_agent = mock.Mock()
        obj = self.mgr.get_rpc_callbacks(context, agent, sg_agent)
        self.assertIsInstance(obj, dpm_agt.DPMRPCCallBack)

    def test_get_rpc_consumers(self):
        consumers = [[topics.PORT, topics.UPDATE],
                     [topics.SECURITY_GROUP, topics.UPDATE]]
        self.assertEqual(consumers, self.mgr.get_rpc_consumers())

    def test_plug_interface(self):
        self.assertTrue(self.mgr.plug_interface('network_id',
                                                'network_segment', 'mac1',
                                                'device_owner'))


class TestDPMMain(base.BaseTestCase):

    def test__validate_firewall_driver(self):
        valid_drivers = ['neutron.agent.firewall.NoopFirewallDriver',
                         'noop']
        for driver in valid_drivers:
            cfg.CONF.set_override('firewall_driver', driver, 'SECURITYGROUP')
            dpm_agt._validate_firewall_driver()

    @mock.patch.object(sys, 'exit')
    def test__validate_firewall_driver_invalid(self, mock_exit):
        cfg.CONF.set_override('firewall_driver', 'foo', 'SECURITYGROUP')
        dpm_agt._validate_firewall_driver()
        mock_exit.assert_called_with(1)

    def test__get_physnet_vswitch_map(self):
        conf_mapping = {'physnet1': {'uuid-1': None},
                        'physnet2': {'uuid-2': 1},
                        'physnet3': {'uuid-3': 0}}
        cfg.CONF.set_override('physical_adapter_mappings', conf_mapping,
                              group='dpm')
        expected = {'physnet1': ['vswitch-uuid-1'],
                    'physnet2': ['vswitch-uuid-2'],
                    'physnet3': ['vswitch-uuid-3']}
        hmc = {"cpcs": [{"object-id": "cpcpid", "vswitches": [
            {"backing-adapter-uri": "/api/adapters/uuid-1",
             "object-id": "vswitch-uuid-1",
             "port": 0},
            {"backing-adapter-uri": "/api/adapters/uuid-2",
             "object-id": "vswitch-uuid-2",
             "port": 1},
            {"backing-adapter-uri": "/api/adapters/uuid-3",
             "object-id": "vswitch-uuid-3",
             "port": 0}
        ]}]}
        cpc = fake_zhmcclient.get_cpc(hmc)
        actual = dpm_agt._get_physnet_vswitch_map(cpc).get_mapping()

        # Cannot use assertDictEqual as order of list is not guaranteed
        self.assertItemsEqual(expected['physnet1'], actual['physnet1'])
        self.assertItemsEqual(expected['physnet2'], actual['physnet2'])
        self.assertItemsEqual(expected['physnet3'], actual['physnet3'])

    @mock.patch.object(sys, 'exit')
    def test__get_physnet_vswitch_map_adapter_not_found(self, m_exit):
        mapping = {'physnet1': {'not-found': None}}
        cfg.CONF.set_override('physical_adapter_mappings', mapping,
                              group='dpm')
        hmc = {"cpcs": [{"object-id": "cpcpid", "vswitches": []}]}
        cpc = fake_zhmcclient.get_cpc(hmc)
        dpm_agt._get_physnet_vswitch_map(cpc)
        m_exit.assert_called_with(1)

    @mock.patch.object(sys, 'exit')
    def test__get_physnet_vswitch_map_empty(self, m_exit):
        mapping = {}
        cfg.CONF.set_override('physical_adapter_mappings', mapping,
                              group='dpm')
        dpm_agt._get_physnet_vswitch_map(mock.Mock())
        m_exit.assert_called_with(1)

    @mock.patch.object(sys, 'exit')
    def test__get_physnet_vswitch_map_multiple_adapters(self, m_exit):
        mapping = {'physnet1': {'uuid-1': None, 'uuid-3': 0}}
        cfg.CONF.set_override('physical_adapter_mappings', mapping,
                              group='dpm')
        dpm_agt._get_physnet_vswitch_map(mock.Mock())
        m_exit.assert_called_with(1)

    def test__get_cpc_found(self):
        hmc = {"cpcs": [{"name": "EURANSE2"}]}
        client = fake_zhmcclient.get_client(hmc)
        cpc = dpm_agt._get_cpc(client, 'EURANSE2')
        self.assertEqual("EURANSE2", cpc.get_property("name"))

    def test__get_cpc_not_dpm(self):
        hmc = {"cpcs": [{"name": "EURANSE2", "dpm_enabled": False}]}
        client = fake_zhmcclient.get_client(hmc)

        with mock.patch.object(sys, 'exit') as m_sys:
            dpm_agt._get_cpc(client, 'EURANSE2')
            m_sys.assert_called_with(1)

    def test__get_cpc_not_found(self):
        hmc = {"cpcs": [{"name": "foo"}]}
        client = fake_zhmcclient.get_client(hmc)
        with mock.patch.object(sys, 'exit') as m_sys:
            dpm_agt._get_cpc(client, 'EURANSE2')
            m_sys.assert_called_with(1)
