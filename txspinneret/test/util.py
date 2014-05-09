from twisted.web import http
from twisted.web.test.requesthelper import DummyRequest



class InMemoryRequest(DummyRequest):
    """
    In-memory `IRequest`.
    """
    def redirect(self, url):
        self.setResponseCode(http.FOUND)
        self.setHeader(b'location', url)
