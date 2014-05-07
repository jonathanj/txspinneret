from collections import OrderedDict
from testtools import TestCase
from testtools.matchers import Equals
from twisted.web.http_headers import Headers

from spinneret.route import route, subroute, Integer, Text



class MockRequest(object):
    """
    A mock L{twisted.web.iweb.IRequest}.
    """
    def __init__(self, requestHeaders=None):
        if requestHeaders is None:
            requestHeaders = Headers()
        self.requestHeaders = requestHeaders



class TextParameterTests(TestCase):
    """
    Tests for L{spinneret.route.Text}.
    """
    def test_parseBytes(self):
        """
        Parse bytes and use the default encoding of I{UTF-8}.
        """
        request = MockRequest()
        match = Text(b'foo')
        self.assertThat(
            match(request, b'42'),
            Equals((b'foo', u'42')))
        self.assertThat(
            match(request, b'\xe2\x98\x83'),
            Equals((b'foo', u'\N{SNOWMAN}')))


    def test_parseUnicode(self):
        """
        Parse a Unicode value.
        """
        request = MockRequest()
        match = Text(b'foo')
        self.assertThat(
            match(request, u'42'),
            Equals((b'foo', u'42')))
        self.assertThat(
            match(request, u'\N{SNOWMAN}'),
            Equals((b'foo', u'\N{SNOWMAN}')))


    def test_defaultEncoding(self):
        """
        Parsing bytes uses the specified default encoding.
        """
        request = MockRequest()
        match = Text(b'foo', encoding=b'utf-32')
        self.assertThat(
            match(request, u'42'),
            Equals((b'foo', u'42')))
        self.assertThat(
            match(request, b'\xff\xfe\x00\x00\x03&\x00\x00'),
            Equals((b'foo', u'\N{SNOWMAN}')))


    def test_encodingHeader(self):
        """
        When the I{Content-Type} header is present and has a I{charset}
        parameter, use that instead of the default encoding.
        """
        request = MockRequest(
            requestHeaders=Headers(
                {b'Content-Type': [b'text/plain;charset=utf-16']}))
        match = Text(b'foo', encoding=b'utf-32')
        self.assertThat(
            match(request, u'42'),
            Equals((b'foo', u'42')))
        self.assertThat(
            match(request, b'\xff\xfe\x03&'),
            Equals((b'foo', u'\N{SNOWMAN}')))



class IntegerParameterTests(TestCase):
    """
    Tests for L{spinneret.route.Integer}.
    """
    def test_match(self):
        """
        Text values are parsed as integers.
        """
        request = MockRequest()
        match = Integer(b'foo')
        self.assertThat(
            match(request, b'42'),
            Equals((b'foo', 42)))


    def test_unparseable(self):
        """
        L{None} is returned if the value is not a valid integer.
        """
        request = MockRequest()
        match = Integer(b'foo')
        self.assertThat(
            match(request, u'arst'),
            Equals((b'foo', None)))



class StaticRouteTests(TestCase):
    """
    Tests for L{spinneret.route.route} using only static path components.
    """
    def test_nullRoute(self):
        """
        The null route matches only zero segments.
        """
        request = MockRequest()
        self.assertThat(
            route()(request, []),
            Equals((OrderedDict(), [])))
        self.assertThat(
            route()(request, ['foo']),
            Equals((None, ['foo'])))


    def test_single(self):
        """
        Match a route with a single component.
        """
        request = MockRequest()
        self.assertThat(
            route('foo')(request, ['foo']),
            Equals((OrderedDict(), [])))


    def test_singleNoMatch(self):
        """
        Do not match a route with a single component.
        """
        request = MockRequest()
        self.assertThat(
            route('foo')(request, ['bar']),
            Equals((None, ['bar'])))


    def test_multiple(self):
        """
        Match a route with a multiple components.
        """
        request = MockRequest()
        self.assertThat(
            route('foo', 'bar')(request, ['foo', 'bar']),
            Equals((OrderedDict(), [])))


    def test_multipleNoMatch(self):
        """
        Do not match a route with a multiple components.
        """
        request = MockRequest()
        self.assertThat(
            route('bar')(request, ['foo', 'bar']),
            Equals((None, ['foo', 'bar'])))
        self.assertThat(
            route('foo', 'quux')(request, ['foo', 'bar']),
            Equals((None, ['foo', 'bar']))),


    def test_tooMany(self):
        """
        Do not match a route that has too many components or segments.
        """
        request = MockRequest()
        self.assertThat(
            route('foo', 'bar')(request, ['foo']),
            Equals((None, ['foo'])))
        request = MockRequest()
        self.assertThat(
            route('foo')(request, ['foo', 'bar']),
            Equals((None, ['foo', 'bar'])))


    def test_multipleSubroute(self):
        """
        Match a sub-route, returning the unmatched segments.
        """
        request = MockRequest()
        self.assertThat(
            subroute('foo')(request, ['foo', 'bar']),
            Equals((OrderedDict(), ['bar'])))


    def test_emptyPlainBytes(self):
        """
        Match a route against the root specified as a single plain string.
        """
        request = MockRequest()
        self.assertThat(
            subroute('/')(request, ['']),
            Equals((OrderedDict(), [])))


    def test_singlePlainBytes(self):
        """
        Match a route with a single component specified as a single plain
        string.
        """
        request = MockRequest()
        self.assertThat(
            subroute('/foo')(request, ['foo']),
            Equals((OrderedDict(), [])))


    def test_multiplePlainBytes(self):
        """
        Match a route with multiple components specified as a single plain
        string.
        """
        request = MockRequest()
        self.assertThat(
            subroute('/foo/bar')(request, ['foo', 'bar']),
            Equals((OrderedDict(), [])))



class DynamicRouteTests(TestCase):
    """
    Tests for L{spinneret.route.route} using dynamic path components.
    """
    def test_single(self):
        """
        Match a route with a single component.
        """
        request = MockRequest()
        self.assertThat(
            route(Text('name'))(request, ['foo']),
            Equals(
                (OrderedDict([('name', 'foo')]), [])))


    def test_singleNoMatch(self):
        """
        Do not match a route with a single component.
        """
        request = MockRequest()
        self.assertThat(
            route(Integer('name'))(request, ['bar']),
            Equals(
                (None, ['bar'])))


    def test_multiple(self):
        """
        Match a route with a multiple components.
        """
        request = MockRequest()
        self.assertThat(
            route(Text('name'), 'bar')(request, ['foo', 'bar']),
            Equals(
                (OrderedDict([('name', 'foo')]), [])))


    def test_multipleNoMatch(self):
        """
        Do not match a route with a multiple components.
        """
        request = MockRequest()
        self.assertThat(
            route(Text('name'), Integer('name2'))(request, ['foo', 'bar']),
            Equals((None, ['foo', 'bar'])))
        self.assertThat(
            route(Integer('name'), Text('name2'))(request, ['foo', 'bar']),
            Equals((None, ['foo', 'bar']))),


    def test_tooMany(self):
        """
        Do not match a route that has too many components or segments.
        """
        request = MockRequest()
        self.assertThat(
            route(Text('name'), Integer('name2'))(request, ['foo']),
            Equals((None, ['foo'])))
        self.assertThat(
            route(Text('name'))(request, ['foo', 'bar']),
            Equals((None, ['foo', 'bar'])))


    def test_multipleSubroute(self):
        """
        Match a sub-route, returning the unmatched segments.
        """
        request = MockRequest()
        self.assertThat(
            subroute(Text('name'))(request, ['foo', 'bar']),
            Equals(
                (OrderedDict([('name', 'foo')]), ['bar'])))



class MixedRouteTests(TestCase):
    """
    Tests for L{spinneret.route.route} using mixed static and dynamic path
    components.
    """
    def test_multiple(self):
        """
        Match a route with a multiple components.
        """
        request = MockRequest()
        segments = ['foo', 'bar', 'quux']
        self.assertThat(
            route(
                Text('name'), 'bar', 'quux')(request, segments),
            Equals(
                (OrderedDict([('name', 'foo')]), [])))
        self.assertThat(
            route(Text('name'), 'bar', Text('name2'))(request, segments),
            Equals(
                (OrderedDict([('name', 'foo'),
                              ('name2', 'quux')]), [])))


    def test_multipleNoMatch(self):
        """
        Do not match a route with a multiple components.
        """
        request = MockRequest()
        self.assertThat(
            route('foo', Integer('name'))(request, ['foo', 'bar', 'quux']),
            Equals(
                (None, ['foo', 'bar', 'quux'])))


    def test_multipleSubRoute(self):
        """
        Match a sub-route, returning the unmatched segments.
        """
        request = MockRequest()
        self.assertThat(
            subroute('foo', Text('name'))(request, ['foo', 'bar', 'quux']),
            Equals(
                (OrderedDict([('name', 'bar')]), ['quux'])))
