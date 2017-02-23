.. _configuration:

=============
Configuration
=============

Neutron DPM mechanism driver
============================

The Neutron DPM mechanism driver itself does not require any DPM-specific
configuration options.

But certain well known Neutron ML2 (Modular Layer 2) configuration options in
the ML2 configuration file (typically *ml2_conf.ini*) are required in order
to use it.

Enable the DPM mechanism driver
-------------------------------

The *DPM* mechanism driver must be enabled using Neutron ML2
*mechanism_drivers* config option. Typically the DPM mechanism driver must be
configured amongst other mechanisms (like *OVS*) that are used on the network
node or compute nodes managing other hypervisor types (like KVM). The
following example enables the *ovs* and the *DPM* mechanism driver in Neutrons
ML2 config file *ml2_conf.ini*::

  [DEFAULT]
  mechanism_drivers = ovs,dpm

More details can be found in the OpenStack Configuration Reference on
`docs.openstack.org <http://docs.openstack.org/>`_.

Neutron DPM agent
=================

The Neutron DPM agent on the compute node requires DPM-specific options. But
also some well known Neutron options can be set.

General Neutron options
-----------------------

The following common Neutron options can be set in the Neutron DPM agent's
configuration file:

* [default] host

* [agent] quitting_rpc_timeout

* [agent] polling_interval

More details can be found in the OpenStack Configuration Reference on
`docs.openstack.org <http://docs.openstack.org/>`_.

DPM-specific options
--------------------

Those are the DPM-specific configuration options required by the Neutron
DPM agent.

.. note::
  This configuration is auto-generated from the networking-dpm project when
  this documentation is built. So if you are having issues with an option,
  please compare your version of networking-dpm with the version of this
  documentation.

The sample configuration can also be viewed in
`file form <_static/neutron_dpm_agent.conf.sample>`_.

.. literalinclude:: _static/neutron_dpm_agent.conf.sample
