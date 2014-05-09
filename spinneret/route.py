from collections import OrderedDict
from functools import partial
from itertools import izip_longest

from spinneret import query
from spinneret.util import contentEncoding



def Text(name, encoding=None):
    """
    Match a text route parameter.

    @type  name: L{bytes}
    @param name: Route parameter name.

    @type  encoding: L{bytes}
    @param encoding: Default encoding to assume if the I{Content-Type}
        header is lacking one.

    @return: I{callable} suitable for use with L{route} or L{subroute}.
    """
    def _match(request, value):
        return name, query.Text(
            value,
            encoding=contentEncoding(request.requestHeaders, encoding))
    return _match



def Integer(name, base=10, encoding=None):
    """
    Match an integer route parameter.

    @type  name: L{bytes}
    @param name: Route parameter name.

    @type  base: L{int}
    @param base: Base to interpret the value in.

    @type  encoding: L{bytes}
    @param encoding: Default encoding to assume if the I{Content-Type}
        header is lacking one.

    @return: I{callable} suitable for use with L{route} or L{subroute}.
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

    @type  components: I{iterable} of L{bytes} or I{callable}s
    @param components: Iterable of path components, to match against the
        request, either static strings or dynamic parameters. As a convenience,
        a single L{bytes} component containing C{/}s may be given instead of
        manually separating the components. If no components are given the null
        route is matched, this is the case where C{segments} is empty.

    @type  segments: I{sequence} of L{bytes}
    @param segments: Sequence of path segments, from the request, to match
        against.

    @type  partialMatching: L{bool}
    @param partialMatching: Allow partial matching against the request path?

    @rtype: 2-L{tuple} of L{dict} keyed on L{bytes} and L{list} of L{bytes}
    @return: Pair of parameter results, mapping parameter names to processed
        values, and a list of the remaining request path segments. If there is
        no route match the result will be C{None} and the original request path
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

    @type  components: I{iterable} of L{bytes} or I{callable}s
    @param components: Iterable of path components, to match against the
        request, either static strings or dynamic parameters. As a convenience,
        a single L{bytes} component containing C{/}s may be given instead of
        manually separating the components. If no components are given the null
        route is matched, this is the case where C{segments} is empty.

    @rtype: 2-L{tuple} of L{dict} keyed on L{bytes} and L{list} of L{bytes}
    @return: Pair of parameter results, mapping parameter names to processed
        values, and a list of the remaining request path segments. If there is
        no route match the result will be C{None} and the original request path
        segments.
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



class Router(SpinneretResource):
    """
    Resource that provides path-based routing to `IResource
    <twisted:twisted.web.resource.IResource>`.

    `Router` is designed to be used as a Python descriptor, and route handlers
    decorated with `Router.route` or `Router.subroute`, route handlers should
    any value supported by `SpinneretResource.locateChild
    <spinneret.resource.SpinneretResource.locateChild>`.
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


    def route(self, *components):
        """
        See `spinneret.route.route`.

        This decorator can be stacked with itself to specify multiple routes
        with a single handler.
        """
        def _factory(f):
            self._addRoute(f, route(*components))
            return f
        return _factory


    def subroute(self, *components):
        """
        See `spinneret.route.subroute`.

        This decorator can be stacked with itself to specify multiple routes
        with a single handler.
        """
        def _factory(f):
            self._addRoute(f, subroute(*components))
            return f
        return _factory


    def _matchRoute(self, request, segments):
        """
        Find a route handler that matches the request path and invoke it.
        """
        for name, meth, route in self._routes:
            matches, remaining = route(request, segments)
            if matches is not None:
                return meth(self._self, request, matches), remaining
        return None, segments


    def render(self, request):
        # This only exists to handle the null route case, ie. there are no
        # segments so this resource's render method is invoked.
        result, segments = self._matchRoute(request, [])
        if result is None:
            result = NotFound()
        return self._handleRenderResult(request, result.render(request))


    def locateChild(self, request, segments):
        return self._matchRoute(request, segments)



__all__ = ['Router', 'Any', 'Text', 'Integer', 'route', 'subroute']
