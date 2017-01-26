====================================
Networking-dpm Configuration Options
====================================

Neutron DPM Mechanism driver
----------------------------

The Neutron DPM Mechanism driver itself does not require any DPM specific
configuration options.

But certain well known Neutron ML2 (Modular Layer 2) configuration options in
the ML2 configuration file (typically *ml2_conf.ini*) are required in order
to use it.

Enable the dpm mechanism driver
+++++++++++++++++++++++++++++++

The *dpm* mechanism driver must be enabled using Neutron ML2
*mechanism_drivers* config option. Typically the DPM mechanism driver must be
configured amongst other mechanisms (like *ovs*) that are used on the network
node or compute nodes managing other hypervisor types (like KVM). The
following example enables the *ovs* and the *dpm* mechanism driver in Neutrons
ML2 config file *ml2_conf.ini*::

  [DEFAULT]
  mechanism_drivers = ovs,dpm

More details can be found in the OpenStack Configuration Reference on
`docs.openstack.org <http://docs.openstack.org/>`_.

Configure ML2 for self service VLAN networks
++++++++++++++++++++++++++++++++++++++++++++

For taking use of self service VLAN networks, the physical networks and their
corresponding VLAN ranges must be defined in the Neutron servers ML2
configuration file::

  [ml2_type_vlan]
  network_vlan_ranges = <physical_network>:<vlan_min>:<vlan_max>,<physical_network2>:<vlan_min>:<vlan_max>

More details can be found in the OpenStack Configuration Reference on
`docs.openstack.org <http://docs.openstack.org/>`_.


.. note::
  Each physical network that should be used for self service VLAN networks
  must also be defined in the Neutron DPM agent *physical_adapter_mappings*
  configuration option. This is also true for other Neutron L2 Agents
  (for example the Neutron Open vSwitch Agent). They all have a similar
  *mappings* option that must be configured accordingly.

.. note::
  This config option is not required if only VLAN provider networks will be
  used.


Neutron DPM Agent
-----------------
The Neutron DPM agent on the compute Node requires DPM specific options. But
also some well known Neutron options can be set.

General Neutron options
+++++++++++++++++++++++

The following common Neutron options can be set in the Neutron DPM Agents
configuration file:

* [default] host

* [agent] quitting_rpc_timeout

* [agent] polling_interval

More details can be found in the OpenStack Configuration Reference on
`docs.openstack.org <http://docs.openstack.org/>`_.

DPM specific options
++++++++++++++++++++

Those are the DPM specific configuration options required by the Neutron
DPM Agent.

.. note::
  This configuration is auto-generated from the networking-dpm project when
  this documentation is built. So if you are having issues with an option,
  please compare your version of networking-dpm with the version of this
  documentation.

The sample configuration can also be viewed in
`file form <_static/neutron_dpm_agent.conf.sample>`_.

.. literalinclude:: _static/neutron_dpm_agent.conf.sample
