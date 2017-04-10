..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==========================
HMC Error Handling Concept
==========================

Problem Description
===================

There are situations where the connection to the Hardware Management Console
(HMC) is lost. Those errors are not handled properly today.

Proposed Change
===============

Timeout/Retry
-------------

zhmcclient allows specifying the following timeout/retry related parameters
[1]. This is based on zhmcclient version: 0.12.1.dev25


* connect_timeout

  * when zhmcclient is initiating a connecting to the HMC, this connection
    will timeout after ``connect_timeout`` seconds.
  * default: 30  [3]
  * Exception: zhmcclient.ConnectTimeout [2]
    (derived from zhmcclient.ConnectionError)
  * Proposal: use default

* connect_retries

  * if zhmcclient fails to establish a connection to the HMC (e.g. due to the
    timeout set in ``connect_timeout``), ``connect_retries`` retries will be
    made. Otherwise an exception is being thrown.
  * default: 3 [3]
  * Exception:
    * zhmcclient.ConnectTimeout [2] (derived from zhmcclient.ConnectionError)
    * zhmcclient.RequestRetriesExceeded for all other reasons [2]
      (derived from zhmcclient.ConnectionError)
  * Proposal: use default

* read_timeout

  * when zhmcclient reads an HMC http response, this will timeout after
    ``read_timeout`` seconds.
  * default: 3600  [3]
  * Exception: zhmcclient.ReadTimeout [2]
    (derived from zhmcclient.ConnectionError)
  * Proposal: 300 - It has been raised due to an issue where a partition with
    hundrets of NICs has been deleted. Such a scenario will most likely not
    happen in the openstack DPM case, as the number of NICs per partition is
    limited by the code.

* read_retries

  * if zhmcclient fails to read the http response (e.g. due to the timeout
    setting ``read_timeout``), ``read_retries`` retries will be made. If non
    of the retries was successful an exception is raised.

    .. note::
      The retry is not only trying to read the result again! Also the request
      is being issued again!
  * default: 0  [3]
  * Exception:
    * zhmcclient.ReadTimeout [2] (derived from zhmcclient.ConnectionError)
    * zhmcclient.RequestRetriesExceeded for all other reasons [2]
      (derived from zhmcclient.ConnectionError)
  * Proposal: use default

* max_redirects

  * The maximum number of http redirects.
  * default: 30  [3]
  * Exception: ?
  * Proposal: use default

* operation_timeout

  * How long the zhmcclient should wait for an asyncronous HMC operation to
    complete. The zhmcclient is polling on the corresponding 'job' object until
    the state transitions to 'complete'. It can be enabled with the parameter
    ``wait_for_completion`` on zhmcclient resource operations. The timeout is
    specified via the ``operations_timeout`` attribute. If ``None`` is given
    (default), the default value is used.
  * default: 3600  [3]
  * Exception: zhmcclient.OperationTimeout (derived from Error)
  * Proposal: 600 - We don't want to wait an hour for a job to complete.

    TBD: Which job takes that long in our case?

* status_timeout

  * This is a special parameter only used by the LPAR object. The timeout
    specifies how long to wait until the partition switches into
    ``not-operating`` state.

    -> not relevant for DPM
  * default: 60  [3]
  * Exception:
  * Proposal: use default


The proposal is to let the zhmcclient handle timeouts and retries!

How to deal with Connection errors?
-----------------------------------

What should if all zhmcclient retries failed and a connection error is raised?

Agent Start
+++++++++++

Scenario: The networking-dpm agent gets started.

Proposal: If the agent fails to establish a connection to the HMC during it's
start, the agent should terminate with a appropriate error message.

Running Agent - GET operations
++++++++++++++++++++++++++++++

Scenario: A running agent loses the connection to the HMC

*Agent object*

The neutron openvswitch agent continues running. It is logging those errors::

      2017-05-15 07:34:37.541 WARNING neutron.agent.ovsdb.native.vlog [-] tcp:127.0.0.1:6640: connection dropped (Connection refused)
      2017-05-15 07:34:37.541 INFO neutron.agent.ovsdb.native.vlog [-] tcp:127.0.0.1:6640: waiting 8 seconds before reconnect
      2017-05-15 07:34:37.542 DEBUG neutron.agent.ovsdb.native.vlog [-] tcp:127.0.0.1:6640: entering BACKOFF from (pid=17589) _transition /usr/local/lib/python2.7/dist-packages/ovs/reconnect.py:468
      2017-05-15 07:34:38.256 ERROR neutron.plugins.ml2.drivers.openvswitch.agent.openflow.native.ofswitch [req-916cbb0c-d3e4-44d3-bba1-ebc42b6e8d14 None None] Switch connection timeout

The agent status is still "UP" and "Alive"::

      $ openstack network agent show 3253b87f-20ab-4843-9bfb-1adce535167d
      +-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
      | Field             | Value                                                                                                                                                                           |
      +-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
      | admin_state_up    | UP                                                                                                                                                                              |
      | agent_type        | Open vSwitch agent                                                                                                                                                              |
      | alive             | True                                                                                                                                                                            |
      | availability_zone | None                                                                                                                                                                            |
      | binary            | neutron-openvswitch-agent                                                                                                                                                       |
      | configuration     | {u'ovs_hybrid_plug': True, u'in_distributed_mode': True, u'datapath_type': u'system', u'vhostuser_socket_dir': u'/var/run/openvswitch', u'tunneling_ip': u'192.168.222.15',     |
      |                   | u'arp_responder_enabled': False, u'devices': 6, u'ovs_capabilities': {u'datapath_types': [u'netdev', u'system'], u'iface_types': [u'geneve', u'gre', u'internal', u'ipsec_gre', |
      |                   | u'lisp', u'patch', u'stt', u'system', u'tap', u'vxlan']}, u'log_agent_heartbeats': False, u'l2_population': True, u'tunnel_types': [u'vxlan'], u'extensions': [],               |
      |                   | u'enable_distributed_routing': True, u'bridge_mappings': {u'public': u'br-ex'}}                                                                                                 |
      | created_at        | 2017-03-28 10:48:55                                                                                                                                                             |
      | description       | None                                                                                                                                                                            |
      | host              | ubuntu-xenial                                                                                                                                                                   |
      | id                | 3253b87f-20ab-4843-9bfb-1adce535167d                                                                                                                                            |
      | last_heartbeat_at | 2017-05-15 07:34:44                                                                                                                                                             |
      | name              | None                                                                                                                                                                            |
      | started_at        | 2017-03-28 10:48:55                                                                                                                                                             |
      | topic             | N/A                                                                                                                                                                             |
      +-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Heartbeat is still going on.

Proposal: Keep the agent running and reporting.

*Port object*

Even though a connection error occurred with ovs agent, the status of a port
is still "UP"::

      $ openstack port show 53c8587b-18e0-463f-8136-3508db55c8da
      +-----------------------+----------------------------------------------------------------------------------+
      | Field                 | Value                                                                            |
      +-----------------------+----------------------------------------------------------------------------------+
      | admin_state_up        | UP                                                                               |
      | allowed_address_pairs |                                                                                  |
      | binding_host_id       | ubuntu-xenial                                                                    |
      | binding_profile       |                                                                                  |
      | binding_vif_details   | ovs_hybrid_plug='True', port_filter='True'                                       |
      | binding_vif_type      | ovs                                                                              |
      | binding_vnic_type     | normal                                                                           |
      | created_at            | 2017-03-28T10:49:48Z                                                             |
      | description           |                                                                                  |
      | device_id             | 33ee6a00-7726-4e83-95f5-f458d4a94f0a                                             |
      | device_owner          | network:router_centralized_snat                                                  |
      | dns_assignment        | None                                                                             |
      | dns_name              | None                                                                             |
      | extra_dhcp_opts       |                                                                                  |
      | fixed_ips             | ip_address='fd2a:d977:2be0::5', subnet_id='2e7d9bf4-66f6-45d8-8f03-9a14bd9c9fbc' |
      | id                    | 53c8587b-18e0-463f-8136-3508db55c8da                                             |
      | ip_address            | None                                                                             |
      | mac_address           | fa:16:3e:a9:3b:63                                                                |
      | name                  |                                                                                  |
      | network_id            | 95eacdce-f42c-4239-b7ab-2a48c96610d6                                             |
      | option_name           | None                                                                             |
      | option_value          | None                                                                             |
      | port_security_enabled | False                                                                            |
      | project_id            |                                                                                  |
      | qos_policy_id         | None                                                                             |
      | revision_number       | 13                                                                               |
      | security_group_ids    |                                                                                  |
      | status                | ACTIVE                                                                           |
      | subnet_id             | None                                                                             |
      | updated_at            | 2017-05-15T07:28:18Z                                                             |
      +-----------------------+----------------------------------------------------------------------------------+

Proposal: Ports (NICs) should still be treated as they were available.


Running Agent - PUT/POST operations
+++++++++++++++++++++++++++++++++++

No PUT/POST operations issued by the networking-dpm agent.

References
==========

[1] http://python-zhmcclient.readthedocs.io/en/stable/general.html#retry-timeout-configuration
[2] http://python-zhmcclient.readthedocs.io/en/stable/general.html#exceptions
[3] http://python-zhmcclient.readthedocs.io/en/latest/general.html#constants