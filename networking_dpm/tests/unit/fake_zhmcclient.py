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
from zhmcclient._exceptions import NotFound
from zhmcclient._exceptions import NoUniqueMatch


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
        searches = kwargs.items()
        found = []
        for obj in self._objects:
            try:
                if all(obj.get_property(propname) == value
                       for (propname, value) in searches):
                    found.append(obj)
            except AttributeError:
                continue
        return found


class _VSwitch(_BaseObject):
    def __init__(self, vswitch_json):
        super(_VSwitch, self).__init__(vswitch_json)


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


def get_client(test_json):
    # Test if input is a valid json
    if type(test_json) == dict:
        json.dumps(test_json)
    elif type(test_json) == str:
        test_json = json.loads(test_json)

    client = _Client(test_json)
    return client
