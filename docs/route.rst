.. py:currentmodule:: txspinneret.route

URL Routing Resources
=====================

Often it is desirable to describe a resource hierarchy without having to
create a separate resource for every segment in the URL path, this is commonly
referred to as "URL routing".

A Python-based Domain Specific Language is used to specify and match routing
paths, string literal components are matched for structure while plain callable
components match segment values and are stored by name for use in the handler,
assuming all the components match; this makes it trivial to create new
functions to match path components.

In order to promote better reuse of resources—by composing and nesting them—it
is only possible to specify relative routes.


Router basics
-------------

`Router.route` will match a URL route exactly, meaning that every route
component must match the respective segment in the URL path; eg.
``route('foo')`` will only match a relative URL path of exactly one segment
that must be the string ``foo``.

`Router.subroute` will partially match a URL route, meaning that once every
route component has matched its respective segment in the URL path the route
will be a match, regardless of whether there are URL path segments left over.
This is useful for the case where you wish to match enough of the URL to know
that you should delegate to another resource.

Routes are intended to be used as method decorators and may be stacked to have
multiple routes serviced by the same handler.


Special routes
--------------

There are two routes—particularly in the case of nested routers—that may not be
obvious at first: The null root and the empty route.

Assuming we had the following hierarchy:

.. code-block:: python

    class Root(object):
        router = Router()

        @router.subroute('bar')
        def bar(self, request, params):
            return SubRoot().router


    class SubRoot(object):
        router = Router()

In the case of a request for the resource at ``/bar/`` we can match that by
declaring a route in ``SubRoot`` with ``@router.route('/')`` or
``@router.route('')`` (the empty route.) If the request was instead for the
resource at ``/bar`` (note the absence of the trailing ``/``) we can match that
with ``@router.route()`` (the null route.)


Matcher basics
--------------

`txspinneret.route` contains some basic matchers such as `Any` (which is
a synonym for `Text`) and `Integer`. These matchers are simple factory
functions that take some parameters and produce a `callable` that takes the
`IRequest` and the segment being matched, as `bytes`, returning a 2-`tuple` of
the parameter name and the processed matched value (or ``None`` if there is no
match.) Writing your own matchers to suit your needs is encouraged.


An example router
-----------------

.. literalinclude:: examples/user_router.py

(Source: :download:`user_router.py <examples/user_router.py>`)

Putting this in a file called ``user_router.py`` and running ``twistd -n web
--class=user_router.start`` you'll find it reacts as below:

.. code-block:: console

    $ curl http://localhost:8080/
    default
    $ curl http://localhost:8080/friend/chuck/friend/bob/
    bob
