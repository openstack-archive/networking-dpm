..
      Copyright 2016-2017 IBM
      All Rights Reserved.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

Welcome to networking-dpm's documentation!
==========================================

This project provides the OpenStack Neutron mechanism driver and L2 agent for
the PR/SM hypervisor of IBM z Systems and IBM LinuxOne machines that are in the
DPM (Dynamic Partition Manager) administrative mode.

The DPM mode enables dynamic capabilities of the firmware-based PR/SM
hypervisor that are usually known from software-based hypervisors, such as
creation, deletion and modification of partitions (i.e. virtual machines) and
virtual devices within these partitions, and dynamic assignment of these
virtual devices to physical I/O adapters.

The Neutron mechanism driver and L2 agent for DPM components are needed on
OpenStack compute nodes for DPM, along with the Nova virtualization driver for
DPM.

For details about OpenStack for DPM, see the `documentation of the nova-dpm
OpenStack project`_.

.. _`documentation of the nova-dpm OpenStack project`:
   http://nova-dpm.readthedocs.io/en/latest/.

Overview
========

.. toctree::
    :maxdepth: 2

    history

Using networking-dpm
====================

.. toctree::
    :maxdepth: 2

    installation
    configuration
    hardware_support

Contributing to the project
===========================

.. toctree::
    :maxdepth: 2

    contributing
    specs/index

Links
=====

* Documentation: `<http://networking-dpm.readthedocs.io/en/latest/>`_
* Source: `<http://git.openstack.org/cgit/openstack/networking-dpm>`_
* Github shadow: `<https://github.com/openstack/networking-dpm>`_
* Bugs: `<http://bugs.launchpad.net/networking-dpm>`_
* Gerrit: `<https://review.openstack.org/#/q/project:openstack/networking-dpm>`_
