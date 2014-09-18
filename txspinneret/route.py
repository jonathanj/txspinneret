"""
URL routing for Twisted Web resources.

A Python-based Domain Specific Language is used to specify and match routing
paths, string literal components are matched for structure while plain callable
components match segment values and are stored by name for use in the handler,
assuming all the components match; this makes it trivial to create new
functions to match path components.

`route` is used to match a URL exactly (the number of route components must
match the number of URL path segments) while `subroute` is used to match a URL
prefix (the specified route components must match the respective segments in
a URL path, additional segments are used in child resource location as normal.)

`Router` is an `IResource` that allows decorating methods as route or subroute
handlers.
"""
from collections import OrderedDict
from functools import partial, wraps
from itertools import izip_longest

from zope.interface import implementer

from txspinneret import query
from txspinneret.resource import (
    ISpinneretResource, NotFound, SpinneretResource)
from txspinneret.util import contentEncoding



def Text(name, encoding=None):
    """
    Match a route parameter.

    `Any` is a synonym for `Text`.

    :type  name: `bytes`
    :param name: Route parameter name.

    :type  encoding: `bytes`
    :param encoding: Default encoding to assume if the ``Content-Type``
        header is lacking one.

    :return: ``callable`` suitable for use with `route` or `subroute`.
    """
    def _match(request, value):
        return name, query.Text(
            value,
            encoding=contentEncoding(request.requestHeaders, encoding))
    return _match



Any = Text



def Integer(name, base=10, encoding=None):
    """
    Match an integer route parameter.

    :type  name: `bytes`
    :param name: Route parameter name.

    :type  base: `int`
    :param base: Base to interpret the value in.

    :type  encoding: `bytes`
    :param encoding: Default encoding to assume if the ``Content-Type``
        header is lacking one.

    :return: ``callable`` suitable for use with `route` or `subroute`.
    """
    def _match(request, value):
        return name, query.Integer(
            value,
            base=base,
            encoding=contentEncoding(request.requestHeaders, encoding))
    return _match



def _matchRoute(components, request, segments, partialMatching):
    """
    Match a request path against our path components.

    The path components are always matched relative to their parent is in the
    resource hierarchy, in other words it is only possible to match URIs nested
    more deeply than the parent resource.

    :type  components: ``iterable`` of `bytes` or `callable`
    :param components: Iterable of path components, to match against the
        request, either static strings or dynamic parameters. As a convenience,
        a single `bytes` component containing ``/`` may be given instead of
        manually separating the components. If no components are given the null
        route is matched, this is the case where ``segments`` is empty.

    :type  segments: ``sequence`` of `bytes`
    :param segments: Sequence of path segments, from the request, to match
        against.

    :type  partialMatching: `bool`
    :param partialMatching: Allow partial matching against the request path?

    :rtype: 2-`tuple` of `dict` keyed on `bytes` and `list` of `bytes`
    :return: Pair of parameter results, mapping parameter names to processed
        values, and a list of the remaining request path segments. If there is
        no route match the result will be ``None`` and the original request path
        segments.
    """
    if len(components) == 1 and isinstance(components[0], bytes):
        components = components[0]
        if components[0] == '/':
            components = components[1:]
        components = components.split('/')

    results = OrderedDict()
    NO_MATCH = None, segments
    remaining = list(segments)

    # Handle the null route.
    if len(segments) == len(components) == 0:
        return results, remaining

    for us, them in izip_longest(components, segments):
        if us is None:
            if partialMatching:
                # We've matched all of our components, there might be more
                # segments for something else to process.
                break
            else:
                return NO_MATCH
        elif them is None:
            # We've run out of path segments to match, so this route can't be
            # the matching one.
            return NO_MATCH

        if callable(us):
            name, match = us(request, them)
            if match is None:
                return NO_MATCH
            results[name] = match
        elif us != them:
            return NO_MATCH
        remaining.pop(0)

    return results, remaining



def route(*components):
    """
    Match a request path exactly.

    The path components are always matched relative to their parent is in the
    resource hierarchy, in other words it is only possible to match URIs nested
    more deeply than the parent resource.

    :type  components: ``iterable`` of `bytes` or `callable`
    :param components: Iterable of path components, to match against the
        request, either static strings or dynamic parameters. As a convenience,
        a single `bytes` component containing ``/`` may be given instead of
        manually separating the components. If no components are given the null
        route is matched, this is the case where ``segments`` is empty.

    :rtype: 2-`tuple` of `dict` keyed on `bytes` and `list` of `bytes`
    :return: Pair of parameter results, mapping parameter names to processed
        values, and a list of the remaining request path segments. If there is
        no route match the result will be ``None`` and the original request
        path segments.
    """
    return partial(_matchRoute, components, partialMatching=False)



def subroute(*components):
    """
    Partially match a request path exactly.

    The path components are always matched relative to their parent is in the
    resource hierarchy, in other words it is only possible to match URIs nested
    more deeply than the parent resource.

    If there are more request path segments than components the match may still
    be successful, the remaining path segments are returned in the second part
    of the result.

    :type  components: ``iterable`` of `bytes` or `callable`
    :param components: Iterable of path components, to match against the
        request, either static strings or dynamic parameters. As a convenience,
        a single `bytes` component containing ``/`` may be given instead of
        manually separating the components. If no components are given the null
        route is matched, this is the case where ``segments`` is empty.

    :rtype: 2-`tuple` of `dict` keyed on `bytes` and `list` of `bytes`
    :return: Pair of parameter results, mapping parameter names to processed
        values, and a list of the remaining request path segments. If there is
        no route match the result will be ``None`` and the original request
        path segments.
    """
    return partial(_matchRoute, components, partialMatching=True)



@implementer(ISpinneretResource)
class _RouterResource(object):
    """
    Resource that provides URL routing to `IResource
    <twisted:twisted.web.resource.IResource>`.
    """
    def __init__(self, obj, routes):
        """
        :param obj: Parent object containing the route handler.

        :type  routes: `list` of 3-`tuple` containing `bytes`, `callable`,
            `callable`
        :param routes: List of 3-tuple containing the route handler name, the
            route handler function and the matcher function.
        """
        self._obj = obj
        self._routes = routes


    def _matchRoute(self, request, segments):
        """
        Find a route handler that matches the request path and invoke it.
        """
        for name, meth, route in self._routes:
            matches, remaining = route(request, segments)
            if matches is not None:
                return meth(self._obj, request, matches), remaining
        return None, segments


    def render(self, request):
        # This only exists to handle the null route case, ie. there are no
        # segments so this resource's render method is invoked.
        result, segments = self._matchRoute(request, [])
        if result is None:
            result = NotFound()
        return result.render(request)


    # ISpinneretResource

    def locateChild(self, request, segments):
        return self._matchRoute(request, segments)



class Router(object):
    """
    URL routing.

    `Router` is designed to be used as a Python descriptor using `Router.route`
    or `Router.subroute` to decorate route handlers, for example:

    .. code-block:: python

        class Users(object):
            router = Router()

            @router.route('name')
            def name(self, request, params):
                # ...

    Route handlers can return any value supported by
    `ISpinneretResource.locateChild`.

    Calling `Router.resource` will produce an `IResource
    <twisted:twisted.web.resource.IResource>`.
    """
    def __init__(self):
        self._routes = []


    def _forObject(self, obj):
        """
        Create a new `Router` instance, with it's own set of routes, for
        ``obj``.
        """
        router = type(self)()
        router._routes = list(self._routes)
        router._self = obj
        return router


    def __get__(self, obj, type=None):
        if obj is None:
            return self
        return self._forObject(obj)


    def _addRoute(self, f, matcher):
        """
        Add a route handler and matcher to the collection of possible routes.
        """
        self._routes.append((f.func_name, f, matcher))


    def resource(self):
        """
        Create an `IResource <twisted:twisted.web.resource.IResource>` that
        will perform URL routing.
        """
        return SpinneretResource(_RouterResource(self._self, self._routes))


    def route(self, *components):
        """
        See `txspinneret.route.route`.

        This decorator can be stacked with itself to specify multiple routes
        with a single handler.
        """
        def _factory(f):
            self._addRoute(f, route(*components))
            return f
        return _factory


    def subroute(self, *components):
        """
        See `txspinneret.route.subroute`.

        This decorator can be stacked with itself to specify multiple routes
        with a single handler.
        """
        def _factory(f):
            self._addRoute(f, subroute(*components))
            return f
        return _factory



def routedResource(f, routerAttribute='router'):
    """
    Decorate a router-producing callable to instead produce a resource.

    This simply produces a new callable that invokes the original callable, and
    calls ``resource`` on the ``routerAttribute``.

    If the router producer has multiple routers the attribute can be altered to
    choose the appropriate one, for example:

    .. code-block:: python

        class _ComplexRouter(object):
            router = Router()
            privateRouter = Router()

            @router.route('/')
            def publicRoot(self, request, params):
                return SomethingPublic(...)

            @privateRouter.route('/')
            def privateRoot(self, request, params):
                return SomethingPrivate(...)

        PublicResource = routedResource(_ComplexRouter)
        PrivateResource = routedResource(_ComplexRouter, 'privateRouter')

    :type  f: ``callable``
    :param f: Callable producing an object with a `Router` attribute, for
        example, a type.

    :type  routerAttribute: `str`
    :param routerAttribute: Name of the `Router` attribute on the result of
        calling ``f``.

    :rtype: `callable`
    :return: Callable producing an `IResource`.
    """
    return wraps(f)(
        lambda *a, **kw: getattr(f(*a, **kw), routerAttribute).resource())



__all__ = [
    'Router', 'Any', 'Text', 'Integer', 'route', 'subroute',
    'routedResource']
