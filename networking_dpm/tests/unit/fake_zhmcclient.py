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

import json
from zhmcclient import NotFound
from zhmcclient import NoUniqueMatch

"""Fake zhmcclient for testing

The fake zhmcclient provides an easy way of testing code that includes READ
calls to the real zhmcclient [1].

Usage:
Just override the real zhmcclient with this mock client in the test
case. As input parameter the fake zhmcclient takes a json dict that represents
the HMC. For an example, see the corresponding test case.

[1] https://github.com/zhmcclient/python-zhmcclient
"""


class _BaseObject(object):
    def __init__(self, object_json):
        self.properties = object_json

    def get_property(self, name):
        return self.properties.get(name, None)


class _BaseManager(object):
    def __init__(self, type, json_object_list):
        self._objects = []
        for object in json_object_list:
            self._objects.append(type(object))

    def list(self):
        return self._objects

    def find(self, **kwargs):
        matches = self.findall(**kwargs)
        num_matches = len(matches)
        if num_matches == 0:
            raise NotFound
        elif num_matches > 1:
            raise NoUniqueMatch
        else:
            return matches[0]

    def findall(self, **kwargs):
        filter_criteria = kwargs.items()
        found = []
        for obj in self._objects:
            try:
                if all(obj.get_property(propname) == value
                       for (propname, value) in filter_criteria):
                    found.append(obj)
            except AttributeError:
                continue
        return found


class _NIC(_BaseObject):
    def __init__(self, nic_json):
        super(_NIC, self).__init__(nic_json)


class _VSwitch(_BaseObject):
    def __init__(self, vswitch_json):
        self.nics = [_NIC(nic) for nic in vswitch_json.pop('nics', [])]
        super(_VSwitch, self).__init__(vswitch_json)

    def get_connected_nics(self):
        return self.nics


class _VSwitchManager(_BaseManager):
    def __init__(self, vswitch_list):
        super(_VSwitchManager, self).__init__(_VSwitch, vswitch_list)


class _CPC(_BaseObject):

    def __init__(self, cpc_json):
        self.vswitches = _VSwitchManager(cpc_json.pop('vswitches', {}))
        self.dpm_enabled = cpc_json.pop('dpm_enabled', True)
        super(_CPC, self).__init__(cpc_json)


class _CPCManager(_BaseManager):

    def __init__(self, cpc_list):
        super(_CPCManager, self).__init__(_CPC, cpc_list)


class _Client(object):
    def __init__(self, hmc_json):
        self.cpcs = _CPCManager(hmc_json['cpcs'])


def get_client(hmc_json):
    """Get an instance of a faked zhmcclient

    :param hmc_json: A json dict or json string representing the hmc
    :return: faked zhmcclient client instance
    """
    # Test if input is a valid json
    if type(hmc_json) == dict:
        json.dumps(hmc_json)
    elif type(hmc_json) == str:
        hmc_json = json.loads(hmc_json)

    client = _Client(hmc_json)
    return client


def get_cpc(test_json):
    """Get an instance of a faked zhmcclient cpc

    :param test_json: A json dict or json string representing the hmc
    :return: faked zhmcclient cpc instance
    """
    client = get_client(test_json)
    return client.cpcs.list()[0]
