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

from neutron._i18n import _


# TODO(andreas_s): Neutron does not make use of required=True, therefore
# the Neutron test base class tests fail when enabled
mapping_example = "physnet1:adapter-uuid:0"
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
    cfg.MultiStrOpt('physical_adapter_mappings',
                    sample_default=mapping_example,
                    help=_("""
String consisting of the following 3 elements:
"<physical_network>:<adapter-uuid>[:<port-element-id>]".
The <port-element-id> is optional and defaults to 0.

This is a Multiline Option. Multiple instances can be defined

physical_adapter_mappings = physnet1:adapter-uuid1
physical_adapter_mappings = physnet2:adapter-uuid2:1
physical_adapter_mappings = physnet3:adapter-uuid3:0

This configuration tells the Neutron DPM agent which physical network is
accessible via which network adapters/ports. Only one adapter/port combination
can be defined per physical network. All physical networks
listed in ml2.network_vlan_ranges on the neutron server should have a
mapping in each Neutron DPM agents configuration."""))
]

dpm_group = cfg.OptGroup(name="dpm", title="DPM Configuration")

cfg.CONF.register_opts(dpm_opts, dpm_group)
