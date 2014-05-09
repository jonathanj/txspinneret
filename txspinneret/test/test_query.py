from datetime import datetime
from testtools import TestCase
from testtools.matchers import Equals, Is

from txspinneret.query import (
    parse, one, many, Boolean, Integer, Text, Delimited, Float, Timestamp,
    TimestampMs)
from txspinneret.util import identity, UTC



class TextTests(TestCase):
    """
    Tests for `txspinneret.query.Text`.
    """
    def test_none(self):
        """
        Parsing ``None`` results in ``None``.
        """
        self.assertThat(
            Text(None),
            Is(None))


    def test_ascii(self):
        """
        Parsing ASCII `bytes` results in `unicode`.
        """
        self.assertThat(
            Text(b'hello'),
            Equals(u'hello'))


    def test_defaultEncoding(self):
        """
        By default UTF-8 encoding is assumed.
        """
        self.assertThat(
            Text(b'\xe2\x98\x83'),
            Equals(u'\N{SNOWMAN}'))


    def test_customEncoding(self):
        """
        Specify a custom bytes encoding.
        """
        self.assertThat(
            Text(b'\xff\xfe\x03&', encoding='utf-16'),
            Equals(u'\N{SNOWMAN}'))



class IntegerTests(TestCase):
    """
    Tests for `txspinneret.query.Integer`.
    """
    def test_none(self):
        """
        Parsing ``None`` results in ``None``.
        """
        self.assertThat(
            Integer(None),
            Is(None))


    def test_invalid(self):
        """
        Invalid integers are parsed as ``None``.
        """
        self.assertThat(
            Integer(b'not a number'),
            Is(None))


    def test_valid(self):
        """
        Valid integers are parsed from bytes.
        """
        self.assertThat(
            Integer(b'1'),
            Equals(1))



class FloatTests(TestCase):
    """
    Tests for `txspinneret.query.Float`.
    """
    def test_none(self):
        """
        Parsing ``None`` results in ``None``.
        """
        self.assertThat(
            Float(None),
            Is(None))


    def test_invalid(self):
        """
        Invalid floats are parsed as ``None``.
        """
        self.assertThat(
            Float(b'not a number'),
            Is(None))


    def test_valid(self):
        """
        Valid floats are parsed from bytes.
        """
        self.assertThat(
            Float(b'1.23'),
            Equals(1.23))



class BooleanTests(TestCase):
    """
    Tests for `txspinneret.query.Boolean`.
    """
    def test_none(self):
        """
        Parsing ``None`` results in ``None``.
        """
        self.assertThat(
            Boolean(None),
            Is(None))


    def test_invalid(self):
        """
        Invalid boolean values are parsed as ``None``.
        """
        self.assertThat(
            Boolean(b'not a boolean'),
            Is(None))


    def test_true(self):
        """
        Valid true boolean values are parsed as ``True``.
        """
        self.assertThat(
            Boolean(b'yes'),
            Is(True))
        self.assertThat(
            Boolean(b'YES'),
            Is(True))
        self.assertThat(
            Boolean(b'1'),
            Is(True))
        self.assertThat(
            Boolean(b'true'),
            Is(True))
        self.assertThat(
            Boolean(b'True'),
            Is(True))


    def test_false(self):
        """
        Valid false boolean values are parsed as ``False``.
        """
        self.assertThat(
            Boolean(b'no'),
            Is(False))
        self.assertThat(
            Boolean(b'NO'),
            Is(False))
        self.assertThat(
            Boolean(b'0'),
            Is(False))
        self.assertThat(
            Boolean(b'false'),
            Is(False))
        self.assertThat(
            Boolean(b'False'),
            Is(False))



class DelimitedTests(TestCase):
    """
    Tests for `txspinneret.query.Delimited`.
    """
    def test_empty(self):
        """
        An empty value results in an empty `list`.
        """
        self.assertThat(
            Delimited(b''),
            Equals([]))


    def test_defaultEncoding(self):
        """
        By default UTF-8 encoding is assumed.
        """
        self.assertThat(
            Delimited(b'foo,\xe2\x98\x83'),
            Equals([u'foo', u'\N{SNOWMAN}']))


    def test_customEncoding(self):
        """
        Specify a custom bytes encoding.
        """
        self.assertThat(
            Delimited(b'\xff\xfef\x00o\x00o\x00,\x00\x03&', encoding='utf-16'),
            Equals([u'foo', u'\N{SNOWMAN}']))


    def test_defaultDelimiter(self):
        """
        Values are split on comma.
        """
        self.assertThat(
            Delimited(b'foo,bar'),
            Equals([u'foo', u'bar']))


    def test_customDelimiter(self):
        """
        Values are split on the specified delimiter.
        """
        self.assertThat(
            Delimited(b'foo;bar', delimiter=u';'),
            Equals([u'foo', u'bar']))


    def test_parser(self):
        """
        Values are mapped through the parser.
        """
        self.assertThat(
            Delimited(b'1,burp,2', parser=Integer),
            Equals([1, None, 2]))



class TimestampTests(TestCase):
    """
    Tests for `txspinneret.query.Timestamp`.
    """
    def test_none(self):
        """
        Parsing ``None`` results in ``None``.
        """
        self.assertThat(
            Timestamp(None),
            Is(None))


    def test_invalid(self):
        """
        Invalid timestamps are parsed as ``None``.
        """
        self.assertThat(
            Timestamp(b'not a number'),
            Is(None))


    def test_valid(self):
        """
        Valid timestamps are parsed from bytes.
        """
        self.assertThat(
            Timestamp(b'1399412885.957837'),
            Equals(datetime(2014, 5, 6, 21, 48, 5, 957837, tzinfo=UTC)))



class TimestampMsTests(TestCase):
    """
    Tests for `txspinneret.query.TimestampMs`.
    """
    def test_none(self):
        """
        Parsing ``None`` results in ``None``.
        """
        self.assertThat(
            TimestampMs(None),
            Is(None))


    def test_invalid(self):
        """
        Invalid timestamps are parsed as ``None``.
        """
        self.assertThat(
            TimestampMs(b'not a number'),
            Is(None))


    def test_valid(self):
        """
        Valid timestamps are parsed from bytes.
        """
        self.assertThat(
            TimestampMs(b'1399412885957.837'),
            Equals(datetime(2014, 5, 6, 21, 48, 5, 957837, tzinfo=UTC)))



class OneTests(TestCase):
    """
    Tests for `txspinneret.query.one`.
    """
    def test_nonSequence(self):
        """
        A non-sequence, or empty sequence, is parsed as ``None``.
        """
        self.assertThat(
            one(identity)(None),
            Is(None))
        self.assertThat(
            one(identity)(42),
            Is(None))
        self.assertThat(
            one(identity)(b'hello'),
            Is(None))
        self.assertThat(
            one(identity)([]),
            Is(None))


    def test_sequence(self):
        """
        The first element of a sequence is used.
        """
        self.assertThat(
            one(identity)([1, 2]),
            Equals(1))
        self.assertThat(
            one(identity)((1, 2)),
            Equals(1))
        self.assertThat(
            one(Integer)((b'1', 2)),
            Equals(1))
        self.assertThat(
            one(Integer)([b'1', '2']),
            Equals(1))


    def test_customN(self):
        """
        The element at the specified index of a sequence is used.
        """
        self.assertThat(
            one(identity, n=1)([1, 2]),
            Equals(2))
        self.assertThat(
            one(identity, n=3)((1, 2)),
            Is(None))



class ManyTests(TestCase):
    """
    Tests for `txspinneret.query.many`.
    """
    def test_nonSequence(self):
        """
        A non-sequence is parsed as ``None``.
        """
        self.assertThat(
            many(identity)(None),
            Equals([]))
        self.assertThat(
            many(identity)(42),
            Equals([]))
        self.assertThat(
            many(identity)(b'hello'),
            Equals([]))


    def test_sequence(self):
        """
        A callable is mapped over each element of a sequence.
        """
        self.assertThat(
            many(identity)([]),
            Equals([]))
        self.assertThat(
            many(identity)([1, 2]),
            Equals([1, 2]))
        self.assertThat(
            many(identity)((1, 2)),
            Equals([1, 2]))
        self.assertThat(
            many(Integer)([b'1', b'2']),
            Equals([1, 2]))



class ParseTests(TestCase):
    """
    Tests for `txspinneret.query.parse`.
    """
    def test_empty(self):
        """
        Parsing empty query arguments with no expected arguments results in an
        empty result.
        """
        self.assertThat(
            parse({}, {}),
            Equals({}))


    def test_nonexistentArgument(self):
        """
        If a query argument is expected but not found it appears as ``None`` in
        the result.
        """
        self.assertThat(
            parse({b'foo': one(Text)}, {}),
            Equals({b'foo': None}))


    def test_nonexistentExpected(self):
        """
        Query arguments that are not expected do not appear in the result.
        """
        self.assertThat(
            parse({}, {b'foo': [b'1']}),
            Equals({}))


    def test_parse(self):
        """
        Parse a query string.
        """
        query = {
            b'foo': [b'1', b'2'],
            b'bar': [],
            b'baz': [b'yes', b'1', b'False', b'huh'],
            b'quux': [b'hello', b'world']}

        self.assertThat(
            parse({b'foo': one(Integer),
                   b'bar': many(Integer),
                   b'baz': many(Boolean),
                   b'quux': many(Text),
                   b'notathing': many(Integer),
                   b'alsonotathing': one(Text)}, query),
            Equals({b'foo': 1,
                    b'bar': [],
                    b'baz': [True, True, False, None],
                    b'quux': [u'hello', u'world'],
                    b'notathing': [],
                    b'alsonotathing': None}))
