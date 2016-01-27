from testtools.matchers import (
    AfterPreprocessing, Raises, MatchesAll, IsInstance)
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
        self.responseHeaders = Headers()


    def setHeader(self, name, value):
        # This was changed in 16.0.0 (or what will be Twisted 16.0.0) while
        # `outgoingHeaders` was entirely deleted.
        self.responseHeaders.addRawHeader(name, value)


    def redirect(self, url):
        self.setResponseCode(http.FOUND)
        self.setHeader(b'location', url)


def MatchesException(exc_type, matcher):
    """
    Match an exception type and a user-provided matcher against the exception
    instance.
    """
    return Raises(
        AfterPreprocessing(
            lambda x: x[1],
            MatchesAll(IsInstance(exc_type), matcher)))
