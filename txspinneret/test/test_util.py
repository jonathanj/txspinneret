from testtools import TestCase
from testtools.matchers import Equals, Is
from twisted.web.http_headers import Headers

from txspinneret.util import (
    _parseAccept, _splitHeaders, maybe, contentEncoding, identity, FixedOffset)



identityv = lambda *a, **kw: (a, kw)



class ParseAcceptTests(TestCase):
    """
    Tests for `txspinneret.util._parseAccept`.
    """
    def test_single(self):
        """
        A single ``Accept`` value is parsed into its content type with no
        parameters.
        """
        self.assertThat(
            _parseAccept(['text/plain']).items(),
            Equals([('text/plain', {})]))


    def test_multiple(self):
        """
        Multiple ``Accept`` values are split on comma each with no
        parameters.
        """
        self.assertThat(
            _parseAccept(['text/plain', 'text/html,text/csv']).items(),
            Equals([('text/plain', {}),
                    ('text/html', {}),
                    ('text/csv', {})]))


    def test_q(self):
        """
        Content types are sorted in descending order by their ``q`` parameter,
        the absence of a ``q`` parameter indicates a value of ``1.0``.
        """
        self.assertThat(
            _parseAccept(['text/plain;q=0.2',
                          'text/html,text/csv;q=0.4']).items(),
            Equals([('text/html', {}),
                    ('text/csv', {'q': '0.4'}),
                    ('text/plain', {'q': '0.2'})]))



class SplitHeadersTests(TestCase):
    """
    Tests for `txspinneret.util._splitHeaders`.
    """
    def test_single(self):
        """
        Split a single header with no parameters.
        """
        self.assertThat(
            _splitHeaders(['foo']),
            Equals([('foo', {})]))


    def test_multiple(self):
        """
        Split multiple headers with no parameters.
        """
        self.assertThat(
            _splitHeaders(['foo', 'bar']),
            Equals([('foo', {}),
                    ('bar', {})]))


    def test_commas(self):
        """
        Split a single header containing multiple values separated by commas
        with no parameters.
        """
        self.assertThat(
            _splitHeaders(['foo,bar']),
            Equals([('foo', {}),
                    ('bar', {})]))


    def test_multipleWithCommas(self):
        """
        Split multiple headers containing multiple values separated by commas
        with no parameters.
        """
        self.assertThat(
            _splitHeaders(['foo,bar', 'baz']),
            Equals([('foo', {}),
                    ('bar', {}),
                    ('baz', {})]))


    def test_params(self):
        """
        Split header values containing parameters.
        """
        self.assertThat(
            _splitHeaders(['foo,bar;quux=1']),
            Equals([('foo', {}),
                    ('bar', {'quux': '1'})]))



class MaybeTests(TestCase):
    """
    Tests for `txspinneret.util.maybe`.
    """
    def test_none(self):
        """
        If the first parameter to a `maybe`-wrapped function is ``None`` then
        the result of that function is immediately ``None``.
        """
        self.assertThat(
            maybe(identity)(None),
            Is(None))
        self.assertThat(
            maybe(identityv)(None, 1, a=2),
            Is(None))


    def test_notNone(self):
        """
        If the first parameter to a `maybe`-wrapped function is not ``None``
        then the result of the wrapped function is returned.
        """
        self.assertThat(
            maybe(identity)(42),
            Equals(42))
        self.assertThat(
            maybe(identityv)(42, 1, a=2),
            Equals(((42, 1), {'a': 2})))


    def test_customDefault(self):
        """
        A custom value can be passed for the ``default`` parameter.
        """
        default = object()
        self.assertThat(
            maybe(identity, default=default)(None),
            Is(default))
        self.assertThat(
            maybe(identityv, default=default)(None, 1, a=2),
            Is(default))



class ContentEncodingTests(TestCase):
    """
    Tests for `txspinneret.util.contentEncoding`.
    """
    def test_default(self):
        """
        If there is no ``Content-Type`` header then use the default encoding.
        """
        headers = Headers()
        self.assertThat(
            contentEncoding(headers),
            Equals(b'utf-8'))


    def test_customDefault(self):
        """
        Allow specifying a default encoding.
        """
        headers = Headers()
        self.assertThat(
            contentEncoding(headers, b'utf-32'),
            Equals(b'utf-32'))


    def test_noCharset(self):
        """
        If the ``Content-Type`` header does not specify a charset then use the
        default encoding.
        """
        headers = Headers({'Content-Type': ['text/plain']})
        self.assertThat(
            contentEncoding(headers),
            Equals(b'utf-8'))


    def test_contentEncoding(self):
        """
        Use the encoding specified in the ``Content-Type`` header.
        """
        headers = Headers({b'Content-Type': [b'text/plain;charset=utf-32']})
        self.assertThat(
            contentEncoding(headers),
            Equals(b'utf-32'))



class FixedOffsetTests(TestCase):
    """
    Tests for `txspinneret.util.FixedOffset`.
    """
    def test_repr(self):
        """
        Human-readable representation.
        """
        self.assertThat(
            repr(FixedOffset(0, 0)),
            Equals(b'FixedOffset(0, 0)'))
        self.assertThat(
            repr(FixedOffset(2, 0)),
            Equals(b'FixedOffset(2, 0)'))
        self.assertThat(
            repr(FixedOffset(5, 30)),
            Equals(b'FixedOffset(5, 30)'))
