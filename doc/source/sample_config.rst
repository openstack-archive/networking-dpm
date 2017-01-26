====================================
Networking-dpm Configuration Options
====================================

Neutron DPM Mechanism driver
----------------------------

The Neutron DPM Mechanism driver itself does not require any configuration
options.

But certain Neutron ML2 configuration options in the ML2 configuration file
(typically *ml2_conf.ini*) are required in order to use it.

Enable the dpm mechanism driver
+++++++++++++++++++++++++++++++

The *dpm* mechanism driver must be enabled using Neutron ML2
*mechanism_drivers* config option. Typically the DPM mechanism driver must be
configured amongst other mechanisms (like *ovs*) that are used on the network
node or compute nodes managing other hypervisor types (like KVM). The
following example enables the *ovs* and the *dpm* mechanism driver in Neutrons
ml2 config file *ml2_conf.ini*::

  [DEFAULT]
  mechanism_drivers = ovs,dpm

For more details see the Neutron ML2 section in the OpenStack
`Configuration Reference <http://docs.openstack.org/>`_.

Configure ML2 for self service VLAN networks
++++++++++++++++++++++++++++++++++++++++++++

For taking use of self service VLAN networks, the physical networks and their
corresponding vlan ranges must be defined in the Neutron servers ML2
configuration file::

  [ml2_type_vlan]
  network_vlan_ranges = <physical_network>:<vlan_min>:<vlan_max>,<physical_network2>:<vlan_min>:<vlan_max>

For more details see the Neutron ML2 section in the OpenStack
`Configuration Reference <http://docs.openstack.org/>`_.

.. note::
  Each physical network that should be used for self service VLAN networks
  must also be defined in the neutron-dpm-agents *physical_adapter_mappings*
  configuration option. This is also true for other Neutron l2 agents. They
  all have a similar *mappings* option that must be configured accordingly.

.. note::
  This config option is not required if only VLAN provider networks will be
  used.


Neutron DPM Agent
-----------------

The following is a sample neutron-dpm-agent configuration for adaptation and
use. It is auto-generated from the networking-dpm project when this
documentation is built, so if you are having issues with an option, please
compare your version of networking-dpm with the version of this documentation.

The sample configuration can also be viewed in
`file form <_static/neutron_dpm_agent.conf.sample>`_.

.. literalinclude:: _static/neutron_dpm_agent.conf.sample
