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

        if isinstance(result, Deferred):
            def _whenDone(result):
                request.write(result)
                request.finish()
                return result
            request.notifyFinish().addBoth(_requestFinished, result.cancel)
            result.addCallback(_whenDone)
            return NOT_DONE_YET
        return result


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
        return NotAcceptable, None


    def render(self, request):
        handler, contentType = self._negotiateHandler(request)
        if contentType is not None:
            request.setHeader(b'Content-Type', contentType)
        return handler().render(request)



class Router(SpinneretResource):
    """
    Resource that provides path-based routing to L{IResource}s.

    L{Router} is designed to be used as a Python descriptor, and route handlers
    decorated with L{Router.route} or L{Router.subroute}, route handlers should
    return L{IResource} or a L{Deferred} that fires with C{IResource}. For
    example::

        from collections import namedtuple
        from spinneret.resource import Router

        class UserRouter(object):
            router = Router()

            def __init__(self, user):
                self.user = user

            @router.route(b'/')
            def name(self, request, params):
                return Data(self.user.name, b'text/plain')

            @router.subroute(b'friend', Text('name'))
            def friend(self, request, params):
                return UserRouter(self.user.friends[params[b'name']]).router


        def start():
            User = namedtuple(b'User', [b'name', b'friends'])
            bob = User(b'bob', {})
            chuck = User(b'chuck', {b'bob': bob})
            default = User(b'default', {b'bob': bob, b'chuck': chuck})
            return UserRouter(default).router


    Putting this in a file called C{user_router.py} and running C{twistd -n web
    --class=user_router.start} will create a resource where accessing C{/}
    displays "default" and accessing C{/friend/chuck/friend/bob/} displays
    "bob".
    """
    def __init__(self):
        self._routes = []


    def _forObject(self, obj):
        """
        Create a new L{Router} instance, with it's own set of routes, for
        C{obj}.
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
        See L{spinneret.route.route}.
        """
        def _factory(f):
            self._addRoute(f, route(*components))
            return f
        return _factory


    def subroute(self, *components):
        """
        See L{spinneret.route.subroute}.
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



__all__ = ['SpinneretResource', 'ContentTypeNegotiator', 'Router',
           'NotAcceptable', 'NotFound']
