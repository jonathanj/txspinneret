from twisted.web.resource import IResource
from zope.interface import Attribute, Interface



class INegotiableResource(IResource):
    """
    Resource used for content negotiation.
    """
    contentType = Attribute(
        """
        L{bytes} indicating the content type of this resource when rendered.
        """)


    acceptTypes = Attribute(
        """
        L{list} of L{bytes} indicating the content types this resource is
        capable of accepting.
        """)
