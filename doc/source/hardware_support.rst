.. _hardware_support:

================
Hardware Support
================

IBM z Systems z13 and LinuxONE
------------------------------

OSA Adapters
~~~~~~~~~~~~

.. list-table:: OSA adapters
    :header-rows: 1
    :widths: 40 15 15 15 15

    * - Adapter
      - Feature Codes
      - CHPIDS per adapter
      - Ports per CHPID
      - Total ports
    * - OSA-Express5S 10 GbE `[2]`_
      - #0415, #0416
      - 1
      - 1
      - 1
    * - OSA-Express5S GbE `[2]`_
      - #0413, #0414
      - 1
      - 2
      - 2
    * - OSA-Express5S 1000BASE-T Ethernet `[2]`_
      - #0417
      - 1
      - 2
      - 2
    * - OSA-Express4S GbE `[6]`_
      - #0404, #0405
      - 2
      - 2
      - 4
    * - OSA-Express4S 10 GbE `[6]`_
      - #0406, #0407
      - 1
      - 1
      - 1
    * - OSA-Express4s 1000BASE-T `[6]`_
      - #0408
      - 2
      - 2
      - 4

Adapters with multiple ports per CHPID
++++++++++++++++++++++++++++++++++++++

Consider the following when using an adapter with multiple
ports per CHPID (all 1 GbE adapters):

Due to technical limitations always both adapter ports are available to
the operating system in the partition. The OpenStack
`DPM guest image tools <https://review.openstack.org/426809>`_ take care
of configuring the correct port. However, it is not technically prevented
that an administrator of the operating system could deconfigure the current
port and configure the other port of the adapter.


Therefore the recommendation is to only wire a single adapter port of such
adapters, or wire both into the same network.

Max amount of NICs per adapter
++++++++++++++++++++++++++++++

There's a limit on how many NICs can be created for a single OSA CHPID. This
also limits the number of Neutron Ports that correspond to a certain adapter.

* Available devices per CHPID: 1920 `[4]`_

* Devices used per NIC: 3

* = Max number of NICs: 340 NICs.

.. note::
    This is an absolute number for an adapter. If multiple hosts are
    configured to use the same adapter, they also share the 340 NICs.

.. note::
    Also partitions not used by OpenStack might consume devices of the same
    adapter configured in OpenStack. The actual number of OpenStack Neutron
    ports for this adapter decreases accordingly.

.. note::
    The limit is more a theoretical limit, as each of the maximum 85
    partitions would need to consume more than 4 NICs on a single adapter,
    which is very unlikely.

.. note::
    The number can be increased by splitting the CPC into multiple hosts
    (subsets), where each subset uses a different adapter that is wired into
    the same physical network.

Hipersockets
~~~~~~~~~~~~

An existing hipersockets network can be used as Neutron physical network.

A hipersockets network is scoped to a CEC. But Neutron requires physical
networks to be accessible on

* all non DPM compute nodes that offer access to that network

* all network nodes (for dhcp, routing and metadata)

* all DPM partitions attached to that network

Therefore the usage of hipersockets is limited to a single CEC as of today.
In the case network node (dhcp, routing, metadata) is required, it must
also reside on the CEC.


Max amount of NICs per hipersockets
+++++++++++++++++++++++++++++++++++

* Available devices: 12288 `[4]`_

* Devices used per network interface: 3

* = Max number of NICs: 4096 NICs.

This number is not per CHPID, but cross all 32 CHPIDs `[5]`_!

.. note::
  4096 relates to NICs on all existing hipersockets networks on this CEC.
  If another hipersockets is configured on this CEC, the amount of NICs
  decreases by the number of already used NICs.


RoCE Adapters
~~~~~~~~~~~~~

RoCE adapters are currently not supported.

.. _[2]: http://www-03.ibm.com/systems/z/hardware/networking/features.html
.. _[4]: http://www.redbooks.ibm.com/redbooks/pdfs/sg245948.pdf
.. _[5]: http://www.redbooks.ibm.com/redbooks/pdfs/sg246816.pdf
.. _[6]: http://www.redbooks.ibm.com/redbooks/pdfs/sg245444.pdf