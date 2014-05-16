from functools import partial
from testtools import TestCase
from testtools.matchers import (
    Contains, Equals, ContainsDict, raises, MatchesStructure, MatchesSetwise)
from twisted.internet.defer import Deferred
from twisted.python.urlpath import URLPath
from twisted.web import http
from twisted.web.error import UnsupportedMethod
from twisted.web.resource import getChildForRequest, Resource
from twisted.web.template import Element, TagLoader, tags
from zope.interface import implementer

from txspinneret.interfaces import INegotiableResource, ISpinneretResource
from txspinneret.resource import (
    ContentTypeNegotiator, SpinneretResource, _renderResource)
from txspinneret.util import identity
from txspinneret.test.util import InMemoryRequest, MatchesException



class RenderResourceTests(TestCase):
    """
    Tests for `txspinneret.resource._renderResource`.
    """
    def test_existingRenderer(self):
        """
        Call the renderer defined that matches the request method.
        """
        called = []
        resource = Resource()
        request = InMemoryRequest([])
        request.method = b'PUT'
        resource.render_PUT = called.append
        _renderResource(resource, request)
        self.assertThat(
            called,
            Equals([request]))


    def test_hasAllowedMethods(self):
        """
        Raise `UnsupportedErrors`, with the value of
        ``resource.allowedMethods``, if there are no matching renderers.
        """
        resource = Resource()
        request = InMemoryRequest([])
        request.method = b'PUT'
        resource.allowedMethods = [b'GET', b'HEAD']
        self.assertThat(
            partial(_renderResource, resource, request),
            MatchesException(
                UnsupportedMethod,
                MatchesStructure(
                    allowedMethods=MatchesSetwise(Equals('GET'),
                                                  Equals('HEAD')))))


    def test_computeAllowedMethods(self):
        """
        Raise `UnsupportedErrors`, computing the allowed methods, if there are
        no matching renderers.
        """
        class _Resource(object):
            render_GET = identity
            render_HEAD = identity
        resource = _Resource()
        request = InMemoryRequest([])
        request.method = b'PUT'
        self.assertThat(
            partial(_renderResource, resource, request),
            MatchesException(
                UnsupportedMethod,
                MatchesStructure(
                    allowedMethods=MatchesSetwise(Equals('GET'),
                                                  Equals('HEAD')))))



class SpinneretResourceTests(TestCase):
    """
    Tests for `txspinneret.resource.SpinneretResource`.
    """
    def test_renderDeferred(self):
        """
        It is possible to return a `Deferred` from a render method.
        """
        @implementer(ISpinneretResource)
        class _RenderDeferred(object):
            def render_GET(zelf, request):
                return d

        d = Deferred()
        resource = SpinneretResource(_RenderDeferred())
        request = InMemoryRequest([])
        request.method = b'GET'
        request.render(resource)
        self.assertThat(request.written, Equals([]))
        d.callback(b'hello')
        self.assertThat(request.written, Equals([b'hello']))


    def test_locateChildSetPostpath(self):
        """
        The second elements in ``locateChild`` return value is the new request
        postpath.
        """
        @implementer(ISpinneretResource)
        class _TestResource(object):
            def locateChild(zelf, request, segments):
                return None, [b'quux']

        resource = SpinneretResource(_TestResource())
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
        ``locateChild`` returns 404 Not Found by default.
        """
        resource = SpinneretResource(Resource())
        request = InMemoryRequest([''])
        result = getChildForRequest(resource, request)
        request.render(result)
        self.assertThat(
            b''.join(request.written),
            Contains(b'404 - No Such Resource'))
        self.assertThat(
            http.NOT_FOUND,
            Equals(request.responseCode))
        self.assertThat(
            request.postpath,
            Equals([]))


    def test_locateChildNotFound(self):
        """
        If ``locateChild`` returns ``None`` the result is a resource for 404 Not
        Found.
        """
        @implementer(ISpinneretResource)
        class _TestResource(object):
            def locateChild(zelf, request, segments):
                return None, segments

        resource = SpinneretResource(_TestResource())
        request = InMemoryRequest([''])
        result = getChildForRequest(resource, request)
        request.render(result)
        self.assertThat(
            b''.join(request.written),
            Contains(b'404 - No Such Resource'))
        self.assertThat(
            http.NOT_FOUND,
            Equals(request.responseCode))
        self.assertThat(
            request.postpath,
            Equals([]))


    def test_locateChildRenderable(self):
        """
        If ``locateChild`` returns something adaptable to `IRenderable` it is
        rendered.
        """
        class _TestElement(Element):
            loader = TagLoader(tags.span(u'Hello ', tags.em(u'World')))

        @implementer(ISpinneretResource)
        class _TestResource(object):
            def locateChild(zelf, request, segments):
                return _TestElement(), []

        resource = SpinneretResource(_TestResource())
        request = InMemoryRequest([''])
        result = getChildForRequest(resource, request)
        request.render(result)
        self.assertThat(
            b''.join(request.written),
            Equals(b'<!DOCTYPE html>\n<span>Hello <em>World</em></span>'))
        self.assertThat(
            http.OK,
            Equals(request.responseCode))
        self.assertThat(
            request.postpath,
            Equals([]))


    def test_locateChildResource(self):
        """
        If ``locateChild`` returns something adaptable to `IResource` it is
        returned.
        """
        class _ResultingResource(Resource):
            isLeaf = True
            def render(zelf, request):
                request.setResponseCode(http.OK)
                return b'hello world'

        @implementer(ISpinneretResource)
        class _TestResource(object):
            def locateChild(zelf, request, segments):
                return _ResultingResource(), []

        resource = SpinneretResource(_TestResource())
        request = InMemoryRequest([''])
        result = getChildForRequest(resource, request)
        request.render(result)
        self.assertThat(
            b''.join(request.written),
            Equals(b'hello world'))
        self.assertThat(
            http.OK,
            Equals(request.responseCode))
        self.assertThat(
            request.postpath,
            Equals([]))


    def test_locateChildSpinneretResource(self):
        """
        If ``locateChild`` returns something adaptable to `ISpinneretResource`
        it is adapted to an `IResource`.
        """
        @implementer(ISpinneretResource)
        class _ResultingResource(object):
            def render_GET(zelf, request):
                request.setResponseCode(http.OK)
                return b'hello world'

        @implementer(ISpinneretResource)
        class _TestResource(object):
            def locateChild(zelf, request, segments):
                return _ResultingResource(), []

        resource = SpinneretResource(_TestResource())
        request = InMemoryRequest([''])
        request.method = b'GET'
        result = getChildForRequest(resource, request)
        request.render(result)
        self.assertThat(
            b''.join(request.written),
            Equals(b'hello world'))
        self.assertThat(
            http.OK,
            Equals(request.responseCode))
        self.assertThat(
            request.postpath,
            Equals([]))


    def test_locateChildRedirect(self):
        """
        If ``locateChild`` returns a `URLPath` instance a redirect is made.
        """
        @implementer(ISpinneretResource)
        class _TestResource(object):
            def locateChild(zelf, request, segments):
                return URLPath.fromString(b'http://quux.com/bar'), []

        resource = SpinneretResource(_TestResource())
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
        self.assertThat(
            request.postpath,
            Equals([]))



@implementer(INegotiableResource)
class _FooJSON(Resource):
    """
    Resource for handling ``application/json`` requests.
    """
    contentType = b'application/json'
    acceptTypes = [contentType]

    def render_GET(zelf, request):
        request.setResponseCode(http.OK)
        return b'hello world'



@implementer(INegotiableResource, ISpinneretResource)
class _FooSpinneretJSON(object):
    """
    Spinneret resource for handling ``application/json`` requests.
    """
    contentType = b'application/json'
    acceptTypes = [contentType]

    def render_GET(zelf, request):
        request.setResponseCode(http.OK)
        return b'hello world'



class ContentTypeNegotiatorTests(TestCase):
    """
    Tests for `txspinneret.resource.ContentTypeNegotiator`.
    """
    def test_duplicateHandlers(self):
        """
        Only one handler for an accept type may be specified.
        """
        @implementer(INegotiableResource)
        class _BarJSON(object):
            contentType = b'application/json'
            acceptTypes = [b'application/json']

        self.assertThat(
            partial(ContentTypeNegotiator, [_FooJSON(), _FooJSON()]),
            raises(ValueError))
        self.assertThat(
            partial(ContentTypeNegotiator, [_FooJSON(), _BarJSON()]),
            raises(ValueError))


    def test_unacceptable(self):
        """
        If no handler could be negotiated then return an empty resource with
        406 Not Acceptable.
        """
        resource = ContentTypeNegotiator([_FooJSON()])
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
        If no handler could be negotiated but ``fallback`` was ``True`` then
        use the first specified handler.
        """
        @implementer(INegotiableResource)
        class _BarXML(object):
            contentType = b'application/xml'
            acceptTypes = [b'applicaton/xml']

        resource = ContentTypeNegotiator(
            [_FooJSON(), _BarXML()], fallback=True)
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


    def test_negotiateResource(self):
        """
        Negotiate a handler resource based on the ``Accept`` header.
        """
        resource = ContentTypeNegotiator([_FooJSON()])
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


    def test_negotiateSpinneretResource(self):
        """
        Negotiate a Spinneret handler resource based on the ``Accept`` header.
        """
        resource = ContentTypeNegotiator([_FooSpinneretJSON()])
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
