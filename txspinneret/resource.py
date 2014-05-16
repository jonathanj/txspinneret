"""
A collection of higher-level Twisted Web resources, suitable for use with any
existing ``IResource`` implementations.

`SpinneretResource` adapts an `ISpinneretResource` to `IResource`.

`ContentTypeNegotiator` will negotiate a resource based on the ``Accept``
header.
"""
from twisted.internet.defer import Deferred, maybeDeferred, succeed
from twisted.python.compat import nativeString
from twisted.python.urlpath import URLPath
from twisted.web import http
from twisted.web.error import UnsupportedMethod
from twisted.web.iweb import IRenderable
from twisted.web.resource import (
    IResource, NoResource, Resource, _computeAllowedMethods)
from twisted.web.server import NOT_DONE_YET
from twisted.web.template import renderElement
from twisted.web.util import DeferredResource, Redirect

from txspinneret.interfaces import ISpinneretResource
from txspinneret.util import _parseAccept



def _renderResource(resource, request):
    """
    Render a given resource.

    See `IResource.render <twisted:twisted.web.resource.IResource.render>`.
    """
    meth = getattr(resource, 'render_' + nativeString(request.method), None)
    if meth is None:
        try:
            allowedMethods = resource.allowedMethods
        except AttributeError:
            allowedMethods = _computeAllowedMethods(resource)
        raise UnsupportedMethod(allowedMethods)
    return meth(request)



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
    Adapter from `IRenderable` to `IResource`.
    """
    isLeaf = True

    def __init__(self, renderable, doctype=b'<!DOCTYPE html>'):
        Resource.__init__(self)
        self._renderable = renderable
        self._doctype = doctype


    def render_GET(self, request):
        request.setResponseCode(http.OK)
        return renderElement(request, self._renderable, self._doctype)



class SpinneretResource(Resource):
    """
    Adapter from `ISpinneretResource` to `IResource`.
    """
    def __init__(self, wrappedResource):
        """
        :type  wrappedResource: `ISpinneretResource`
        :param wrappedResource: Spinneret resource to wrap in an `IResource`.
        """
        self._wrappedResource = wrappedResource
        Resource.__init__(self)


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

        spinneretResource = ISpinneretResource(result, None)
        if spinneretResource is not None:
            return SpinneretResource(spinneretResource)

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
        def _setSegments(result):
            result, segments = result
            request.postpath[:] = segments
            return result

        def _locateChild(request, segments):
            def _defaultLocateChild(request, segments):
                return NotFound(), []
            locateChild = getattr(
                self._wrappedResource, 'locateChild', _defaultLocateChild)
            return locateChild(request, segments)

        d = maybeDeferred(
            _locateChild, request, request.prepath[-1:] + request.postpath)
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
        # This is kind of terrible but we need `_RouterResource.render` to be
        # called to handle the null route. Finding a better way to achieve this
        # would be great.
        if hasattr(self._wrappedResource, 'render'):
            result = self._wrappedResource.render(request)
        else:
            result = _renderResource(self._wrappedResource, request)
        return self._handleRenderResult(request, result)



class ContentTypeNegotiator(Resource):
    """
    Negotiate an appropriate representation based on the ``Accept`` header.

    Rendering this resource will negotiate a representation and render the
    matching handler.
    """
    def __init__(self, handlers, fallback=False):
        """
        :type  handlers: ``iterable`` of `INegotiableResource` and either
            `IResource` or `ISpinneretResource`.
        :param handlers: Iterable of negotiable resources, either
            `ISpinneretResource` or `IResource`, to use as handlers for
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
        resource, contentType = self._negotiateHandler(request)
        if contentType is not None:
            request.setHeader(b'Content-Type', contentType)

        spinneretResource = ISpinneretResource(resource, None)
        if spinneretResource is not None:
            resource = SpinneretResource(spinneretResource)

        return resource.render(request)



__all__ = [
    'SpinneretResource', 'ContentTypeNegotiator', 'NotAcceptable', 'NotFound']
