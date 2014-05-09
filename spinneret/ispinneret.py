from twisted.web.resource import IResource
from zope.interface import Attribute



class INegotiableResource(IResource):
    """
    Resource used for content negotiation.
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
