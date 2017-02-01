#!/usr/bin/env python
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

import ConfigParser
import re
import requests.packages.urllib3
from socket import gethostname
import time
import zhmcclient


from keystoneauth1 import identity
from keystoneauth1 import session
from neutronclient.v2_0 import client

TEST_PARTITION_NAME = 'networking-dpm-test'

# TODO(andreas_s): Implement using taskflow?

# OpenStack Authentication
os_user = 'admin'
os_password = 'openstack'
project_name = 'demo'
project_domain_id = 'default'
user_domain_id = 'default'
auth_url = 'http://localhost:5000/v3'
auth = identity.Password(auth_url=auth_url,
                         username=os_user,
                         password=os_password,
                         project_name=project_name,
                         project_domain_id=project_domain_id,
                         user_domain_id=user_domain_id)
sess = session.Session(auth=auth)
neutron = client.Client(session=sess)

# Parse neutron plugin conf
plugin_conf = ConfigParser.ConfigParser()
plugin_conf.read("/etc/neutron/plugins/ml2/ml2_conf.ini")
zhmc = plugin_conf.get('dpm', 'hmc')
userid = plugin_conf.get('dpm', 'hmc_username')
password = plugin_conf.get('dpm', 'hmc_password')
cpc_oid = plugin_conf.get('dpm', 'cpc_object_id')

adapter_mappings = plugin_conf.get('dpm', 'physical_adapter_mappings')
regex = re.search('public:(.{36}):([01]?)', adapter_mappings)
adapter_id = regex.group(1)
port_element_id = int(regex.group(2) or 0)


# Parse neutron.conf
plugin_conf = ConfigParser.ConfigParser()
plugin_conf.read("/etc/neutron/neutron.conf")

# Set host to cfg.CONF.DEFAULT.host if possible, default to hostname
host = None
try:
    host = plugin_conf.get('DEFAULT', 'host')
except ConfigParser.NoOptionError:
    host = gethostname()


# DPM Authentication
requests.packages.urllib3.disable_warnings()
session = zhmcclient.Session(zhmc, userid, password)
client = zhmcclient.Client(session)


cpc = client.cpcs.find(**{"object-id": cpc_oid})
print("Working on cpc %s" % cpc)

# Cleaning up partitions from previous test runs
for partition in cpc.partitions.findall(name=TEST_PARTITION_NAME):
    print("Cleaning up DPM partitions")
    print("  " + str(partition))
    partition.stop()
    partition.delete()

# Get virtual switch uri
vswitch = cpc.vswitches.find(**{
    'backing-adapter-uri': '/api/adapters/' + adapter_id,
    'port': port_element_id})
vswitch.pull_full_properties()
vswitch_id = vswitch.get_property('object-id')
vswitch_uri = vswitch.get_property('object-uri')

# Create OpenStack Port
networks = neutron.list_networks(name='private')
net = networks['networks'][0]
net_id = net['id']
prov_net_type = net['provider:network_type']
vlan_id = net['provider:segmentation_id']

body = {"port": {"network_id": net_id,
                 "binding:host_id": "vagrant-ubuntu-trusty-64"}}
port = neutron.create_port(body=body)
port_id = port['port']['id']
mac = port['port']['mac_address']
print("Created Neutron port with id %s" % str(port_id))

assert("DOWN" == port['port']['status'])

# Create Partition
properties = {
    'name': TEST_PARTITION_NAME,
    'description': 'Original partition description.',
    'cp-processors': 1,
    'initial-memory': 512,
    'maximum-memory': 512,
    'processor-mode': 'shared',
    'boot-device': 'test-operating-system'
}
partition = cpc.partitions.create(properties)
print("DPM partition created %s" % str(partition))

# Create the vnic and set the NICs properties like nova would do it
# nic.description starts with 'OpenStack'
# nic.description contains mac=<mac-of-neutron-port>
# nic.description contains host identifier
nic = partition.nics.create({"virtual-switch-uri": vswitch_uri,
                             "name": "OpenStack foo",
                             "description": "OpenStack mac=" + mac + " Host"
                                            + host})
print("DPM NIC created %s" % str(nic))

# sleeping to give the agent time to do the work
time.sleep(6)


def get_neutron_port(port_id):
    ports = neutron.list_ports(id=port_id)
    return ports['ports'][0]

port = get_neutron_port(port_id)

print(port)
# Do assertions
assert("ACTIVE" == get_neutron_port(port_id)['status'])
print("Neutron port status changed to 'ACTIVE'")
assert("dpm_vswitch" == port['binding:vif_type'])
print("Neutron port vif type set to 'dpm_vswitch'")
assert(vswitch_id == port['binding:vif_details']['object_id'])
print("Neutron port vif details object_id set to " + vswitch_id)
if prov_net_type == 'vlan':
    assert(vlan_id == port['binding:vif_details']['vlan'])
    print("VLAN ID set to " + str(vlan_id))
    assert('inband' == port['binding:vif_details']['vlan_mode'])
    print("vlan_mode set to 'inband'")

# Remove NIC from partition again
print("Removing DPM NIC again")
nic.delete()


# sleeping to give the agent time to do the work
time.sleep(6)

assert("DOWN" == get_neutron_port(port_id)['status'])
print("Neutron port status went to 'DOWN' again")

# Deleting Neutron port
neutron.delete_port(port_id)
print("Deleted Neutron port")

partition.delete()
print("Deleted DPM partition")
print("Success!")
