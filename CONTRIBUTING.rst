=========================
Contributing to Spinneret
=========================


`Spinneret <https://github.com/jonathanj/txspinneret>`_ is an open source
project that encourages community contributions to all aspects:

  * Code patches;
  * `Documentation <https://txspinneret.readthedocs.org/>`_ improvements;
  * `Bug reports <https://github.com/jonathanj/txspinneret/issues>`_;
  * Code reviews for `contributed patches
    <https://github.com/jonathanj/txspinneret/pulls>`_.


Code
====

  * Propose all code changes via a pull request in the `GitHub repository
    <https://github.com/jonathanj/txspinneret>`_;
  * Use `Twisted's coding standard`_;
  * Ensure codes changes have unit tests and good coverage;
  * New features should have examples and documentation;
  * Add yourself to ``AUTHORS``.

.. _Twisted's coding standard: http://twistedmatrix.com/documents/current/core/development/policy/coding-standard.html


Documentation
=============

  * The header order::

      ========
      Header 1
      ========

      Header 2
      ========

      Header 3
      --------

      Header 4
      ~~~~~~~~
  * Perform at least basic spelling checks;
  * Use `gender-neutral language
    <https://www.google.com/search?q=gender+neutral+language>`_ (`singular they
    <https://www.google.co.za/search?q=singular+they>`_ is great!);


Reviewing
=========

All code that is merged into Spinneret must be reviewed by at least one person
other than an author of the change.

While perfection is a noble goal it often leads to an idea that improvement
without achieving perfection is not an improvement. Improvements need only be
that, improvements. Glyph wrote a `compelling email
<https://twistedmatrix.com/pipermail/twisted-python/2014-January/027894.html>`_
on this topic, it's worth reading if you're a reviewer *or* a contributor.
