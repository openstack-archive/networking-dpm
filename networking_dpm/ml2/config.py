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


mapping_example = ["physnet1:12345678-1234-1234-1234-123456789a",
                   "physnet2:12345678-1234-1234-1234-123456789b:1",
                   "physnet3:12345678-1234-1234-1234-123456789c:0"]

# TODO(andreas_s): Neutron does not make use of required=True, therefore
# the Neutron test base class tests fail when enabled
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
  `ml2.network_vlan_ranges` config option of the Neutron server, and
* must have all of their physical networks specified in the
  corresponding `*mappings` config option of the Neutron L2 agent service
  on all network nodes.
"""))


]

dpm_group = cfg.OptGroup(name="dpm", title="DPM Configuration")

cfg.CONF.register_opts(dpm_opts, dpm_group)


def list_opts():
    return [
        (dpm_group.name, dpm_opts),
    ]
