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


from oslo_config import cfg

OBJECT_ID_REGEX = "[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12}"
PORT_REGEX = "[0,1]"
MAPPING_REGEX = "^[^:]+:" + OBJECT_ID_REGEX + "(:?|(:" + PORT_REGEX + ")?)$"


class NetworkAdapterMappingType(cfg.types.String):
    """Network adapter mapping type.

    Values are returned as tuple (net, adapter-id, port).
    Port defaults to '0' if non given.
    """
    def __init__(self, type_name='multi valued'):
        super(NetworkAdapterMappingType, self).__init__(
            type_name=type_name,
            regex=MAPPING_REGEX,
            ignore_case=True
        )

    def format_defaults(self, default, sample_default=None):
        multi = cfg.types.MultiString()
        return multi.format_defaults(default, sample_default)

    def __call__(self, value):
        val = super(NetworkAdapterMappingType, self).__call__(value)
        # No extra checking for None required here.
        # The regex ensures the format of the value in the super class.
        split_result = val.split(':')
        net = split_result[0]
        adapter_id = split_result[1].lower()
        port = (split_result[2] if len(split_result) == 3 and
                split_result[2] else "0")
        return net, adapter_id, port
