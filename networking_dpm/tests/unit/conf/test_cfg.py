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

import os
from oslo_config import cfg
from oslo_config.fixture import Config
import tempfile

from neutron.tests import base

from networking_dpm.conf.cfg import MultiNetworkAdapterMappingOpt
from networking_dpm.conf.types import NetworkAdapterMappingType
from networking_dpm.tests.unit.conf.test_types import VALID_DPM_OBJECT_ID
from networking_dpm.tests.unit.conf.test_types import VALID_NETWORK_MAPPING


class TestNetworkAdapterMappingType(base.BaseTestCase):

    def create_tempfiles(self, files, ext='.conf'):
        # TODO(andreas_s): Make a mixin in os-dpm and move this there
        # (also required in nova-dpm)
        tempfiles = []
        for (basename, contents) in files:
            if not os.path.isabs(basename):
                # create all the tempfiles in a tempdir
                tmpdir = tempfile.mkdtemp()
                path = os.path.join(tmpdir, basename + ext)
                # the path can start with a subdirectory so create
                # it if it doesn't exist yet
                if not os.path.exists(os.path.dirname(path)):
                    os.makedirs(os.path.dirname(path))
            else:
                path = basename + ext
            fd = os.open(path, os.O_CREAT | os.O_WRONLY)
            tempfiles.append(path)
            try:
                os.write(fd, contents.encode('utf-8'))
            finally:
                os.close(fd)
        return tempfiles

    def test_object(self):
        opt = MultiNetworkAdapterMappingOpt("mapping", help="foo-help")
        self.assertEqual("foo-help", opt.help)
        self.assertEqual("mapping", opt.name)
        self.assertEqual(NetworkAdapterMappingType, type(opt.type))

    def test_config_single(self):
        conf = self.useFixture(Config())
        conf.load_raw_values(mapping=VALID_NETWORK_MAPPING)
        opt = MultiNetworkAdapterMappingOpt("mapping")
        conf.register_opt(opt)
        self.assertEqual([("physnet", VALID_DPM_OBJECT_ID, "0")],
                         cfg.CONF.mapping)

    def test_config_multiple(self):
        other_object_id = 'aaaaaaaa-12df-311a-804c-aaaaaaaaaaaa'
        other_net = 'net2'
        other_mapping = other_net + ':' + other_object_id
        paths = self.create_tempfiles([
            ('test', '[DEFAULT]\nmapping = ' + VALID_NETWORK_MAPPING + '\n'
             'mapping = ' + other_mapping + '\n')])

        conf = self.useFixture(Config())
        conf.register_opt(MultiNetworkAdapterMappingOpt("mapping"))
        conf.conf(args=['--config-file', paths[0]])
        expected_mapping = [("physnet", VALID_DPM_OBJECT_ID, "0"),
                            (other_net, other_object_id, "0")]
        self.assertEqual(expected_mapping, cfg.CONF.mapping)
