# Copyright 2017 IBM Corp. All Rights Reserved.
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

from networking_dpm.conf.cfg import MultiNetworkAdapterMappingOpt
from networking_dpm.conf.types import NetworkAdapterMappingType
from networking_dpm.tests import base


class TestNetworkAdapterMappingType(base.BaseTestCase):

    def create_tempfiles(self, files, ext='.conf'):
        """Create temp files for testing

        :param files: A list of files of tuples in the format
           [('filename1', 'line1\nline2\n'), ('filename2', 'line1\nline2\n')]
        :param ext: The file extension to be used
        :return: List of file paths
           paths[0] = path of filename1
           paths[1] = path of filename2
        """
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

    def test_config_single_set_override(self):
        mapping = ["physnet:aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa:0"]
        opt = MultiNetworkAdapterMappingOpt("mapping")
        cfg.CONF.register_opt(opt)
        self.flags(mapping=mapping)
        self.assertEqual([("physnet", "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                           "0")], cfg.CONF.mapping)

    def test_config_multiple_set_override(self):
        mapping = ["physnet:aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa:0",
                   "net2:bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"]
        opt = MultiNetworkAdapterMappingOpt("mapping")
        cfg.CONF.register_opt(opt)
        self.flags(mapping=mapping)
        expected_mapping = [
            ("physnet", "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "0"),
            ("net2", "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "0")]
        self.assertEqual(expected_mapping, cfg.CONF.mapping)

    def test_config_multiple_with_conf_file(self):
        mapping = "physnet:aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa:0"
        other_mapping = "net2:bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        paths = self.create_tempfiles([
            ('test', '[DEFAULT]\nmapping = ' + mapping + '\n'
             'mapping = ' + other_mapping + '\n')])

        conf = self.useFixture(Config())
        conf.register_opt(MultiNetworkAdapterMappingOpt("mapping"))
        conf.conf(args=['--config-file', paths[0]])
        expected_mapping = [
            ("physnet", "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "0"),
            ("net2", "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "0")]
        self.assertEqual(expected_mapping, cfg.CONF.mapping)
