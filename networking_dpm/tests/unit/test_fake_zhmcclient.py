# Copyright 2016 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from neutron.tests import base

from networking_dpm.tests.unit import fake_zhmcclient


class TestFakeZHMC(base.BaseTestCase):

    def test_fakehmc_full(self):

        nics = [{'name': 'nic-name-1', 'object-id': 'nic-id-1'},
                {'name': 'nic-name-2', 'object-id': 'nic-id-2'}]
        vswitches = [{'backing-adapter-uri': '/api/adapters/uuid-0',
                      'object-id': 'vswitch-uuid-0', 'port': 0},
                     {'backing-adapter-uri': '/api/adapters/uuid-1',
                      'object-id': 'vswitch-uuid-1',
                      'port': 1,
                      'nics': nics}
                     ]
        adapter_ports = [{'element-id': '0'}, {'element-id': '1'}]
        adapters = [{'object-id': 'uuid-0', 'ports': adapter_ports},
                    {'object-id': 'uuid-1'}]

        hmc_json = {'cpcs': [
            {'object-id': 'oid0', 'name': 'CPCname0',
             'vswitches': vswitches, 'adapters': adapters},
            {'object-id': 'oid1', 'name': 'CPCname1', 'dpm_enabled': False,
             'vswitches': {}}
        ]}

        client = fake_zhmcclient.get_client(hmc_json)
        cpc_list = client.cpcs.list()
        self.assertTrue(len(cpc_list) == 2)

        # CPC 0
        cpc0 = client.cpcs.find(**{'object-id': 'oid0'})
        self.assertEqual('oid0', cpc0.get_property('object-id'))
        self.assertEqual('CPCname0', cpc0.get_property('name'))
        self.assertIn(cpc0, cpc_list)
        self.assertTrue(cpc0.dpm_enabled)

        vswitch_list = cpc0.vswitches.list()
        self.assertEqual(2, len(vswitch_list))

        vswitch0 = cpc0.vswitches.find(**{'object-id': 'vswitch-uuid-0'})
        self.assertEqual('/api/adapters/uuid-0',
                         vswitch0.get_property('backing-adapter-uri'))
        self.assertEqual('vswitch-uuid-0', vswitch0.get_property('object-id'))
        self.assertEqual(0, vswitch0.get_property('port'))
        self.assertIn(vswitch0, vswitch_list)

        vswitch1 = cpc0.vswitches.find(**{'object-id': 'vswitch-uuid-1'})
        self.assertEqual('/api/adapters/uuid-1',
                         vswitch1.get_property('backing-adapter-uri'))
        self.assertEqual('vswitch-uuid-1', vswitch1.get_property('object-id'))
        self.assertEqual(1, vswitch1.get_property('port'))
        self.assertIn(vswitch1, vswitch_list)

        adapter_list = cpc0.adapters.list()
        self.assertEqual(2, len(adapter_list))
        adapter0 = cpc0.adapters.find(**{'object-id': 'uuid-0'})
        self.assertEqual('uuid-0', adapter0.get_property('object-id'))
        port_list = adapter0.ports.list()
        self.assertEqual(2, len(port_list))
        port0 = adapter0.ports.find(**{'element-id': '0'})
        self.assertEqual('0', port0.get_property('element-id'))
        port1 = adapter0.ports.find(**{'element-id': '1'})
        self.assertEqual('1', port1.get_property('element-id'))

        adapter1 = cpc0.adapters.find(**{'object-id': 'uuid-1'})
        self.assertEqual('uuid-1', adapter1.get_property('object-id'))

        nics = vswitch1.get_connected_nics()
        self.assertEqual(2, len(nics))
        nic1 = nics[0]
        self.assertEqual(('nic-name-1', 'nic-id-1'),
                         (nic1.get_property('name'),
                          nic1.get_property('object-id')))
        nic2 = nics[1]
        self.assertEqual(('nic-name-2', 'nic-id-2'),
                         (nic2.get_property('name'),
                          nic2.get_property('object-id')))

        # CPC 1
        cpc1 = client.cpcs.find(**{'object-id': 'oid1'})
        self.assertEqual('oid1', cpc1.get_property('object-id'))
        self.assertEqual('CPCname1', cpc1.get_property('name'))
        self.assertIn(cpc1, cpc_list)
        self.assertFalse(cpc1.dpm_enabled)

        self.assertEqual(0, len(cpc1.vswitches.list()))

    def test_port_element_id(self):
        """zhmcclient treats element-id as string

        https://github.com/zhmcclient/python-zhmcclient/issues/125
        """
        ports_json = [{'element-id': 0}, {'element-id': '1'}]
        adapter_json = {'object-id': 'oid1', 'ports': ports_json}

        adapt = fake_zhmcclient._Adapter(adapter_json)
        self.assertRaises(fake_zhmcclient.NotFound,
                          adapt.ports.find, **{'element-id': 0})
        self.assertRaises(fake_zhmcclient.NotFound,
                          adapt.ports.find, **{'element-id': 1})

        self.assertIsNotNone(adapt.ports.find(**{'element-id': '0'}))
        self.assertIsNotNone(adapt.ports.find(**{'element-id': '1'}))

    def test_fakehmc_consistency_fail(self):
        vswitches = [{'backing-adapter-uri': '/api/adapters/uuid-0',
                      'object-id': 'vswitch-uuid-0'}]
        adapters = [{'object-id': 'another-uuid'}]
        hmc_json = {'cpcs': [
            {'object-id': 'oid0',
             'vswitches': vswitches, 'adapters': adapters}
        ]}
        self.assertRaises(fake_zhmcclient.FakeZHMCClientError,
                          fake_zhmcclient.get_cpc, hmc_json)

    def test_fakehmc_consistency_given(self):
        vswitches = [{'backing-adapter-uri': '/api/adapters/uuid-0',
                      'object-id': 'vswitch-uuid-0'}]
        adapters = [{'object-id': 'uuid-0'}]
        hmc_json = {'cpcs': [
            {'object-id': 'oid0',
             'vswitches': vswitches, 'adapters': adapters}
        ]}
        # No Exception thrown
        fake_zhmcclient.get_cpc(hmc_json)

    def test_fakehmc_consistency_no_adapters_given(self):
        # If no adapters are specified, don't check for consistency
        vswitches = [{'backing-adapter-uri': '/api/adapters/uuid-0',
                      'object-id': 'vswitch-uuid-0'}]
        hmc_json = {'cpcs': [
            {'object-id': 'oid0', 'vswitches': vswitches}
        ]}
        # No Exception thrown
        fake_zhmcclient.get_cpc(hmc_json)

    def test_fakehmc_minimal(self):
        hmc = {"cpcs": [{"name": "foo"}]}
        # Verify that no exception is thrown
        fake_zhmcclient.get_client(hmc)

    def test_fakehmc_str(self):
        test_json = '{"cpcs": [{"prop1": "value1", "vswitches": []}]}'
        # Verify that no exception is thrown
        fake_zhmcclient.get_client(test_json)

    def test_fakehmc_invalid_json(self):
        test_json = "{'blub': {"
        self.assertRaises(ValueError, fake_zhmcclient.get_client, test_json)

    def test_fakehmc_get_cpc(self):
        hmc = {"cpcs": [{"name": "foo"}]}
        cpc = fake_zhmcclient.get_cpc(hmc)
        self.assertEqual("foo", cpc.get_property('name'))
