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
from zhmcclient import ConnectionError
from zhmcclient import HTTPError

from networking_dpm.ml2 import dpm_neutron_agent as dpm_agt
from networking_dpm.ml2.dpm_neutron_agent import (PhysicalNetworkMapping as
                                                  dpm_map)
from networking_dpm.tests.unit import fake_zhmcclient

from neutron.common import topics
from neutron.tests import base


class TestPhysnetMapping(base.BaseTestCase):

    def _test__parse_config_line(self, line, ex_net, ex_adapt, ex_port):
        net, adapt, port = dpm_map._parse_config_line(line)
        self.assertEqual(ex_net, net)
        self.assertEqual(ex_adapt, adapt)
        self.assertEqual(ex_port, port)

    def test__parse_config_line_default_to_zero(self):
        line = "foo:uuid:"
        self._test__parse_config_line(line, 'foo', 'uuid', 0)
        line = "foo:uuid"
        self._test__parse_config_line(line, 'foo', 'uuid', 0)

    def test__parse_config_line(self):
        line = "foo:uuid:1"
        self._test__parse_config_line(line, 'foo', 'uuid', 1)

    def test__get_interface_mapping_conf(self):
        test_mapping = ["physnet1:uuid1:1",
                        "physnet1:uuid2:1",
                        "physnet2:uuid3:1"
                        ]
        cfg.CONF.set_override('physical_network_adapter_mappings',
                              test_mapping, group='dpm')
        mapping = dpm_map(mock.Mock())
        self.assertEqual(test_mapping, mapping._get_interface_mapping_conf())

    def test_create_mapping(self):
        conf_mapping = ["physnet1:uuid-1:",
                        "physnet2:uuid-2:1",
                        "physnet3:uuid-3:0"
                        ]
        cfg.CONF.set_override('physical_network_adapter_mappings',
                              conf_mapping, group='dpm')
        expected = {'physnet1': ['vswitch-uuid-1'],
                    'physnet2': ['vswitch-uuid-2'],
                    'physnet3': ['vswitch-uuid-3']}

        adapters = [{'object-id': 'uuid-1', 'type': 'osd',
                     'ports': [{'element-id': 0}]},
                    {'object-id': 'uuid-2', 'type': 'osd',
                     'ports': [{'element-id': 1}]},
                    {'object-id': 'uuid-3', 'type': 'hipersockets',
                     'ports': [{'element-id': 0}]}]
        vswitches = [
            {"backing-adapter-uri": "/api/adapters/uuid-1",
             "object-id": "vswitch-uuid-1",
             "port": 0},
            {"backing-adapter-uri": "/api/adapters/uuid-2",
             "object-id": "vswitch-uuid-2",
             "port": 1},
            {"backing-adapter-uri": "/api/adapters/uuid-3",
             "object-id": "vswitch-uuid-3",
             "port": 0}]
        hmc = {"cpcs": [{"object-id": "cpcpid", "vswitches": vswitches,
                         "adapters": adapters}]}
        cpc = fake_zhmcclient.get_cpc(hmc)
        mapping = dpm_map.create_mapping(cpc)
        actual = mapping.get_mapping()
        self.assertItemsEqual(expected['physnet1'], actual['physnet1'])
        self.assertItemsEqual(expected['physnet2'], actual['physnet2'])
        self.assertItemsEqual(expected['physnet3'], actual['physnet3'])
        vswitch_list = mapping.get_all_vswitches()
        vswitch_ids = [vswitch.get_property('object-id')
                       for vswitch in vswitch_list]

        self.assertIn("vswitch-uuid-1", vswitch_ids)
        self.assertIn("vswitch-uuid-2", vswitch_ids)
        self.assertIn("vswitch-uuid-3", vswitch_ids)

    def test_create_mapping_invalid_adapter_type(self):
        cfg.CONF.set_override('physical_network_adapter_mappings',
                              ["physnet1:uuid-1:"],
                              group='dpm')
        hmc = {"cpcs": [{
            "object-id": "cpcpid",
            "adapters": [{'object-id': 'uuid-1', 'type': 'bad_type'}]}]}

        cpc = fake_zhmcclient.get_cpc(hmc)
        self.assertRaises(SystemExit,
                          dpm_map.create_mapping, cpc)

    def test_create_mapping_adapter_not_exists(self):
        conf_mapping = ['physnet1:not_exists:']
        cfg.CONF.set_override('physical_network_adapter_mappings',
                              conf_mapping, group='dpm')
        hmc = {"cpcs": [{
            "object-id": "cpcpid",
            "adapters": [{'object-id': 'other_adapter', 'type': 'osd'}]}]}

        cpc = fake_zhmcclient.get_cpc(hmc)
        self.assertRaises(SystemExit,
                          dpm_map.create_mapping, cpc)

    def test_create_mapping_adapter_port_not_exists(self):
        conf_mapping = ['physnet1:uuid-1:1']
        cfg.CONF.set_override('physical_network_adapter_mappings',
                              conf_mapping, group='dpm')
        hmc = {"cpcs": [{
            "object-id": "cpcpid",
            "adapters": [{'object-id': 'uuid-1', 'type': 'osd',
                          'ports': []}]}]}

        cpc = fake_zhmcclient.get_cpc(hmc)
        self.assertRaises(SystemExit,
                          dpm_map.create_mapping, cpc)

    def test_create_mapping_vswitch_not_exists(self):
        conf_mapping = ['physnet1:uuid-1:']
        cfg.CONF.set_override('physical_network_adapter_mappings',
                              conf_mapping, group='dpm')
        hmc = {"cpcs": [{
            "object-id": "cpcpid",
            "adapters": [{'object-id': 'uuid-1', 'type': 'osd'}]}]}

        cpc = fake_zhmcclient.get_cpc(hmc)
        self.assertRaises(SystemExit,
                          dpm_map.create_mapping, cpc)

    def test_create_mapping_no_config(self):
        cfg.CONF.set_override('physical_network_adapter_mappings', [],
                              group='dpm')
        self.assertRaises(SystemExit,
                          dpm_map.create_mapping,
                          mock.Mock())

    def test_create_mapping_multiple_adapters_per_physnet(self):
        mapping = ['physnet1:uuid-1:', 'physnet1:uuid-3:0']
        cfg.CONF.set_override('physical_network_adapter_mappings', mapping,
                              group='dpm')

        adapters = [{'object-id': 'uuid-1', 'type': 'osd'},
                    {'object-id': 'uuid-3', 'type': 'osd'}]
        hmc = {"cpcs": [{"object-id": "cpcpid", "vswitches": [
            {"backing-adapter-uri": "/api/adapters/uuid-1",
             "object-id": "vswitch-uuid-1",
             "port": 0},
            {"backing-adapter-uri": "/api/adapters/uuid-3",
             "object-id": "vswitch-uuid-3",
             "port": 0}], "adapters": adapters}]}
        cpc = fake_zhmcclient.get_cpc(hmc)
        self.assertRaises(SystemExit,
                          dpm_map.create_mapping,
                          cpc)


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
        self.mgr = dpm_agt.DPMManager({}, mock.Mock(), [])

    def test__managed_by_agent(self):
        cfg.CONF.set_override('host', 'foo-host')
        valid_mac_str = "mac=00:11:22:33:44:55:66"
        # Host and mac part of description
        self.assertTrue(self.mgr._managed_by_agent(fake_zhmcclient._NIC(
            {'description': 'OpenStackcontains-foo-host-in-description' +
                            valid_mac_str})))

        # Unicode
        self.assertTrue(self.mgr._managed_by_agent(fake_zhmcclient._NIC(
            {'description': u"OpenStack foo-host mac=00:11:22:33:44:55:66"})))

        # host missing
        self.assertFalse(self.mgr._managed_by_agent(fake_zhmcclient._NIC(
            {'description': 'OpenStacknot-managed' + valid_mac_str})))

        # mac missing
        self.assertFalse(self.mgr._managed_by_agent(fake_zhmcclient._NIC(
            {'description': 'OpenStack foo-host'})))

        # prefix missing
        self.assertFalse(self.mgr._managed_by_agent(fake_zhmcclient._NIC(
            {'description': 'foo-host' + valid_mac_str})))

        # No host match
        self.assertFalse(self.mgr._managed_by_agent(fake_zhmcclient._NIC(
            {'description': 'not-managed' + valid_mac_str})))

        # No description
        self.assertFalse(self.mgr._managed_by_agent(fake_zhmcclient._NIC(
            {'description': ''})))

    def test_get_all_devices(self):
        hmc = {"cpcs": [{"object-id": "cpcpid", "vswitches": [
            {"backing-adapter-uri": "/api/adapters/uuid-1",
             "object-id": "vswitch-uuid-1",
             "port": 0,
             "nics": [{"description": "foomac=00:00:00:00:00:11bar"},
                      {"description": "foomac=00:00:00:00:00:33bar"}]},
            {"backing-adapter-uri": "/api/adapters/uuid-2",
             "object-id": "vswitch-uuid-2",
             "port": 1,
             "nics": [{"description": "foomac=00:00:00:00:00:22bar"}]},
            {"backing-adapter-uri": "/api/adapters/uuid-3",
             "object-id": "vswitch-uuid-3",
             "port": 0},
            {"backing-adapter-uri": "/api/adapters/not-configured",
             "object-id": "not-configured",
             "port": 1,
             "nics": [{"description": "not-configured"}]},
        ]}]}

        cpc = self.mgr.cpc = fake_zhmcclient.get_cpc(hmc)

        self.mgr.vswitches = [cpc.vswitches._get('vswitch-uuid-1'),
                              cpc.vswitches._get('vswitch-uuid-2'),
                              cpc.vswitches._get('vswitch-uuid-3')]
        with mock.patch.object(self.mgr, '_managed_by_agent',
                               return_value=True) as is_uuid:
            devices = self.mgr.get_all_devices()
            self.assertEqual(3, is_uuid.call_count)
        expected = ['00:00:00:00:00:11', '00:00:00:00:00:22',
                    '00:00:00:00:00:33']
        self.assertItemsEqual(expected, devices)

    def test_get_all_devices_mac_not_present(self):
        hmc = {"cpcs": [{"object-id": "cpcpid", "vswitches": [
            {"backing-adapter-uri": "/api/adapters/uuid-1",
             "object-id": "vswitch-uuid-1",
             "port": 0,
             "nics": [{"description": "OpenStack foo"}]},
        ]}]}

        cpc = self.mgr.cpc = fake_zhmcclient.get_cpc(hmc)

        self.mgr.vswitches = [cpc.vswitches._get('vswitch-uuid-1')]
        devices = self.mgr.get_all_devices()
        expected = []
        self.assertItemsEqual(expected, devices)

    def test_get_all_devices_deleted_concurrently(self):
        hmc = {"cpcs": [{"object-id": "cpcpid", "vswitches": [
            {"backing-adapter-uri": "/api/adapters/uuid-1",
             "object-id": "vswitch-uuid-1",
             "port": 0,
             "nics": [{"name": "port-id-1"}]},
        ]}]}
        cpc = self.mgr.cpc = fake_zhmcclient.get_cpc(hmc)
        self.mgr.vswitches = [cpc.vswitches._get('vswitch-uuid-1')]
        with mock.patch.object(fake_zhmcclient._NIC, 'get_property',
                               side_effect=HTTPError(mock.Mock())):
            devices = self.mgr.get_all_devices()
            self.assertEqual(0, len(devices))

    def _test_get_all_devices_vswitch_error(self, error):
        hmc = {"cpcs": [{"object-id": "cpcpid"}]}

        self.mgr.cpc = fake_zhmcclient.get_cpc(hmc)
        vswitch = mock.Mock()
        self.mgr.vswitches = [vswitch]
        with mock.patch.object(vswitch, 'get_connected_nics',
                               side_effect=error):
            self.mgr.get_all_devices()

    @mock.patch.object(sys, 'exit')
    def test_get_all_devices_vswitch_http_error_ignore(self, m_exit):
        self._test_get_all_devices_vswitch_error(HTTPError({}))
        self.assertFalse(m_exit.called)

    @mock.patch.object(sys, 'exit')
    def test_get_all_devices_vswitch_http_404(self, m_exit):
        http_error = HTTPError({'http-status': 404})
        self._test_get_all_devices_vswitch_error(http_error)
        m_exit.assert_called_once_with(1)

    def test_get_all_devices_connection_error(self):
        vswitch_bad = mock.Mock()
        vswitch_bad.get_connected_nics.side_effect = ConnectionError("foo")
        self.mgr.vswitches = [vswitch_bad]

        devices = self.mgr.get_all_devices()
        self.assertEqual(set(), devices)

    def test_get_agent_configurations(self):
        self.mgr.physnet_map = 'foo'
        expected = {'adapter_mappings': 'foo'}
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

    def test__extract_mac(self):
        desc = "Openstack:mac=00:11:22:33:44:55,host_id=foo"
        nic = fake_zhmcclient._NIC({'description': desc})
        self.assertEqual("00:11:22:33:44:55", self.mgr._extract_mac(nic))


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

    def test__get_cpc_found(self):
        hmc = {"cpcs": [{"object-id": "oid1"}]}
        client = fake_zhmcclient.get_client(hmc)
        cpc = dpm_agt._get_cpc(client, "oid1")
        self.assertEqual("oid1", cpc.get_property("object-id"))

    def test__get_cpc_not_dpm(self):
        hmc = {"cpcs": [{"object-id": "oid1", "dpm_enabled": False}]}
        client = fake_zhmcclient.get_client(hmc)

        with mock.patch.object(sys, 'exit') as m_sys:
            dpm_agt._get_cpc(client, 'oid1')
            m_sys.assert_called_with(1)

    def test__get_cpc_not_found(self):
        hmc = {"cpcs": [{"object-id": "oid1"}]}
        client = fake_zhmcclient.get_client(hmc)
        with mock.patch.object(sys, 'exit') as m_sys:
            dpm_agt._get_cpc(client, 'not-found')
            m_sys.assert_called_with(1)

    @mock.patch.object(dpm_agt.common_config, 'init')
    @mock.patch.object(dpm_agt, '_get_cpc')
    @mock.patch.object(dpm_agt.PhysicalNetworkMapping, 'create_mapping')
    @mock.patch.object(dpm_agt.service, 'launch')
    def test_main(self, mock_launch, mock_cm, mock_get_cpcp, mock_init):
        # This test also discovers when config options have changed e.g. in
        # os-dpm
        dpm_agt.main()
        mock_launch.assert_called_once()
