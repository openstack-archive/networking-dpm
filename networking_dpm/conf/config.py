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

from networking_dpm.conf.cfg import MultiNetworkAdapterMappingOpt

# Update help text of DPM group with networking-dpm specifics
os_dpm_conf.DPM_GROUP.help += """

DPM config options for the Neutron agent on the compute node (one agent
instance for each OpenStack hypervisor host) specify the target CPC, the HMC
managing it, and the OpenStack physical networks for the OpenStack hypervisor
host and their backing network adapters and ports in the target CPC."""

os_dpm_conf.register_opts()

mapping_example = ["physnet1:12345678-1234-1234-1234-123456789a",
                   "physnet2:12345678-1234-1234-1234-123456789b:1",
                   "physnet3:12345678-1234-1234-1234-123456789c:0"]

# TODO(andreas_s): Neutron does not make use of required=True, therefore
# the Neutron test base class tests fail when enabled
dpm_opts = [
    MultiNetworkAdapterMappingOpt(
        'physical_network_adapter_mappings',
        sample_default=mapping_example,
        help="""
The OpenStack physical networks that can be used by this OpenStack hypervisor
host, and their backing network adapters and ports in the target CPC.

This is a multi-line option. Each instance (line) of the option defines one
physical network for use by this OpenStack hypervisor host, and the network
adapter and port that is used for that physical network, using this syntax:

```
    <physical-network-name>:<adapter-object-id>[:<port-element-id>]
```

* `<physical-network-name>` is the name of the OpenStack physical network.
* `<adapter-object-id>` is the object-id of the network adapter in the target
  CPC that is used for this physical network.
* `<port-element-id>` is the element-id of the port on that network adapter.
  It is optional and defaults to 0.

The instances (lines) of this option for a particular Neutron agent

* must not specify the same physical network more than once, and
* must not specify the same adapter and port more than once, and
* must have all of their physical networks specified in the
  corresponding `*mappings` config option of the Neutron L2 agent service
  on all network nodes, and
* must have all of their physical networks specified in the
  `ml2.network_vlan_ranges` config option of the Neutron server, if vlan
  self service networks should be used.
""")


]

cfg.CONF.register_opts(dpm_opts, os_dpm_conf.DPM_GROUP)


def list_opts():
    return [
        (os_dpm_conf.DPM_GROUP, dpm_opts + os_dpm_conf.COMMON_DPM_OPTS),
    ]
