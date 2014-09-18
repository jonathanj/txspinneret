from collections import OrderedDict

from testtools import TestCase
from testtools.matchers import Equals, Is, Not
from twisted.web import http
from twisted.web.http_headers import Headers
from twisted.web.resource import getChildForRequest
from twisted.web.static import Data

from txspinneret.route import (
    Integer, route, routedResource, Router, subroute, Text)
from txspinneret.test.util import InMemoryRequest



class MockRequest(object):
    """
    A mock `twisted.web.iweb.IRequest`.
    """
    def __init__(self, requestHeaders=None):
        if requestHeaders is None:
            requestHeaders = Headers()
        self.requestHeaders = requestHeaders



class TextParameterTests(TestCase):
    """
    Tests for `txspinneret.route.Text`.
    """
    def test_parseBytes(self):
        """
        Parse bytes and use the default encoding of ``UTF-8``.
        """
        request = MockRequest()
        match = Text(b'foo')
        self.assertThat(
            match(request, b'42'),
            Equals((b'foo', u'42')))
        self.assertThat(
            match(request, b'\xe2\x98\x83'),
            Equals((b'foo', u'\N{SNOWMAN}')))


    def test_parseUnicode(self):
        """
        Parse a Unicode value.
        """
        request = MockRequest()
        match = Text(b'foo')
        self.assertThat(
            match(request, u'42'),
            Equals((b'foo', u'42')))
        self.assertThat(
            match(request, u'\N{SNOWMAN}'),
            Equals((b'foo', u'\N{SNOWMAN}')))


    def test_defaultEncoding(self):
        """
        Parsing bytes uses the specified default encoding.
        """
        request = MockRequest()
        match = Text(b'foo', encoding=b'utf-32')
        self.assertThat(
            match(request, u'42'),
            Equals((b'foo', u'42')))
        self.assertThat(
            match(request, b'\xff\xfe\x00\x00\x03&\x00\x00'),
            Equals((b'foo', u'\N{SNOWMAN}')))


    def test_encodingHeader(self):
        """
        When the ``Content-Type`` header is present and has a ``charset``
        parameter, use that instead of the default encoding.
        """
        request = MockRequest(
            requestHeaders=Headers(
                {b'Content-Type': [b'text/plain;charset=utf-16']}))
        match = Text(b'foo', encoding=b'utf-32')
        self.assertThat(
            match(request, u'42'),
            Equals((b'foo', u'42')))
        self.assertThat(
            match(request, b'\xff\xfe\x03&'),
            Equals((b'foo', u'\N{SNOWMAN}')))



class IntegerParameterTests(TestCase):
    """
    Tests for `txspinneret.route.Integer`.
    """
    def test_match(self):
        """
        Text values are parsed as integers.
        """
        request = MockRequest()
        match = Integer(b'foo')
        self.assertThat(
            match(request, b'42'),
            Equals((b'foo', 42)))


    def test_unparseable(self):
        """
        ``None`` is returned if the value is not a valid integer.
        """
        request = MockRequest()
        match = Integer(b'foo')
        self.assertThat(
            match(request, u'arst'),
            Equals((b'foo', None)))



class StaticRouteTests(TestCase):
    """
    Tests for `txspinneret.route.route` using only static path components.
    """
    def test_nullRoute(self):
        """
        The null route matches only zero segments.
        """
        request = MockRequest()
        self.assertThat(
            route()(request, []),
            Equals((OrderedDict(), [])))
        self.assertThat(
            route()(request, ['foo']),
            Equals((None, ['foo'])))


    def test_single(self):
        """
        Match a route with a single component.
        """
        request = MockRequest()
        self.assertThat(
            route('foo')(request, ['foo']),
            Equals((OrderedDict(), [])))


    def test_singleNoMatch(self):
        """
        Do not match a route with a single component.
        """
        request = MockRequest()
        self.assertThat(
            route('foo')(request, ['bar']),
            Equals((None, ['bar'])))


    def test_multiple(self):
        """
        Match a route with a multiple components.
        """
        request = MockRequest()
        self.assertThat(
            route('foo', 'bar')(request, ['foo', 'bar']),
            Equals((OrderedDict(), [])))


    def test_multipleNoMatch(self):
        """
        Do not match a route with a multiple components.
        """
        request = MockRequest()
        self.assertThat(
            route('bar')(request, ['foo', 'bar']),
            Equals((None, ['foo', 'bar'])))
        self.assertThat(
            route('foo', 'quux')(request, ['foo', 'bar']),
            Equals((None, ['foo', 'bar']))),


    def test_tooMany(self):
        """
        Do not match a route that has too many components or segments.
        """
        request = MockRequest()
        self.assertThat(
            route('foo', 'bar')(request, ['foo']),
            Equals((None, ['foo'])))
        request = MockRequest()
        self.assertThat(
            route('foo')(request, ['foo', 'bar']),
            Equals((None, ['foo', 'bar'])))


    def test_multipleSubroute(self):
        """
        Match a sub-route, returning the unmatched segments.
        """
        request = MockRequest()
        self.assertThat(
            subroute('foo')(request, ['foo', 'bar']),
            Equals((OrderedDict(), ['bar'])))


    def test_emptyPlainBytes(self):
        """
        Match a route against the root specified as a single plain string.
        """
        request = MockRequest()
        self.assertThat(
            subroute('/')(request, ['']),
            Equals((OrderedDict(), [])))


    def test_singlePlainBytes(self):
        """
        Match a route with a single component specified as a single plain
        string.
        """
        request = MockRequest()
        self.assertThat(
            subroute('/foo')(request, ['foo']),
            Equals((OrderedDict(), [])))


    def test_multiplePlainBytes(self):
        """
        Match a route with multiple components specified as a single plain
        string.
        """
        request = MockRequest()
        self.assertThat(
            subroute('/foo/bar')(request, ['foo', 'bar']),
            Equals((OrderedDict(), [])))



class DynamicRouteTests(TestCase):
    """
    Tests for `txspinneret.route.route` using dynamic path components.
    """
    def test_single(self):
        """
        Match a route with a single component.
        """
        request = MockRequest()
        self.assertThat(
            route(Text('name'))(request, ['foo']),
            Equals(
                (OrderedDict([('name', 'foo')]), [])))


    def test_singleNoMatch(self):
        """
        Do not match a route with a single component.
        """
        request = MockRequest()
        self.assertThat(
            route(Integer('name'))(request, ['bar']),
            Equals(
                (None, ['bar'])))


    def test_multiple(self):
        """
        Match a route with a multiple components.
        """
        request = MockRequest()
        self.assertThat(
            route(Text('name'), 'bar')(request, ['foo', 'bar']),
            Equals(
                (OrderedDict([('name', 'foo')]), [])))


    def test_multipleNoMatch(self):
        """
        Do not match a route with a multiple components.
        """
        request = MockRequest()
        self.assertThat(
            route(Text('name'), Integer('name2'))(request, ['foo', 'bar']),
            Equals((None, ['foo', 'bar'])))
        self.assertThat(
            route(Integer('name'), Text('name2'))(request, ['foo', 'bar']),
            Equals((None, ['foo', 'bar']))),


    def test_tooMany(self):
        """
        Do not match a route that has too many components or segments.
        """
        request = MockRequest()
        self.assertThat(
            route(Text('name'), Integer('name2'))(request, ['foo']),
            Equals((None, ['foo'])))
        self.assertThat(
            route(Text('name'))(request, ['foo', 'bar']),
            Equals((None, ['foo', 'bar'])))


    def test_multipleSubroute(self):
        """
        Match a sub-route, returning the unmatched segments.
        """
        request = MockRequest()
        self.assertThat(
            subroute(Text('name'))(request, ['foo', 'bar']),
            Equals(
                (OrderedDict([('name', 'foo')]), ['bar'])))



class MixedRouteTests(TestCase):
    """
    Tests for `txspinneret.route.route` using mixed static and dynamic path
    components.
    """
    def test_multiple(self):
        """
        Match a route with a multiple components.
        """
        request = MockRequest()
        segments = ['foo', 'bar', 'quux']
        self.assertThat(
            route(
                Text('name'), 'bar', 'quux')(request, segments),
            Equals(
                (OrderedDict([('name', 'foo')]), [])))
        self.assertThat(
            route(Text('name'), 'bar', Text('name2'))(request, segments),
            Equals(
                (OrderedDict([('name', 'foo'),
                              ('name2', 'quux')]), [])))


    def test_multipleNoMatch(self):
        """
        Do not match a route with a multiple components.
        """
        request = MockRequest()
        self.assertThat(
            route('foo', Integer('name'))(request, ['foo', 'bar', 'quux']),
            Equals(
                (None, ['foo', 'bar', 'quux'])))


    def test_multipleSubRoute(self):
        """
        Match a sub-route, returning the unmatched segments.
        """
        request = MockRequest()
        self.assertThat(
            subroute('foo', Text('name'))(request, ['foo', 'bar', 'quux']),
            Equals(
                (OrderedDict([('name', 'bar')]), ['quux'])))



class _RoutedThing(object):
    """
    Basic router.
    """
    router = Router()

    @router.route(b'foo')
    @router.route(b'foo2')
    def foo(self, request, params):
        return Data(b'hello world', b'text/plain')


    @router.route()
    def null(self, request, params):
        return Data(b'null route', b'text/plain')



class _SubroutedThing(object):
    """
    Basic sub-router.
    """
    router = Router()
    otherRouter = Router()

    @router.subroute(b'bar')
    def bar(self, request, params):
        return _RoutedThing().router.resource()


    @otherRouter.route(b'other')
    def other(self, request, params):
        return Data(b'other router', b'text/plain')



def renderRoute(resource, segments):
    """
    Locate and render a child resource.

    @type  resource: `IResource`
    @param resource: Resource to locate the child resource on.

    @type  segments: `list` of `bytes`
    @param segments: Path segments.

    @return: Request.
    """
    request = InMemoryRequest(segments)
    child = getChildForRequest(resource, request)
    request.render(child)
    return request



class RouterTests(TestCase):
    """
    Tests for `txspinneret.resource.Router`.
    """
    def test_descriptorRouter(self):
        """
        `Router.__get__` returns the `Router` instance when accessed via
        a type.
        """
        _router = Router()
        class _Descriptor(object):
            router = _router

        self.assertThat(
            _Descriptor.router,
            Is(_router))


    def test_descriptorObject(self):
        """
        `Router.__get__` returns the instance of the object it's an attribute
        of when accessed via an instance.
        """
        thing = _RoutedThing()
        self.assertThat(
            thing.router._self,
            Is(thing))


    def test_nullRoute(self):
        """
        Match the null route.
        """
        resource = _RoutedThing().router.resource()
        self.assertThat(
            renderRoute(resource, []).written,
            Equals([b'null route']))


    def test_nullRouteNoMatch(self):
        """
        If there is no route that can match the request path return 404 Not
        Found.
        """
        resource = _SubroutedThing().router.resource()
        request = renderRoute(resource, [])
        self.assertThat(
            request.responseCode,
            Equals(http.NOT_FOUND))
        self.assertThat(
            request.written,
            Not(Equals([b'null route'])))


    def test_route(self):
        """
        Perform exact route matching using the `Router.route` decorator.
        """
        resource = _RoutedThing().router.resource()
        self.assertThat(
            renderRoute(resource, [b'foo']).written,
            Equals([b'hello world']))


    def test_routeNoMatch(self):
        """
        If there is no route that can match the request path return 404 Not
        Found.
        """
        resource = _RoutedThing().router.resource()
        request = renderRoute(resource, [b'not_a_thing'])
        self.assertThat(
            request.responseCode,
            Equals(http.NOT_FOUND))
        self.assertThat(
            request.written,
            Not(Equals([b'hello world'])))


    def test_subroute(self):
        """
        Perform partial route matching using the `Router.subroute` decorator.
        """
        resource = _SubroutedThing().router.resource()
        self.assertThat(
            renderRoute(resource, [b'bar', b'foo']).written,
            Equals([b'hello world']))


    def test_multipleRoutes(self):
        """
        It is possible to have multiple routes handled by the same route
        handler just by stacking the decorators.
        """
        resource = _RoutedThing().router.resource()
        self.assertThat(
            renderRoute(resource, [b'foo2']).written,
            Equals([b'hello world']))



class RoutedResourceTests(TestCase):
    """
    Tests for `txspinneret.resource.routedResource`.
    """
    def test_defaultRouterAttribute(self):
        """
        ``routerAttribute`` defaults to ``'router'``.
        """
        resource = routedResource(_SubroutedThing)()
        self.assertThat(
            renderRoute(resource, [b'bar', b'foo']).written,
            Equals([b'hello world']))
        self.assertThat(
            renderRoute(resource, [b'other']).responseCode,
            Equals(http.NOT_FOUND))


    def test_customRouterAttribute(self):
        """
        A custom ``routerAttribute``.
        """
        resource = routedResource(_SubroutedThing, 'otherRouter')()
        self.assertThat(
            renderRoute(resource, [b'other']).written,
            Equals([b'other router']))
        self.assertThat(
            renderRoute(resource, [b'bar', b'foo']).responseCode,
            Equals(http.NOT_FOUND))
