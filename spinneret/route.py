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
    return partial(_matchRoute, components, partialMatching=True)



__all__ = ['Text', 'Integer', 'route', 'subroute']
