from functools import partial
from testtools import TestCase
from testtools.matchers import Contains, Equals, Is, ContainsDict, raises, Not
from twisted.internet.defer import Deferred
from twisted.python.urlpath import URLPath
from twisted.web import http
from twisted.web.resource import getChildForRequest, Resource
from twisted.web.server import NOT_DONE_YET
from twisted.web.static import Data
from twisted.web.template import Element, TagLoader, tags
from twisted.web.test.requesthelper import DummyRequest

from spinneret.resource import ContentTypeNegotiator, Router, SpinneretResource


from twisted.python.failure import Failure
from testtools.matchers import Mismatch



class InMemoryRequest(DummyRequest):
    """
    """
    def redirect(self, url):
        self.setResponseCode(http.FOUND)
        self.setHeader(b'location', url)



class NoResult(object):
    """
    Match if a Deferred has not fired yet.
    """
    def __str__(self):
        return 'NoResult()'


    def match(self, matchee):
        result = []
        def cb(res):
            result.append(res)
            return res
        matchee.addBoth(cb)
        if result:
            return Mismatch(
                'No result expected on %r, found result instead: %r' % (
                    matchee, result))
        return None



class SuccessResultOf(object):
    """
    Match if a Deferred has fired with a result.
    """
    def __init__(self, resultMatcher=None):
        self.resultMatcher = resultMatcher


    def __str__(self):
        return 'SuccessResultOf(%s)' % (self.resultMatcher or '')


    def match(self, matchee):
        result = []
        matchee.addBoth(result.append)
        if not result:
            return Mismatch(
                'Success result expected on %r, found no result instead' % (
                    matchee,))
        elif isinstance(result[0], Failure):
            return Mismatch(
                'Success result expected on %r,'
                ' found failure result instead:\n%s' % (
                    matchee, result[0].getTraceback()))
        elif self.resultMatcher:
            return self.resultMatcher.match(result[0])
        return None



class SpinneretResourceTests(TestCase):
    """
    Tests for L{spinneret.resource.SpinneretResource}.
    """
    def test_renderDeferred(self):
        """
        """
        class _RenderDeferred(SpinneretResource):
            def render_GET(zelf, request):
                return d

        d = Deferred()
        resource = _RenderDeferred()
        request = InMemoryRequest([])
        request.method = b'GET'
        self.assertThat(
            resource.render(request),
            Is(NOT_DONE_YET))
        self.assertThat(request.written, Equals([]))
        d.callback(b'hello')
        self.assertThat(request.written, Equals([b'hello']))


    def test_locateChildSetPostpath(self):
        """
        The second elements in I{locateChild}'s return value is the new request
        postpath.
        """
        class _TestResource(SpinneretResource):
            def locateChild(zelf, request, segments):
                return None, [b'quux']

        resource = _TestResource()
        request = InMemoryRequest([b'foo', b'bar'])
        self.assertThat(
            request.postpath,
            Equals([b'foo', b'bar']))
        getChildForRequest(resource, request)
        self.assertThat(
            request.postpath,
            Equals([b'quux']))


    def test_locateChildDefault(self):
        """
        I{locateChild} returns 404 Not Found by default.
        """
        resource = SpinneretResource()
        request = InMemoryRequest([''])
        result = getChildForRequest(resource, request)
        request.render(result)
        self.assertThat(
            b''.join(request.written),
            Contains(b'404 - No Such Resource'))
        self.assertThat(
            http.NOT_FOUND,
            Equals(request.responseCode))


    def test_locateChildNotFound(self):
        """
        If I{locateChild} returns C{None} the result is a resource for 404 Not
        Found.
        """
        class _TestResource(SpinneretResource):
            def locateChild(zelf, request, segments):
                return None, segments

        resource = _TestResource()
        request = InMemoryRequest([''])
        result = getChildForRequest(resource, request)
        request.render(result)
        self.assertThat(
            b''.join(request.written),
            Contains(b'404 - No Such Resource'))
        self.assertThat(
            http.NOT_FOUND,
            Equals(request.responseCode))


    def test_locateChildRenderable(self):
        """
        If I{locateChild} returns something adaptable to L{IRenderable} it is
        rendered.
        """
        class _TestElement(Element):
            loader = TagLoader(tags.span(u'Hello ', tags.em(u'World')))

        class _TestResource(SpinneretResource):
            def locateChild(zelf, request, segments):
                return _TestElement(), segments

        resource = _TestResource()
        request = InMemoryRequest([''])
        result = getChildForRequest(resource, request)
        request.render(result)
        self.assertThat(
            b''.join(request.written),
            Equals(b'<!DOCTYPE html>\n<span>Hello <em>World</em></span>'))
        self.assertThat(
            http.OK,
            Equals(request.responseCode))


    def test_locateChildResource(self):
        """
        If I{locateChild} returns something adaptable to L{IResource} it is
        returned.
        """
        class _ResultingResource(Resource):
            isLeaf = True
            def render(zelf, request):
                request.setResponseCode(http.OK)
                return b'hello world'

        class _TestResource(SpinneretResource):
            def locateChild(zelf, request, segments):
                return _ResultingResource(), segments

        resource = _TestResource()
        request = InMemoryRequest([''])
        result = getChildForRequest(resource, request)
        request.render(result)
        self.assertThat(
            b''.join(request.written),
            Equals(b'hello world'))
        self.assertThat(
            http.OK,
            Equals(request.responseCode))


    def test_locateChildRedirect(self):
        """
        If I{locateChild} returns a L{URLPath} instance a redirect is made.
        """
        class _TestResource(SpinneretResource):
            def locateChild(zelf, request, segments):
                return URLPath.fromString(b'http://quux.com/bar'), segments

        resource = _TestResource()
        request = InMemoryRequest([''])
        result = getChildForRequest(resource, request)
        request.render(result)
        self.assertThat(
            request.outgoingHeaders,
            ContainsDict(
                {b'location': Equals(b'http://quux.com/bar')}))
        self.assertThat(
            http.FOUND,
            Equals(request.responseCode))



class _FooJSON(Resource):
    """
    Resource for handling C{application/json} requests.
    """
    contentType = b'application/json'
    acceptTypes = [contentType]

    def render_GET(zelf, request):
        request.setResponseCode(http.OK)
        return b'hello world'



class ContentTypeNegotiatorTests(TestCase):
    """
    Tests for L{spinneret.resource.ContentTypeNegotiator}.
    """
    def test_duplicateHandlers(self):
        """
        Only one handler for an accept type may be specified.
        """
        class _BarJSON(object):
            acceptTypes = [b'application/json']

        self.assertThat(
            partial(ContentTypeNegotiator, [_FooJSON, _FooJSON]),
            raises(ValueError))
        self.assertThat(
            partial(ContentTypeNegotiator, [_FooJSON, _BarJSON]),
            raises(ValueError))


    def test_unacceptable(self):
        """
        If no handler could be negotiated then return an empty resource with
        406 Not Acceptable.
        """
        resource = ContentTypeNegotiator([_FooJSON])
        request = InMemoryRequest([])
        request.requestHeaders.setRawHeaders(b'accept', [b'text/plain'])
        request.render(resource)
        self.assertThat(
            b''.join(request.written),
            Equals(b''))
        self.assertThat(
            http.NOT_ACCEPTABLE,
            Equals(request.responseCode))


    def test_fallback(self):
        """
        If no handler could be negotiated but C{fallback} was C{True} then use
        the first specified handler.
        """
        class _BarXML(object):
            acceptTypes = [b'applicaton/xml']

        resource = ContentTypeNegotiator([_FooJSON, _BarXML], fallback=True)
        request = InMemoryRequest([])
        request.requestHeaders.setRawHeaders(b'accept', [b'text/plain'])
        request.render(resource)
        self.assertThat(
            b''.join(request.written),
            Equals(b'hello world'))
        self.assertThat(
            request.outgoingHeaders,
            ContainsDict(
                {b'content-type': Equals(b'application/json')}))
        self.assertThat(
            http.OK,
            Equals(request.responseCode))


    def test_negotiate(self):
        """
        Negotiate a handler resource based on the I{Accept} header.
        """
        resource = ContentTypeNegotiator([_FooJSON])
        request = InMemoryRequest([])
        request.requestHeaders.setRawHeaders(b'accept', [b'application/json'])
        request.render(resource)
        self.assertThat(
            b''.join(request.written),
            Equals(b'hello world'))
        self.assertThat(
            request.outgoingHeaders,
            ContainsDict(
                {b'content-type': Equals(b'application/json')}))
        self.assertThat(
            http.OK,
            Equals(request.responseCode))



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

    @router.subroute(b'bar')
    def bar(self, request, params):
        return _RoutedThing().router



def renderRoute(resource, segments):
    """
    Locate and render a child resource.

    @type  resource: L{IResource}
    @param resource: Resource to locate the child resource on.

    @type  segments: L{list} of L{bytes}
    @param segments: Path segments.

    @return: Request.
    """
    request = InMemoryRequest(segments)
    child = getChildForRequest(resource, request)
    request.render(child)
    return request



class RouterTests(TestCase):
    """
    Tests for L{spinneret.resource.Router}.
    """
    def test_nullRoute(self):
        """
        Match the null route.
        """
        resource = _RoutedThing().router
        self.assertThat(
            renderRoute(resource, []).written,
            Equals([b'null route']))


    def test_nullRouteNoMatch(self):
        """
        If there is no route that can match the request path return 404 Not
        Found.
        """
        resource = _SubroutedThing().router
        request = renderRoute(resource, [])
        self.assertThat(
            request.responseCode,
            Equals(http.NOT_FOUND))
        self.assertThat(
            request.written,
            Not(Equals([b'null route'])))


    def test_route(self):
        """
        Perform exact route matching using the L{Router.route} decorator.
        """
        resource = _RoutedThing().router
        self.assertThat(
            renderRoute(resource, [b'foo']).written,
            Equals([b'hello world']))


    def test_routeNoMatch(self):
        """
        If there is no route that can match the request path return 404 Not
        Found.
        """
        resource = _RoutedThing().router
        request = renderRoute(resource, [b'not_a_thing'])
        self.assertThat(
            request.responseCode,
            Equals(http.NOT_FOUND))
        self.assertThat(
            request.written,
            Not(Equals([b'hello world'])))


    def test_subroute(self):
        """
        Perform partial route matching using the L{Router.subroute} decorator.
        """
        resource = _SubroutedThing().router
        self.assertThat(
            renderRoute(resource, [b'bar', b'foo']).written,
            Equals([b'hello world']))


    def test_multipleRoutes(self):
        """
        It is possible to have multiple routes handled by the same route
        handler just by stacking the decorators.
        """
        resource = _RoutedThing().router
        self.assertThat(
            renderRoute(resource, [b'foo2']).written,
            Equals([b'hello world']))
