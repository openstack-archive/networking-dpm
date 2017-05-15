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

from os_dpm.config import config as os_dpm_conf
from oslo_config import cfg

from networking_dpm.conf import config
from networking_dpm.tests import base


class TestConfig(base.BaseTestCase):
    def test_config(self):
        mappings = ["physnet:aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa:0"]
        mappings_parsed =\
            [('physnet', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '0')]

        cfg.CONF.set_override('hmc', 'hmc-ip', 'dpm')
        cfg.CONF.set_override('hmc_username', 'username', 'dpm')
        cfg.CONF.set_override('hmc_password', 'password', 'dpm')
        cfg.CONF.set_override('cpc_object_id', 'oid', 'dpm')
        cfg.CONF.set_override('physical_network_adapter_mappings', mappings,
                              'dpm')

        self.assertEqual('hmc-ip', cfg.CONF.dpm.hmc)
        self.assertEqual('username', cfg.CONF.dpm.hmc_username)
        self.assertEqual('password', cfg.CONF.dpm.hmc_password)
        self.assertEqual('oid', cfg.CONF.dpm.cpc_object_id)
        self.assertEqual(mappings_parsed,
                         cfg.CONF.dpm.physical_network_adapter_mappings)

    def test_list_opts(self):
        expected = os_dpm_conf.COMMON_DPM_OPTS + config.dpm_opts
        # Result is a list of tuples (one tuple per config group)
        result = config.list_opts()

        # DPM Config options
        dpm_tuple = result[0]
        # Tuple consists of the groups name and a list of config_option objects
        self.assertEqual(os_dpm_conf.DPM_GROUP, dpm_tuple[0])
        config_opts = dpm_tuple[1]
        self.assertItemsEqual(expected, config_opts)
