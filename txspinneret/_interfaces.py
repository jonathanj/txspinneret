from zope.interface import Attribute, Interface



class ISpinneretResource(Interface):
    """
    Spinneret resource.

    Spinneret resources may additionally have methods like ``render_GET`` (to
    handle a ``GET`` request) ``render_POST`` etc., like `IResource`, that may
    return the same types of objects as `ISpinneretResource.locateChild`.

    Adaptable to `IResource`.
    """
    def locateChild(request, segments):
        """
        Locate another object which can be adapted to `IResource`.

        :type  request: `IRequest <twisted:twisted.web.iweb.IRequest>`
        :param request: Request.

        :type  segments: ``sequence`` of `bytes`
        :param segments: Sequence of strings giving the remaining query
            segments to resolve.

        :rtype: 2-`tuple` of `IResource`, `IRenderable` or `URLPath` and
            a ``sequence`` of `bytes`
        :return: Pair of an `IResource`, `IRenderable` or `URLPath` and
            a sequence of the remaining path segments to be process, or
            a `Deferred` containing the aforementioned result.
        """



class INegotiableResource(Interface):
    """
    Resource used for content negotiation.

    The implementation should be adaptable to `IResource
    <twisted:twisted.web.resource.IResource>`.
    """
    contentType = Attribute(
        """
        `bytes` indicating the content type of this resource when rendered.
        """)


    acceptTypes = Attribute(
        """
        `list` of `bytes` indicating the content types this resource is capable
        of accepting.
        """)
