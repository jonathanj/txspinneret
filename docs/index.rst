.. Spinneret documentation master file, created by
   sphinx-quickstart on Wed May  7 15:43:13 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Spinneret: Twisted Web's Silk Spinner
=====================================

Release v\ |release|.


What is this?
-------------

Spinneret is a collection of higher-level utility classes and functions to make
writing complex Twisted Web applications far simpler, it is designed to easily
integrate with existing Twisted Web projects for things like the improved
``IResource`` implementations.


Why is this one different?
--------------------------

While I think `Klein`_ is a fantastic library—and a terrific source of
inspiration—there are some fundamental aspects I disagree with, not to mention
Spinneret includes a number of other utilities to make other aspects of Twisted
Web development easier. However, using Spinneret to enhance your `Klein`_ (or
any other Twisted Web) application is not only trivial and perfectly reasonable
but also encouraged!

.. _Klein: https://github.com/twisted/klein


Installation
============

.. code-block:: bash

    $ pip install txspinneret

Or to install the latest development version:

.. code-block:: bash

    $ pip install git+git://github.com/jonathanj/txspinneret


Documentation
-------------

.. toctree::
   :maxdepth: 2

   route
   query
   resource

API documentation
-----------------

.. toctree::
   :maxdepth: 2

   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

