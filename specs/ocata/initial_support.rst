..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

================================================
Initial networking support for OpenStack for DPM
================================================

https://bugs.launchpad.net/networking-dpm/+bug/1646095


Problem Description
===================

Requirements
------------

* The OpenStack user should not care about the adapter type used for its
  networking.

* Support Flat networking

* DPM backed instances should be able to communicate with non DPM backed
  instances in the same cloud.

* DPM backed instances should be able to communicate with external network
  participants not managed by OpenStack.

* DPM backed instances should be able to use a Neutron router and floating ips.


Out of scope

* Live migration is not considered

* Network virtualization via Tunneling (e.g. VXLAN, GRE, STT) and VLAN


.. _adapters_and_ports:

Adapters and Adapter Ports
--------------------------

Adapters from DPM API Perspective:

::

    +-------+
    |       |
    |  HMC  |
    |       |
    +--+----+
       | 1
       |
       | *
    +--+----+       +---------------+       +----------+
    |       |1     *|               | 1   * |          |  is a
    |  CEC  +-------+ DPM Partition +-------+ DPM NIC  +<------+
    |       |       |               |       |          |       |
    +---+---+       +---------------+       +-----+----+       |
        | 1                                     ^              |
        |                                  is a |              |
        |                                       |              |
        |                               +-------+----+  +------+------+
        |                               |     DPM    |  |    DPM      |
        |                               |  RoCE NIC  |  | OSA/HS NIC  |
        |                               |            |  |             |
        |                               +--------+---+  +-------------+
        |                                        | *           *|
        |                                        |              |
        |                                        |             1|
        |                                        |       +--------------------+
        |                                        |       |                    |
        |                                        |       | DPM Virtual Switch |
        |                                        |       |                    |
        |                                        |       +----+---------------+
        |                                        |            | 1
        |                                        |            |
        |  *                                     | 1          | 1
    +---+---------------+                       ++------------+-----+
    |                   | 1                 1+2 |                   |
    |      DPM Adapter  +-----------------------+ DPM Network port  |
    |                   |                       |                   |
    +-------------------+                       +-------------------+

The following DPM objects represent system hardware:

* CEC

* DPM Adapter

* DPM Network port

* DPM Virtual Switch (OSA & Hipersockets)

.. note::
  A special case is Hipersockets. It's not hardware but firmware and therefore
  the corresponding adapter and vswitch objects can get created via the HMC
  Web Services API as well.

The following DPM objects are dynamic resources that can be created via the
HMC WS API:

* Partition

* NIC

The HMC istelf is not a DPM object at all. It's just the management interface
hosting the HMC WS API.

OSA Adapter
~~~~~~~~~~~

The DPM API allows attaching a partition to an OSA adapter port. However this
attachment is not honored at all. Although the a partition was attached to port
1, the operating system has access to both ports!

The configuration of the adapter port (0 or 1) is from within the Linux
via a network devices portno attribute:

::

  cat /sys/devices/qeth/0.0.1530/portno

By default Linux configures the port 0. In order to use port 1, the sysfs
attribute must be explicitly changed from within the Linux.

It is not possible to configure both ports in parallel using the same NIC.
A separate NIC to the same adapter would need to be assigned to the partition.

RoCE Adapter
~~~~~~~~~~~~

The DPM API allows attaching a partition to an RoCe adapter port. However this
attachment is not honored at all. Although the a partition was attached to port
1, the operating system has access to both ports!

In contradiction to OSA both ports are assigned to an LPAR and both ports
are configured by Linux. However only a single IP address is assigned to both
ports, as from Neutron perspective this is a single port!

Hipersockets
~~~~~~~~~~~~

Hipersockets is CEC internal network implemented in firmware.

Proposed Change
===============

Supported Adapters
------------------

OSA (Open Systems Adapter)
~~~~~~~~~~~~~~~~~~~~~~~~~~


.. list-table:: Available OSA adapters on z13
    :header-rows: 1
    :widths: 40 10 10 10 10 10 10

    * - Adapter
      - Feature Codes
      - available on
      - CHPIDS per adapter
      - Ports per CHPID
      - Total ports
      - Supported by DPM OpenStack
    * - OSA-Express5S 10 GbE `[2]`_
      - #0415, #0416
      - z13
      - 1
      - 1
      - 1
      - yes
    * - OSA-Express5S GbE `[2]`_
      - #0413, #0414
      - z13
      - 1
      - 2
      - 2
      - yes (b)
    * - OSA-Express5S 1000BASE-T Ethernet `[2]`_
      - #0417
      - z13
      - 1
      - 2
      - 2
      - yes (b)
    * - OSA-Express4S GbE `[6]`_
      - #0404, #0405
      - z13 (a)
      - 2
      - 2
      - 4
      - yes (b)
    * - OSA-Express4S 10 GbE `[6]`_
      - #0406, #0407
      - z13 (a)
      - 1
      - 1
      - 1
      - yes
    * - OSA-Express4s 1000BASE-T `[6]`_
      - #0408
      - z13 (a)
      - 2
      - 2
      - 4
      - yes (b)


( a ) Available on carry forward only

( b ) Supported with restrictions described in this chapter

.. note::
  All 10 Gbit/s adapters only have 1 port. The special cases are only the
  1 Gbit/s adapters.

The multiport issues described in :ref:`adapters_and_ports` should
be documented. For maximum security the recommendation is to only wire port 0
of an multiport adapter or to wire both ports into the same physical network.


For usage of port 1, some logic inside the guest image is required to determine
which port should be configured. As of today there's no way to figure out
if port 0 or 1 was chosen from with the Operating System.

.. _roce_adapter:

10 GbE RoCE (RDMA over Converged Ethernet) Express
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Available RoCE adapters on z13
    :header-rows: 1

    * - Adapter
      - No. ports per feature (FID)
      - supported
    * - 10 GbE RoCE Express (CX3)
      - 2
      - no

Due to the multiport issues described in :ref:`adapters_and_ports` the RoCE
adapter is not supported at all.

Alternative: Document that both ports must be wired into the same physical
network. If that is the case, a bond could be configured on top of those
2 interfaces.

Hipersockets
~~~~~~~~~~~~

.. list-table:: Hipersockets on z13
    :header-rows: 1

    * - Adapter
      - No. ports per feature (CHPID)
      - supported
    * - Hipersockets
      - n/a
      - yes

Due to the facts described in :ref:`adapters_and_ports` hipersockets
is only supported on Single CEC deployments. In order to use the network node
(DHCP, Routing, Floating IP, Metadata) it must also be deployed on the same
CEC with an attachment to the hipersockets network.

::

  +------------------------------+  +--------------+  +--------------+
  |                              |  |              |  |              |
  |         Network Node         |  | Instance     |  | Instance     |
  |                              |  |              |  |              |
  |                              |  |              |  |              |
  |  +---------------------+     |  |              |  |              |
  |  |      Bridge         |     |  |              |  |              |
  |  +------+-----------+--+     |  |              |  |              |
  |         |           |        |  |              |  |              |
  |  +------+------+    |        |  |              |  |              |
  |  | Bond        |    |        |  |              |  |              |
  |  +--+-------+--+    |        |  |              |  |              |
  |     |       |       |        |  |              |  |              |
  |  +--+--+ +--+--+  +-+--+     |  |    +----+    |  |    +----+    |
  |  | OSA | | OSA |  | HS |     |  |    | HS |    |  |    | HS |    |
  +--+--+--+-+--+--+--+-+--+-----+  +----+-+--+----+  +----+-+--+----+
        |       |       |                  |                 |
        |       |       |                  |                 |
        |       |       |                  |                 |
        |       |       +------------------+-----------------+
        |       |
        +       +
       external network


The OpenStack user is not aware if hipersockets is being used or not.

.. note::

  DPM offers a ReST API to dynamically create a new hipersockets adapter.
  Neutron will not take use of this DPM ReST API but assumes that the
  hipersockets network already exists.

.. _dpm_neutron_phys_network:

Physical networks
-----------------

Neutron Reference implementations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the Neutron reference implementations (linuxbridge, ovs, macvtap), the
mapping between physical networks and hyperivsor interfaces is a 1:1 mapping.
::

  +------------------+ 1      1 +---------------------------+
  | physical network +----------+ hypervisor net-interface  |
  +------------------+          +---------------------------+

There is no support for multiple hypervisor interfaces going into the same
physical network. To achieve this, those interfaces need to be bonded in the
hypervisor, that Neutron again sees a single interface.

Mapping that to DPM
~~~~~~~~~~~~~~~~~~~

Mapping this to DPM, the mapping between physical networks and adapter-ports
must be a 1:1 mapping.
::

  +------------------+ 1      1 +---------------+
  | physical network +----------+ adapter-port  |
  +------------------+          +---------------+

Consequences:

A physical network can only be backed by a single adapter and there use
only a single port.

OSA adapter
+++++++++++

1920 devices per CHPID means 1920/3= 340 NICs. See `[4]`_ page 10.

-> A physical network can serve 340 NICs on a CEC.

Hipersockets
++++++++++++

12288 devices means 12288/3 = 4096 NICs across all 32
Hipersockets networks. See `[5]`_ page 8.

-> A physical network can serve a total number of 4096 NICs.

.. note::
  4096 relates to NICs on all existing hipersockets networks on this CEC.
  If another hipersockets is configured on this CEC, the amount of NICs
  decreases by the number of already used NICs.

.. note::
  As only the hipersocket bridge solution is supported, the maximum
  number of NICs available for OpenStack DPM partitions is 4095, as
  also the bridge partition needs one attachment.

Logical networks
----------------

A logical network can be represented by

* a physical network (= flat provider network)

.. note::

  Explicitly out of scope are VLAN and tunneled networks like VXLAN or GRE.

Neutron Mechanism Driver and L2 Agent
-------------------------------------

A mechanism driver and a Neutron l2 agent (per CPCSubset) get implemented.

* Agent

  * Reads config file on startup

  * Looks up virtualswitch object-ids by adapter object-id provided by the
    configuration

  * Sends status reports to Neutron including the resolved configuration per
    CPCSubset

   * Checks for added/removed NICs

     * Does additional configuration for the NIC (None to be done in the
       first release)

     * Reports the Neutron Server about the port configured

* Mechanism driver

  * Stores all the status information from the agents

  * On portbinding request, it looks up the corresponding agent in the database
    and adds the relevant information to the response.


.. note::

  As of today, the agent itself does not do any configuration of the NIC.
  Therefore no polling for new NICs needs to be done. Nova can continue
  instance start without waiting for the vif-plug event.

  Going with an agent looks a bit overkilled, but going this way, we are
  prepared for the future. Also we can take use of the existing ML2
  Framework with it's AgentMechanismDriver Base classes and eventually the
  ml2 common agent. Eventually it's easier to use the polling right from
  the beginning, as it's integrated into those existing frameworks.

  Another argument for going with this design is keeping the overall node
  architecture clean. E.g. all compute node related configuration is
  present on the compute node only.

Alternatives:

* Go with a mechanism driver (server) only implementation

* Have one agent per HMC

Neutron mechanism driver (server)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

VNIC Type and VIF_TYPE
++++++++++++++++++++++
Use::

  VNIC_TYPE='normal'

It should be totally transparent to the user, if Hipersockets or OSA is being
used. It should only depend on the admin if a Hipersockets or OSA attachment is
used (depending on the configuration).

Use::

  vif_type = "dpm_vswitch"


The vif_type determines how Nova should attach the guest to network.


.. _`SequenceDiagram`:

Sequence diagram
----------------

.. seqdiag::

   diagram {
      // Do not show activity line
      activation = none;
      n-cpu; q-svc; q-agt; HMC;

      === Loop ===
      q-agt ->> q-svc [label = "report configuration"];
      === End Loop ===

      n-cpu -> q-svc [label = "create port
        {host_id:host,
         vnic_type:Normal}"];
      n-cpu <-- q-svc [label = "port {vif_type:dpm,
         vif_details={vswitch_id:uuid, vlan:1}"];


      n-cpu -> HMC [label = "create partition"];
      n-cpu -> HMC [label = "add NIC to partition"];
      === Check for added/removed NICs===
      n-cpu -> n-cpu [label = "wait for vif-plugged-event"];
      q-agt -> HMC [label = "loop for new devices", note = "endless loop"];
      q-agt -> HMC [label = "configure device"];
      q-agt ->> q-svc [label = "report as up"];
      q-svc ->> n-cpu [label = "vif-plugged-event"];
      === END ===
      n-cpu -> HMC [label = "start partition"];

    }

* The Neutron agent (q-agt) frequently sends its configuration to the Neutron
  server. The relevant pieces are

  * host = CPCSubset host identifier

  * mappings = physical network and

    * OSA/HS: virtual switch object-id

* On spawn instance, nova compute agent (n-cpu) asks Neutron to create a port
    with the following relevant details

  * host = the CPCSubset host identifier on which the instance should be
    spawned

* Neutron server (q-svc) now looks its database for the corresponding agent
  configuration. It adds the required details to the ports binding:vif_details
  dictionary. The following attributes are required:

  * virtual switch object-id (OSA, HS)

* Nova compute creates the Partition (This can also done before the port
  details are requested).

* Nova compute attaches the NIC to the partition and waits for the
  vif-plugged-event

* Neutron agent detects that this new NIC is available.

  * Neutron agent does configurations on the appeared NIC (optional).

  * Neutron agent reports existence of the device to the Neutron server.

* The Neutron server sends the vif-plugged-event to Neutron.

* Nova compute starts the partition.

Neutron configuration
---------------------

The following configuration is required

* Mapping from physical network to adapter port

* HMC Access URL and credentials (depends on Design of configuration options)


Identification of an adapter-port
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The configuration specifies an network adapter port along the following
parameters:

* adapter object-id

* port element-id

This works for all adapters (RoCE, OSA, Hipersockets) in the same manner!

A script should be provided, that helps the administrator to figure out the
object-id and the port element-id along the card location parameter or the
PCHID.


Alternatives for identifying an adapter port:

* The card location parameter and port element-id

* PCHID/VCHID and port element-id

* OSA/HS: Virtual-switch object-id

Neutron configuration options
+++++++++++++++++++++++++++++

There is one Neutron agent per HMC and cloud. Therefore the following
configuration is required for the Neutron agent.

The Neutron server does not need configuration options.

*HMC access information*

::

  hmc =
  hmc_username =
  hmc_password =

.. note::

  How those options look like is not part of this specification. Neutron
  would use the same config parameters as Nova. All options that Nova
  implements need also be implemented by the Neutron agent as well. The shown
  options are just boilerplate options.

*Physical adapter mappings*

::

  [dpm]
  # List of mappings between physical network, and adapter-id/port combination
  # <port element-id> defaults to 0
  # physical_adapter_mappings = <physical_network>:<adapter object-id>[:<port element-id>],...
  physical_adapter_mappings = physnet1:2841d931-6662-4c85-be2d-9b5b0b76d342:1,
                              physnet2:4a7abde3-964c-4f6a-918f-fbd124c4d7d3


A mapping between physical network and the combination of adapter object-id and
port element-id.

References
==========

.. _[1]: https://bugs.launchpad.net/neutron/+bug/1580880
.. _[2]: http://www-03.ibm.com/systems/z/hardware/networking/features.html
.. _[4]: http://www.redbooks.ibm.com/redbooks/pdfs/sg245948.pdf
.. _[5]: http://www.redbooks.ibm.com/redbooks/pdfs/sg246816.pdf
.. _[6]: http://www.redbooks.ibm.com/redbooks/pdfs/sg245444.pdf
