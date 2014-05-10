from twisted.web import http
from twisted.web.http_headers import Headers
from twisted.web.test.requesthelper import DummyRequest



class InMemoryRequest(DummyRequest):
    """
    In-memory `IRequest`.
    """
    def __init__(self, *a, **kw):
        DummyRequest.__init__(self, *a, **kw)
        # This was only added to `DummyRequest` in Twisted 14.0.0, so we'll do
        # this so our tests pass on older versions of Twisted.
        self.requestHeaders = Headers()


    def redirect(self, url):
        self.setResponseCode(http.FOUND)
        self.setHeader(b'location', url)
