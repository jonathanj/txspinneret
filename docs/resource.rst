.. py:currentmodule:: txspinneret.resource

Resource Utilities
==================

A collection of higher-level Twisted Web resource utilities, suitable for use
with any existing `IResource` implementations.


More featureful resources
-------------------------

`ISpinneretResource` is cut-down version of `IResource` that allows child
location (via `ISpinneretResource.locateChild`) and rendering (via the normal
``render_GET``, ``render_POST``, etc. methods) to return a 2-`tuple` of firstly
any of the following:

    * `bytes`, in the same way that `IResource` does;
    * An object that can be adapted to either `IResource` or `IRenderable`;
    * A `URLPath` instance, to indicate an HTTP redirect;
    * Or a `Deferred` that results in any of the above values.

And secondly, a `list` of remaining path segments to be processed.

`ISpinneretResource` implementations may be adapted to `IResource` via
`SpinneretResource`, to produce a resource suitable for use with Twisted Web.


Negotiating resources based on ``Accept``
-----------------------------------------

When building an API, in particular, you may want to negotiate the resource
that best fits what the client is willing to accept, as specified in the
``Accept`` header; enter `ContentTypeNegotiator`. For example: If the client
indicates it accepts, in order, ``application/xml`` and ``application/json``
and your service supports JSON and HTML, you are able to deliver a result that
the client finds acceptable. It is also possible to allow falling back to
a default representation in the case where negotiations fail.

An example of supporting JSON and HTML might be:

.. literalinclude:: examples/negotiator.py

(Source: :download:`negotiator.py <examples/negotiator.py>`)

Putting this in a file called ``negotiator.py`` and running ``twistd -n web
--class=negotiator.start`` will create a resource where performing an HTTP
``GET`` on ``/`` with a ``text/html`` ``Accept`` header (or no ``Accept``
header) results in an HTML page, while an ``Accept`` header of
``application/json`` results in a JSON response:

.. code-block:: console

    $ curl -H 'Accept: application/json' http://localhost:8080/
    {"name": "Bob"}

While any other content type results in the HTML page.
