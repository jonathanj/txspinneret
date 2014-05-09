"""
A collection of higher-level Twisted Web resources, suitable for use with any
existing ``IResource`` implementations.

`SpinneretResource` supports child location that results in an `IResource`,
`IRenderable` or `URLPath` (to indicate a redirect), or a `Deferred` resulting
in any of the previously mentioned values.

`ContentTypeNegotiator` will negotiate a resource based on the ``Accept``
header.
"""
from twisted.internet.defer import Deferred, maybeDeferred, succeed
from twisted.web import http
from twisted.web.iweb import IRenderable
from twisted.web.resource import IResource, NoResource, Resource
from twisted.web.server import NOT_DONE_YET
from twisted.web.template import renderElement
from twisted.web.util import DeferredResource, Redirect
from twisted.python.urlpath import URLPath

from txspinneret.util import _parseAccept



class NotAcceptable(Resource):
    """
    Leaf resource that renders an empty body for ``406 Not Acceptable``.
    """
    isLeaf = True

    def render(self, request):
        request.setResponseCode(http.NOT_ACCEPTABLE)
        return b''



class NotFound(NoResource):
    """
    Leaf resource that renders a page for ``404 Not Found``.
    """
    def __init__(self):
        NoResource.__init__(self, b'Resource not found')



class _RenderableResource(Resource):
    """
    `IResource` implementation for `IRendable`s.
    """
    isLeaf = True

    def __init__(self, renderable, doctype=b'<!DOCTYPE html>'):
        Resource.__init__(self)
        self._renderable = renderable
        self._doctype = doctype


    def render_GET(self, request):
        request.setResponseCode(http.OK)
        return renderElement(request, self._renderable, self._doctype)



class SpinneretResource(Resource, object):
    """
    Web resource convenience base class.

    Child resource location is done by `SpinneretResource.locateChild`, which
    gives a slightly higher level interface than
    `IResource.getChildWithDefault
    <twisted:twisted.web.resource.IResource.getChildWithDefault>`.
    """
    def _adaptToResource(self, result):
        """
        Adapt a result to `IResource`.

        Several adaptions are tried they are, in order: ``None``,
        `IRenderable <twisted:twisted.web.iweb.IRenderable>`, `IResource
        <twisted:twisted.web.resource.IResource>`, and `URLPath
        <twisted:twisted.python.urlpath.URLPath>`. Anything else is returned as
        is.

        A `URLPath <twisted:twisted.python.urlpath.URLPath>` is treated as
        a redirect.
        """
        if result is None:
            return NotFound()

        renderable = IRenderable(result, None)
        if renderable is not None:
            return _RenderableResource(renderable)

        resource = IResource(result, None)
        if resource is not None:
            return resource

        if isinstance(result, URLPath):
            return Redirect(str(result))

        return result


    def getChildWithDefault(self, path, request):
        def _setSegments((result, segments)):
            request.postpath[:] = segments
            return result

        segments = request.prepath[-1:] + request.postpath
        d = maybeDeferred(self.locateChild, request, segments)
        d.addCallback(_setSegments)
        d.addCallback(self._adaptToResource)
        return DeferredResource(d)


    def _handleRenderResult(self, request, result):
        """
        Handle the result from `IResource.render`.

        If the result is a `Deferred` then return `NOT_DONE_YET` and add
        a callback to write the result to the request when it arrives.
        """
        def _requestFinished(result, cancel):
            cancel()
            return result

        if not isinstance(result, Deferred):
            result = succeed(result)

        def _whenDone(result):
            render = getattr(result, 'render', lambda request: result)
            renderResult = render(request)
            if renderResult != NOT_DONE_YET:
                request.write(renderResult)
                request.finish()
            return result
        request.notifyFinish().addBoth(_requestFinished, result.cancel)
        result.addCallback(self._adaptToResource)
        result.addCallback(_whenDone)
        result.addErrback(request.processingFailed)
        return NOT_DONE_YET


    def render(self, request):
        return self._handleRenderResult(
            request,
            super(SpinneretResource, self).render(request))


    def locateChild(self, request, segments):
        """
        Locate another object which can be adapted to `IResource`.

        :type  request: `IRequest`
        :param request: Request.

        :type  segments: ``sequence`` of `bytes`
        :param segments: Sequence of strings giving the remaining query
            segments to resolve.

        :rtype: 2-`tuple` of `IResource`, `IRendable` or `URLPath` and
            a ``sequence`` of `bytes`
        :return: Pair of an `IResource`, `IRendable` or `URLPath` and
            a sequence of the remaining path segments to be process, or
            a `Deferred` containing the aforementioned result.
        """
        return NotFound(), []



class ContentTypeNegotiator(Resource):
    """
    Negotiate an appropriate representation based on the ``Accept`` header.

    Rendering this resource will negotiate a representation and render the
    matching handler.
    """
    def __init__(self, handlers, fallback=False):
        """
        :type  handlers: ``iterable`` of `INegotiableResource
            <txspinneret.interfaces.INegotiableResource>`
        :param handlers: Iterable of resources to use as handlers for
            negotiation.

        :type  fallback: `bool`
        :param fallback: Fall back to the first handler in the case where
            negotiation fails?
        """
        Resource.__init__(self)
        self._handlers = list(handlers)
        self._fallback = fallback
        self._acceptHandlers = {}
        for handler in self._handlers:
            for acceptType in handler.acceptTypes:
                if acceptType in self._acceptHandlers:
                    raise ValueError(
                        'Duplicate handler for %r' % (acceptType,))
                self._acceptHandlers[acceptType] = handler


    def _negotiateHandler(self, request):
        """
        Negotiate a handler based on the content types acceptable to the
        client.

        :rtype: 2-`tuple` of `twisted.web.iweb.IResource` and `bytes`
        :return: Pair of a resource and the content type.
        """
        accept = _parseAccept(request.requestHeaders.getRawHeaders('Accept'))
        for contentType in accept.keys():
            handler = self._acceptHandlers.get(contentType.lower())
            if handler is not None:
                return handler, handler.contentType

        if self._fallback:
            handler = self._handlers[0]
            return handler, handler.contentType
        return NotAcceptable(), None


    def render(self, request):
        handler, contentType = self._negotiateHandler(request)
        if contentType is not None:
            request.setHeader(b'Content-Type', contentType)
        return handler.render(request)



__all__ = [
    'SpinneretResource', 'ContentTypeNegotiator', 'NotAcceptable', 'NotFound']
