.. _installation:

============
Installation
============

The networking-dpm package provides two components:

* Neutron mechanism driver for DPM

* L2 agent for DPM

The Neutron mechanism driver for DPM must be registered with the Neutron
server on the OpenStack controller node.

The L2 agent for DPM mnust be installed on every OpenStack compute node for
DPM.

This section describes the manual installation of these components onto a
controller node and compute node that have already been installed by some
means.

The networking-dpm package is released on PyPI as package `networking-dpm`_.

.. _`networking-dpm`: https://pypi.python.org/pypi/networking-dpm

The following table indicates which version of the networking-dpm package on
PyPI to use for a particular OpenStack release:

.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - OpenStack release
     - networking-dpm version
   * - Ocata
     - 1.x.x

Typically, the networking-dpm package will increase its major version number by
one for each new OpenStack release.

If you want to install the package for a particular OpenStack release,
it is recommended to use the package that has been released to PyPI, rather
than installing from a particular branch of a Git repository.

To do that, identify the major version number for the desired OpenStack release
from the table above, and install the latest minor and fix version of the
package for that major version, also specifying the global upper constraints
file for the desired OpenStack release (the latter ensures that you get the
right versions of any dependent packages).

For example, for Ocata:

.. code-block:: console

    $ constraints_file=https://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?h=stable/ocata
    $ pip install -c$constraints_file "networking-dpm >=1,<2"

If you have good reasons to install the latest not yet released fix level of
the networking-dpm package for a particular (released) OpenStack release,
install the networking-dpm package from the stable branch of the GitHub repo
for that OpenStack release:

For example, for Ocata:

.. code-block:: console

    $ constraints_file=https://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?h=stable/ocata
    $ pip install -c$constraints_file git+https://git.openstack.org/openstack/networking-dpm@stable/ocata

If you are a developer and want to install the latest code of the
networking-dpm package for the OpenStack release that is in development:

.. code-block:: console

    $ constraints_file=https://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?h=master
    $ pip install -c$constraints_file git+https://git.openstack.org/openstack/networking-dpm@master

The pip commands above install the packages into the currently active Python
environment.

If your active Python environment is a virtual Python environment, the
commands above can be issued from a userid without sudo rights.

If you need to install the packages into the system Python environment, you
need sudo rights:

.. code-block:: console

    $ sudo pip install ...

After installing the networking-dpm package, proceed with its
:ref:`configuration`.

Note that you will also need to install and configure the nova-dpm
package on the compute node. For its documentation, see
http://nova-dpm.readthedocs.io/en/latest/.
