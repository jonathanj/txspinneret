from datetime import datetime
from operator import isSequenceType

from spinneret.util import maybe



def _isSequenceTypeNotText(x):
    return isSequenceType(x) and not isinstance(x, (bytes, unicode))



def one(func, n=0):
    """
    Create a callable that applies a callable to the first value in a sequence.

    If the value is not a sequence or is an empty sequence then C{None} is
    returned.
    """
    def _one(result):
        if _isSequenceTypeNotText(result) and len(result) > n:
            return func(result[n])
        return None
    return maybe(_one)



def many(func):
    """
    Create a callable that applies a callable to every value in a sequence.

    If the value is not a sequence then C{None} is returned.
    """
    def _many(result):
        if _isSequenceTypeNotText(result):
            return map(func, result)
        return None
    return maybe(_many)



def Text(value, encoding=None):
    """
    Parse a value as text.

    @type  value: L{unicode} or L{bytes}
    @param value: Text value to parse.

    @type  encoding: L{bytes}
    @param encoding: Encoding to treat L{bytes} values as, defaults to
        I{utf-8}.

    @rtype: L{unicode}
    @return: Parsed text or C{None} if C{value} is neither L{bytes} nor
        L{unicode}.
    """
    if encoding is None:
        encoding = 'utf-8'
    if isinstance(value, bytes):
        return value.decode(encoding)
    elif isinstance(value, unicode):
        return value
    return None



def Integer(value, base=10, encoding=None):
    """
    Parse a value as an integer.

    @type  value: L{unicode} or L{bytes}
    @param value: Text value to parse.

    @type  base: L{unicode} or L{bytes}
    @param base: Base to assume C{value} is specified in.

    @type  encoding: L{bytes}
    @param encoding: Encoding to treat L{bytes} values as, defaults to
        I{utf-8}.

    @rtype: L{int}
    @return: Parsed integer or C{None} if C{value} could not be parsed as an
        integer.
    """
    try:
        return int(Text(value, encoding), base)
    except (TypeError, ValueError):
        return None



def Float(value, encoding=None):
    """
    Parse a value as a floating point number.

    @type  value: L{unicode} or L{bytes}
    @param value: Text value to parse.

    @type  encoding: L{bytes}
    @param encoding: Encoding to treat L{bytes} values as, defaults to
        I{utf-8}.

    @rtype: L{float}
    @return: Parsed float or C{None} if C{value} could not be parsed as a
        float.
    """
    try:
        return float(Text(value, encoding))
    except (TypeError, ValueError):
        return None



def Boolean(value, true=(u'yes', u'1', u'true'), false=(u'no', u'0', u'false'),
            encoding=None):
    """
    Parse a value as a boolean.

    @type  value: L{unicode} or L{bytes}
    @param value: Text value to parse.

    @type  true: L{tuple} of L{unicode}
    @param true: Values to compare, ignoring case, for C{True} values.

    @type  false: L{tuple} of L{unicode}
    @param false: Values to compare, ignoring case, for C{False} values.

    @type  encoding: L{bytes}
    @param encoding: Encoding to treat L{bytes} values as, defaults to
        I{utf-8}.

    @rtype: L{bool}
    @return: Parsed boolean or C{None} if C{value} did not match C{true} or
        C{false} values.
    """
    value = Text(value, encoding)
    if value is not None:
        value = value.lower().strip()
    if value in true:
        return True
    elif value in false:
        return False
    return None



def Delimited(value, parser=Text, delimiter=u',', encoding=None):
    """
    Parse a value as a delimited list.

    @type  value: L{unicode} or L{bytes}
    @param value: Text value to parse.

    @type  parser: I{callable} taking a L{unicode} parameter
    @param parser: Callable to map over the delimited text values.

    @type  delimiter: L{unicode}
    @param delimiter: Delimiter text.

    @type  encoding: L{bytes}
    @param encoding: Encoding to treat L{bytes} values as, defaults to
        I{utf-8}.

    @rtype: L{list}
    @return: List of parsed values.
    """
    value = Text(value, encoding)
    if value is None or value == u'':
        return []
    return map(parser, value.split(delimiter))



def Timestamp(value, _divisor=1., encoding=None):
    """
    Parse a value as a POSIX timestamp in seconds.

    @type  value: L{unicode} or L{bytes}
    @param value: Text value to parse, which should be the number of seconds
        since the epoch.

    @type  _divisor: L{float}
    @param _divisor: Number to divide the value by.

    @type  encoding: L{bytes}
    @param encoding: Encoding to treat L{bytes} values as, defaults to
        I{utf-8}.

    @rtype: L{datetime.datetime}
    @return: Parsed datetime or C{None} if C{value} could not be parsed.
    """
    value = Float(value, encoding)
    if value is not None:
        value = value / _divisor
        return datetime.fromtimestamp(value)
    return None



def TimestampMs(value, encoding=None):
    """
    Parse a value as a POSIX timestamp in milliseconds.

    @type  value: L{unicode} or L{bytes}
    @param value: Text value to parse, which should be the number of
        milliseconds since the epoch.

    @type  _divisor: L{float}
    @param _divisor: Number to divide the timestamp value by.

    @type  encoding: L{bytes}
    @param encoding: Encoding to treat L{bytes} values as, defaults to
        I{utf-8}.

    @rtype: L{datetime.datetime}
    @return: Parsed datetime or C{None} if C{value} could not be parsed.
    """
    return Timestamp(value, _divisor=1000., encoding=encoding)



def parse(expected, query):
    """
    Parse query parameters.

    @type  expected: L{dict} mapping L{bytes} to I{callable}
    @param expected: Mapping of query argument names to argument parsing
        callables.

    @type  query: L{dict} mapping L{bytes} to L{list} of L{bytes}
    @param query: Mapping of query argument names to lists of argument values,
        this is the form that Twisted Web's C{IRequest.args} value takes.

    @rtype: L{dict} mapping L{bytes} to L{object}
    @return: Mapping of query argument names to parsed argument values.
    """
    return dict(
        (key, parser(query.get(key, [])))
        for key, parser in expected.items())



__all__ = ['one', 'many', 'Text', 'Integer', 'Boolean', 'Delimited', 'parse']
