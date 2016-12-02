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

import json
import os
import sys

import mock
from neutron_lib.utils import helpers
from oslo_config.fixture import Config
from oslo_config import cfg
from oslo_service import service
import zhmcclient

from networking_dpm.ml2 import dpm_neutron_agent as dpm_agt
from networking_dpm.tests.unit import fake_zhmcclient

from neutron.agent.linux import ip_lib
from neutron.common import config as common_config
from neutron.common import topics
from neutron.plugins.ml2.drivers.agent import _agent_manager_base as amb
from neutron.plugins.ml2.drivers.macvtap.agent import macvtap_neutron_agent
from neutron.tests import base


INTERFACE_MAPPINGS = {'physnet1': 'uuid-1:0',
                      'physnet2': 'uuid-2:1'}
NETWORK_ID = 'net-id123'
NETWORK_SEGMENT_VLAN = amb.NetworkSegment('vlan', 'physnet1', 1)
NETWORK_SEGMENT_FLAT = amb.NetworkSegment('flat', 'physnet1', None)


class TestDPMRPCCallbacks(base.BaseTestCase):
    def setUp(self):
        super(TestDPMRPCCallbacks, self).setUp()

        agent = mock.Mock()
        agent.mgr = mock.Mock()
        agent.mgr.interface_mappings = INTERFACE_MAPPINGS
        self.rpc = dpm_agt.DPMRPCCallBack(mock.Mock(), agent, mock.Mock())

    def test_port_update(self):
        port = {'id': 'port-id123', 'mac_address': 'mac1'}
        self.rpc.port_update(context=None, port=port)
        self.assertEqual(set(['mac1']), self.rpc.updated_devices)


class TestDPMManager(base.BaseTestCase):
    def setUp(self):
        super(TestDPMManager, self).setUp()
        self.mgr = dpm_agt.DPMManager(INTERFACE_MAPPINGS)

    def test_ensure_port_admin_state_up(self):
        pass

    def test_get_all_devices(self):
        pass

    def test_get_agent_configurations(self):
        expected = {'interface_mappings': INTERFACE_MAPPINGS}
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

    def _test_parse_interface_mappings_good(self, mappings, expected):
        Config().load_raw_values(group='dpm',
                                 adapter_interface_mappings=mappings)
        self.assertEqual(expected, dpm_agt.parse_adapter_mappings())

    def test_parse_interface_mappings_good(self):
        mappings = 'physnet1:{uuid-1:0},physnet2:{uuid-2:1,uuid-3:1}'
        expected = {'physnet1': {'uuid-1': 0},
                     'physnet2': {'uuid-2': 1, 'uuid-3': 1}}
        self._test_parse_interface_mappings_good(mappings, expected)

    def test_parse_interface_mappings_good_no_port(self):
        mappings = 'physnet1:{uuid-1:}'
        expected = {'physnet1': {'uuid-1': None}}
        self._test_parse_interface_mappings_good(mappings, expected)

    def test_parse_interface_mappings_bad(self):
        bad_mappings = [
            # Missing }
            'physnet1:{uuid-1:0,physnet2:{uuid-2:1,uuid-3:1}',
            # Port-element-id not an Int
            'physnet1:{uuid-1:foo}',
            # Duplicated physnet definition
            'physnet1:{uuid-1:0},physnet1:{uuid-2:1}',
            # Duplicated adapter-id definition in a physnet
            'physnet1:{uuid-1:0, uuid-1:1}',
            # Missing adapter:port information
            'physnet1',
            # Missing port definition
            'physnet1:{uuid-1}',
        ]

        for mapping in bad_mappings:
            Config().load_raw_values(group='dpm',
                                     adapter_interface_mappings=mapping)
            self.assertRaises(ValueError, dpm_agt.parse_adapter_mappings)

    def test_validate_firewall_driver(self):
        valid_drivers = ['neutron.agent.firewall.NoopFirewallDriver',
                         'noop']
        for driver in valid_drivers:
            cfg.CONF.set_override('firewall_driver', driver, 'SECURITYGROUP')
            dpm_agt.validate_firewall_driver()

    def test_validate_firewall_driver_invalid(self):
        cfg.CONF.set_override('firewall_driver', 'foo', 'SECURITYGROUP')
        with mock.patch.object(sys, 'exit')as mock_exit:
            dpm_agt.validate_firewall_driver()
            mock_exit.assert_called_with(1)

    def _get_client(self, mocked=True):
        if mocked:
            return mock.Mock()
        else:
            with open("credentials.json") as creds_file:
                creds = json.load(creds_file)
            session = zhmcclient.Session(creds['ip'],
                                         creds['user'],
                                         creds['password'])
            client = zhmcclient.Client(session)
            return client

    def _get_fake_cpc(self, dpm_enabled=True, mocked=True):
        if mocked:
            fake_cpc = mock.Mock()
            fake_cpc.dpm_enabled = dpm_enabled
            return fake_cpc
        else:
            client = self._get_client(mocked=False)
            cpc = client.cpcs.find(name='EURANSE2')
            return cpc

    def test_validate_interface_mappings(self):
        mapping = {'physnet1': {'uuid-1': None},
                   'physnet2': {'uuid-2': 1, 'uuid-3': None}}
        expected = {'physnet1': ['vswitch-uuid-1'],
                    'physnet2': ['vswitch-uuid-2', 'vswitch-uuid-3']}
        #mapping = {'foo': {'8de39a6c-b7d3-11e6-8593-020000000322': None}}
        fake_cpc = fake_zhmcclient.CPC()
        actual = dpm_agt.get_physnet_adapter_map(mapping, fake_cpc)

        # Cannot use assertDictEqual as order of list is not guaranteed
        self.assertItemsEqual(expected['physnet1'], actual['physnet1'])
        self.assertItemsEqual(expected['physnet2'], actual['physnet2'])

    def test__get_cpc_found(self):
        fake_client = self._get_client()
        fake_cpc = self._get_fake_cpc()

        with mock.patch.object(fake_client.cpcs, "find",
                               return_value=fake_cpc):
            cpc = dpm_agt._get_cpc(fake_client, 'EURANSE2')
            self.assertEqual(fake_cpc, cpc)

    def test__get_cpc_not_dpm(self):
        fake_client = mock.Mock()
        fake_cpc = self._get_fake_cpc(False)

        with mock.patch.object(fake_client.cpcs, "find",
                               return_value=fake_cpc),\
                mock.patch.object(sys, 'exit') as m_sys:
            dpm_agt._get_cpc(fake_client, 'EURANSE2')
            m_sys.assert_called_with(1)

    def test__get_cpc_not_found(self):
        fake_client = mock.Mock()
        with mock.patch.object(fake_client.cpcs, "find",
                               side_effect=zhmcclient.NotFound()), \
             mock.patch.object(sys, 'exit') as m_sys:
            dpm_agt._get_cpc(fake_client, 'EURANSE2')
            m_sys.assert_called_with(1)



                    # def test_main(self):
    #     cfg.CONF.set_override('quitting_rpc_timeout', 1, 'AGENT')
    #     cfg.CONF.set_override('polling_interval', 2, 'AGENT')
    #
    #     mock_manager_return = mock.Mock(spec=amb.CommonAgentManagerBase)
    #     mock_launch_return = mock.Mock()
    #
    #     with mock.patch.object(common_config, 'init'),\
    #         mock.patch.object(common_config, 'setup_logging'),\
    #         mock.patch.object(service, 'launch',
    #                           return_value=mock_launch_return) as mock_launch,\
    #         mock.patch.object(dpm_agt,
    #                           'parse_interface_mappings',
    #                           return_value=INTERFACE_MAPPINGS) as mock_pim,\
    #         mock.patch.object(dpm_agt,
    #                           'validate_firewall_driver') as mock_vfd,\
    #         mock.patch('neutron.plugins.ml2.drivers.agent._common_agent.'
    #                    'CommonAgentLoop') as mock_loop,\
    #         mock.patch('neworking_dpm.ml2.dpm_neutronagent.DPMManager',
    #                    return_value=mock_manager_return) as mock_manager:
    #         macvtap_neutron_agent.main()
    #         self.assertTrue(mock_vfd.called)
    #         self.assertTrue(mock_pim.called)
    #         mock_manager.assert_called_with(INTERFACE_MAPPINGS)
    #         mock_loop.assert_called_with(mock_manager_return, 2, 1,
    #                                      'DPM agent',
    #                                      'neutron-dpm-agent')
    #         self.assertTrue(mock_launch.called)
    #         self.assertTrue(mock_launch_return.wait.called)
