from functools import partial
from twisted.internet.defer import Deferred, maybeDeferred
from twisted.web import http
from twisted.web.iweb import IRenderable
from twisted.web.resource import IResource, NoResource, Resource
from twisted.web.server import NOT_DONE_YET
from twisted.web.template import renderElement
from twisted.web.util import DeferredResource, Redirect
from twisted.python.urlpath import URLPath

from spinneret.util import _parseAccept
from spinneret.route import route, subroute



class NotAcceptable(Resource):
    """
    No acceptable content type could be negotiated.
    """
    def render(self, request):
        request.setResponseCode(http.NOT_ACCEPTABLE)
        return b''



NotFound = partial(NoResource, b'Resource not found')



class SpinneretResource(Resource, object):
    """
    Web resource convenience base class.

    Child resource location is done by L{SpinneretResource.locateChild}, which
    gives a slightly higher level interface than
    L{IResource.getChildWithDefault}.
    """
    def _adaptToResource(self, result):
        """
        Adapt a result to L{IResource}.

        Several adaptions are tried they are, in order: C{None},
        L{IRenderable}, L{IResource}, and L{URLPath}. Anything else is returned
        as is.

        A L{URLPath} is treated as a redirect.
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
        Handle the result from L{IResource.render}.

        If the result is a L{Deferred} then return L{NOT_DONE_YET} and add
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
        Locate another object which can be adapted to L{IResource}.

        @type  request: L{IRequest}
        @param request: Request.

        @type  segments: I{sequence} of L{bytes}
        @param segments: Sequence of strings giving the remaining query
            segments to resolve.

        @rtype: 2-L{tuple} of L{IResource}, L{IRendable} or L{URLPath} and
            a I{sequence} of L{bytes}
        @return: Pair of an L{IResource}, L{IRendable} or L{URLPath} and
            a sequence of the remaining path segments to be process, or
            a L{Deferred} containing the aforementioned result.
        """
        return NotFound(), []



class _RenderableResource(Resource):
    """
    L{IResource} implementation for L{IRendable}s.
    """
    isLeaf = True


    def __init__(self, renderable, doctype=b'<!DOCTYPE html>'):
        Resource.__init__(self)
        self._renderable = renderable
        self._doctype = doctype


    def render_GET(self, request):
        request.setResponseCode(http.OK)
        return renderElement(request, self._renderable, self._doctype)



class ContentTypeNegotiator(Resource):
    """
    Negotiate an appropriate representation based on the I{Accept} header.

    Rendering this resource will negotiate a representation and render the
    matching handler.

    @ivar _handlers: See L{__init__}.
    @ivar _fallback: See L{__init__}.
    """
    def __init__(self, handlers, fallback=False):
        """
        @type  handlers: I{iterable} of L{INegotiableResource}
        @param handlers: Iterable of resources to use as handlers for
            negotiation.

        @type  fallback: L{bool}
        @param fallback: Fall back to the first handler in the case where
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

        @rtype: 2-L{tuple} of L{twisted.web.iweb.IResource} and L{bytes}
        @return: Pair of a resource and the content type.
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
