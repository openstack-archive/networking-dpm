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

For more details see the Neutron ML2 section in the OpenStack
`Configuration Reference <http://docs.openstack.org/>`_.

Configure ML2 for self service VLAN networks
++++++++++++++++++++++++++++++++++++++++++++

For taking use of self service VLAN networks, the physical networks and their
corresponding VLAN ranges must be defined in the Neutron servers ML2
configuration file::

  [ml2_type_vlan]
  network_vlan_ranges = <physical_network>:<vlan_min>:<vlan_max>,<physical_network2>:<vlan_min>:<vlan_max>

For more details see the Neutron ML2 section in the OpenStack
`Configuration Reference <http://docs.openstack.org/>`_.

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

The following is a sample Neutron DPM Agent configuration for adaptation and
use.

.. note::
  This configuration is auto-generated from the networking-dpm project when
  this documentation is built. That means,
  * it does not represent the config options of a stable release
  * it does not represent the latest config options on master
  -> it only shows the config options from the last documentation build.

  So if you are having issues with an option, please compare your version of
  networking-dpm with the version of this documentation.

The sample configuration can also be viewed in
`file form <_static/neutron_dpm_agent.conf.sample>`_.

.. literalinclude:: _static/neutron_dpm_agent.conf.sample
