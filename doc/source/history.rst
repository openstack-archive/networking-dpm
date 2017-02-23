=============
Release Notes
=============

1.0.0
=====

*networking-dpm* 1.0.0 is the first release of the Neutron mechanism driver
and its corresponding l2 agent for the PR/SM hypervisor of IBM z Systems and
IBM LinuxOne machines that are in the DPM (Dynamic Partition Manager)
administrative mode.

New Features
------------

* Support for flat networks

Known Issues
------------

* Only a single adapter can be configured per physical network
* Always port 0 of an network adapter gets autoconfigured in the guest image.
  If port 1 should be used, port 0 must be deconfigured and port 1 configured
  manually in the instance operating system after the instance has launched.
* All bug reports are listed at: https://bugs.launchpad.net/netwokring-dpm
