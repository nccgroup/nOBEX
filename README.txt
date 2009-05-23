=====================
PyOBEX Python Package
=====================

:Author: `David Boddie`_
:Date: 2009-05-24
:Version: 0.23

*Note: This text is marked up using reStructuredText formatting. It should be
readable in a text editor but can be processed to produce versions of this
document in other formats.*


.. contents::


Introduction
------------

The Object Exchange (OBEX_) protocol is a widely used protocol for network
communication between Bluetooth and infra-red devices that provides the
foundation for a number of common tasks, such as file transfer and data
synchronization via the use of "profiles".

Although Bluetooth communication is well-supported on the most popular
operating systems, support for OBEX is limited by the restricted amount of
information freely available on the protocol. The specification of the protocol
is published by the Infrared Data Association (IrDA_). Non-members of this
association must pay a fee to obtain a copy of the specification document.

Most applications and libraries that provide connectivity between, for example,
desktop computers and mobile phones use the OpenOBEX_ library to communicate
using the OBEX protocol.

This package provides a simple Python_ implementation of aspects of the OBEX
protocol based on the information available in freely available
`Bluetooth specifications`_ and other openly accessible online resources.
It is not intended to be a complete, accurate, or fully functioning
implementation of the protocol.

This package depends on Bluetooth support in the standard Python ``socket``
module. Users of Linux and Windows XP systems may also find the PyBluez_
package useful; this provides the ``bluetooth`` module described below.


Installation
------------

To install the package alongside other packages and modules in your Python
installation, unpack the contents of the archive. At the command line, enter
the directory containing the ``setup.py`` script and install it by typing the
following::

  python setup.py install

You may need to become the root user or administrator to do this.


Locating the Bluetooth device
-----------------------------

Low level discovery of Bluetooth devices and services is provided by the
``bluetooth`` module, distributed as part of the PyBluez_ package. You need to
use the following calls to determine the address of the device you wish to
connect to.

Discover the devices available by calling::

  devices = bluetooth.discover_devices()

Look up names by calling::

  bluetooth.lookup_name(device_address)

on each device in the devices list.

Find out about the services provided by a device by calling::

  bluetooth.find_service(address=device_address)

The file transfer service has the service ID, "E006", so we can find out the
port on the device that we need to connect to when using the BrowserClient
from the PyOBEX.client module::

  services = bluetooth.find_service(uuid="E006", address=device_address)

The list returned contains dictionaries corresponding to each service. The port
used by a service can be obtained from the "port" dictionary entry. Assuming
that the previous line of code returned a list containing a single item, we can
obtain the port using the following code::

  port = services[0]["port"]

This integer value will be required when connecting to the service.


Using the PyOBEX package
------------------------

The PyOBEX package contains the following modules:

``__init__.py``
            Package file for the PyOBEX Python package.
``common.py``
            Classes providing common facilities for other modules.
``client.py``
            Client classes for sending OBEX requests and handling responses.
``headers.py``
            Classes encapsulating OBEX headers.
``requests.py``
            Classes encapsulating OBEX requests.
``responses.py``
            Classes encapsulating OBEX responses.

For most people, the client module is the most useful module because it
provides a reasonably high level API that can be used to interact with a
Bluetooth device.

Using appropriate values for ``device_address`` and ``port`` obtained using the
``bluetooth`` module, or alternative tools on your system, the following code
can be used to list the files in the root directory on a device::

  from PyOBEX.client import BrowserClient
  client = BrowserClient(device_address, port)
  client.connect()
  client.listdir()
  client.disconnect()

Other methods of the ``BrowserClient`` object can be used to get and put files,
set the current directory and delete files. Use the interactive help facilities
to find out more or read the docstrings in the source code.


Resources
---------

Listing services under Linux::

  sdptool browse <device address>

A list of services is available in the OpenOBEX Trac site:

* http://www.openobex.org
* http://dev.zuckschwerdt.org/openobex/wiki/ObexFtpServices


Notes on the Sony Ericsson K750i
--------------------------------

In file browsing mode, you may be able to obtain low level information about
the directory structure on the phone by calling the client's get() method with
an empty string.


License
-------

The contents of this package are licensed under the GNU General Public License
(version 3 or later)::

 PyOBEX, a Python package implementing aspects of the Object Exchange (OBEX) protocol.
 Copyright (C) 2007 David Boddie <david@boddie.org.uk>

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.



.. _`IrDA`:                     http://www.irda.org/
.. _`OBEX`:                     http://bluetooth.com/Bluetooth/Technology/Works/OBEX.htm
.. _`Bluetooth specifications`: http://bluetooth.com/Bluetooth/Technology/Building/Specifications/Default.htm
.. _`OpenOBEX`:                 http://dev.zuckschwerdt.org/openobex/
.. _`PyBluez`:                  http://code.google.com/p/pybluez/
.. _Python:                     http://www.python.org/
.. _`David Boddie`:             mailto:david@boddie.org.uk
