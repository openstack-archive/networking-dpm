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

from networking_dpm.ml2 import config

from neutron.tests import base


class TestConfig(base.BaseTestCase):
    def test_config(self):
        conf = Config()
        conf.load_raw_values(group="dpm", hmc='host')
        conf.load_raw_values(group="dpm", hmc_username='username')
        conf.load_raw_values(group="dpm", hmc_password='password')
        conf.load_raw_values(group="dpm", cpc_uuid='uuid')
        conf.load_raw_values(group="dpm", cpc_name='name')
        conf.load_raw_values(group="dpm", physical_adapter_mappings='mapping')
        self.assertEqual('host', cfg.CONF.dpm.hmc)
        self.assertEqual('username', cfg.CONF.dpm.hmc_username)
        self.assertEqual('password', cfg.CONF.dpm.hmc_password)
        self.assertEqual('uuid', cfg.CONF.dpm.cpc_uuid)
        self.assertEqual('name', cfg.CONF.dpm.cpc_name)
        self.assertEqual(['mapping'], cfg.CONF.dpm.physical_adapter_mappings)

    def test_list_opts(self):
        expected = ["hmc", "hmc_username", "hmc_password", "cpc_uuid",
                    "cpc_name", "physical_adapter_mappings"]
        # Result is a list of tuples (one tuple per config group)
        result = config.list_opts()
        self.assertEqual(1, len(result))
        config_tuple = result[0]
        # Tuple consists of the groups name and a list of config_option objects
        self.assertEqual("dpm", config_tuple[0])
        config_opts = config_tuple[1]
        self.assertItemsEqual(expected, [opt.name for opt in config_opts])
