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
from oslo_config import types

from neutron._i18n import _

DEFAULT_ADAPTER_MAPPINGS = {}


class DictOfIntDictsOpt(cfg.Opt):

    """Option with Dict(Dict(Integer)) type

    Option with ``type`` :class:`oslo_config.types.Dict`

    :param name: the option's name
    :param \*\*kwargs: arbitrary keyword arguments passed to :class:`Opt`
    """

    def __init__(self, name, **kwargs):
        # A config value of 'key:' results in the value 'None'.
        # This can be treated in the agent code to default to '0'.
        # A config value of 'key' results in an error
        # TODO(andreas_s): Extend the Dict type in oslo.config to allow default
        # values other than None.
        # TODO(andreas_s): Enable oslo.config to also accept the format
        # 'key' if a default value was set
        inner_dict_type = types.Dict(value_type=types.Dict(types.Integer(),
                                     bounds=True))
        super(DictOfIntDictsOpt, self).__init__(name, type=inner_dict_type,
                                                **kwargs)

# TODO(andreas_s): What if both ports of an adapter should be used for the
# same physical network? Using the same uuid as key obviously results in a key
# error. Solution: Make the value a String and allow something like uuid1:'0,1'
# TODO(andreas_s): Neutron does not make use of required=True, therefore
# the Neutron test base class tests fail when enabled

mapping_example = "physnet1:{uuid1:},physnet2:{uuid2:1},physnet3:{uuid3:0}"
dpm_opts = [
    cfg.StrOpt('hmc',
               help=_("Hostname or IP address for connection to HMC via "
                      "zhmcclient")),
    cfg.StrOpt('hmc_username',
               help=_("User name for connection to HMC Host.")),
    cfg.StrOpt('hmc_password',
               help=_("Password for connection to HMC Host.")),
    cfg.StrOpt('cpc_name',
               help=_("CPC name on which the host is carved out from")),
    DictOfIntDictsOpt('physical_adapter_mappings',
                      default=DEFAULT_ADAPTER_MAPPINGS,
                      sample_default=mapping_example,
                      help=_("""
List of "<physical_network>:{<adapter-uuid>:<port-element-id>}" combinations.

<port-element-id> defaults to 0 if none is given This configuration tells the
Neutron DPM agent which physical network is accessible via which network
adapters/ports. Only a single adapter/port combination is supported by one
physical network. All physical networks listed in ml2.network_vlan_ranges on
the neutron server should have a mapping in each Neutron DPM agents
configuration."""))
]

dpm_group = cfg.OptGroup(name="dpm", title="DPM Configuration")

cfg.CONF.register_opts(dpm_opts, dpm_group)


def list_opts():
    return [
        (dpm_group.name, dpm_opts),
    ]
