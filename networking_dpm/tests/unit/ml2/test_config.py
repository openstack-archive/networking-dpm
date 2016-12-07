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

from oslo_config import cfg
from oslo_config.fixture import Config

from networking_dpm.ml2 import config  # noqa

from neutron.tests import base


class TestDPMConfig(base.BaseTestCase):

    def _test_parse_interface_mappings_good(self, mappings, expected):
        Config().load_raw_values(group='dpm',
                                 physical_adapter_mappings=mappings)
        self.assertEqual(expected, cfg.CONF.dpm.physical_adapter_mappings)

    def test_parse_interface_mappings_good(self):
        mappings = 'physnet1:{uuid-1:0},physnet2:{uuid-2:1,uuid-3:1}'
        expected = {'physnet1': {'uuid-1': 0},
                    'physnet2': {'uuid-2': 1, 'uuid-3': 1}}
        self._test_parse_interface_mappings_good(mappings, expected)

    def test_parse_interface_mappings_good_no_port(self):
        mappings = 'physnet1:{uuid-1:}'
        expected = {'physnet1': {'uuid-1': None}}
        self._test_parse_interface_mappings_good(mappings, expected)

    def _get_physical_adapter_mappings(self):
        return cfg.CONF.dpm.physical_adapter_mappings

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
                                     physical_adapter_mappings=mapping)
            # The callable argument of assertRaises must be a callable.
            # cfg.CONF is not a callable. Therefore the wrapper func exists
            self.assertRaises(cfg.ConfigFileValueError,
                              self._get_physical_adapter_mappings)
