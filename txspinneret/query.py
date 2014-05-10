"""
Utility functions for processing query arguments.

The task of processing query arguments is made easy by deciding whether you
want exactly `one` or `many` results and then composing that with the expected
argument type, such as `Integer`, `Text`, `Boolean`, etc.; for example:

.. code-block:: python

    one(Integer)

Produces a callable that takes a list of strings and produces an integer from
the first value, or ``None`` if the list was empty or the first value could not
be parsed as an integer.

.. code-block:: python

    many(Boolean)

Produces a callable that takes a list of strings and produces a list of
booleans.
"""
from datetime import datetime
from operator import isSequenceType

from txspinneret.util import maybe, UTC



def _isSequenceTypeNotText(x):
    """
    Is this a ``sequence`` type that isn't also a ``string`` type?
    """
    return isSequenceType(x) and not isinstance(x, (bytes, unicode))



def one(func, n=0):
    """
    Create a callable that applies ``func`` to a value in a sequence.

    If the value is not a sequence or is an empty sequence then ``None`` is
    returned.

    :type  func: `callable`
    :param func: Callable to be applied to each result.

    :type  n: `int`
    :param n: Index of the value to apply ``func`` to.
    """
    def _one(result):
        if _isSequenceTypeNotText(result) and len(result) > n:
            return func(result[n])
        return None
    return maybe(_one)



def many(func):
    """
    Create a callable that applies ``func`` to every value in a sequence.

    If the value is not a sequence then an empty list is returned.

    :type  func: `callable`
    :param func: Callable to be applied to the first result.
    """
    def _many(result):
        if _isSequenceTypeNotText(result):
            return map(func, result)
        return []
    return maybe(_many, default=[])



def Text(value, encoding=None):
    """
    Parse a value as text.

    :type  value: `unicode` or `bytes`
    :param value: Text value to parse

    :type  encoding: `bytes`
    :param encoding: Encoding to treat ``bytes`` values as, defaults to
        ``utf-8``.

    :rtype: `unicode`
    :return: Parsed text or ``None`` if ``value`` is neither `bytes` nor
        `unicode`.
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

    :type  value: `unicode` or `bytes`
    :param value: Text value to parse

    :type  base: `unicode` or `bytes`
    :param base: Base to assume ``value`` is specified in.

    :type  encoding: `bytes`
    :param encoding: Encoding to treat ``bytes`` values as, defaults to
        ``utf-8``.

    :rtype: `int`
    :return: Parsed integer or ``None`` if ``value`` could not be parsed as an
        integer.
    """
    try:
        return int(Text(value, encoding), base)
    except (TypeError, ValueError):
        return None



def Float(value, encoding=None):
    """
    Parse a value as a floating point number.

    :type  value: `unicode` or `bytes`
    :param value: Text value to parse.

    :type  encoding: `bytes`
    :param encoding: Encoding to treat `bytes` values as, defaults to
        ``utf-8``.

    :rtype: `float`
    :return: Parsed float or ``None`` if ``value`` could not be parsed as a
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

    :type  value: `unicode` or `bytes`
    :param value: Text value to parse.

    :type  true: `tuple` of `unicode`
    :param true: Values to compare, ignoring case, for ``True`` values.

    :type  false: `tuple` of `unicode`
    :param false: Values to compare, ignoring case, for ``False`` values.

    :type  encoding: `bytes`
    :param encoding: Encoding to treat `bytes` values as, defaults to
        ``utf-8``.

    :rtype: `bool`
    :return: Parsed boolean or ``None`` if ``value`` did not match ``true`` or
        ``false`` values.
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

    :type  value: `unicode` or `bytes`
    :param value: Text value to parse.

    :type  parser: `callable` taking a `unicode` parameter
    :param parser: Callable to map over the delimited text values.

    :type  delimiter: `unicode`
    :param delimiter: Delimiter text.

    :type  encoding: `bytes`
    :param encoding: Encoding to treat `bytes` values as, defaults to
        ``utf-8``.

    :rtype: `list`
    :return: List of parsed values.
    """
    value = Text(value, encoding)
    if value is None or value == u'':
        return []
    return map(parser, value.split(delimiter))



def Timestamp(value, _divisor=1., tz=UTC, encoding=None):
    """
    Parse a value as a POSIX timestamp in seconds.

    :type  value: `unicode` or `bytes`
    :param value: Text value to parse, which should be the number of seconds
        since the epoch.

    :type  _divisor: `float`
    :param _divisor: Number to divide the value by.

    :type  tz: `tzinfo`
    :param tz: Timezone, defaults to UTC.

    :type  encoding: `bytes`
    :param encoding: Encoding to treat `bytes` values as, defaults to
        ``utf-8``.

    :rtype: `datetime.datetime`
    :return: Parsed datetime or ``None`` if ``value`` could not be parsed.
    """
    value = Float(value, encoding)
    if value is not None:
        value = value / _divisor
        return datetime.fromtimestamp(value, tz)
    return None



def TimestampMs(value, encoding=None):
    """
    Parse a value as a POSIX timestamp in milliseconds.

    :type  value: `unicode` or `bytes`
    :param value: Text value to parse, which should be the number of
        milliseconds since the epoch.

    :type  encoding: `bytes`
    :param encoding: Encoding to treat `bytes` values as, defaults to
        ``utf-8``.

    :rtype: `datetime.datetime`
    :return: Parsed datetime or ``None`` if ``value`` could not be parsed.
    """
    return Timestamp(value, _divisor=1000., encoding=encoding)



def parse(expected, query):
    """
    Parse query parameters.

    :type  expected: `dict` mapping `bytes` to `callable`
    :param expected: Mapping of query argument names to argument parsing
        callables.

    :type  query: `dict` mapping `bytes` to `list` of `bytes`
    :param query: Mapping of query argument names to lists of argument values,
        this is the form that Twisted Web's `IRequest.args
        <twisted:twisted.web.iweb.IRequest.args>` value takes.

    :rtype: `dict` mapping `bytes` to `object`
    :return: Mapping of query argument names to parsed argument values.
    """
    return dict(
        (key, parser(query.get(key, [])))
        for key, parser in expected.items())



__all__ = [
    'parse', 'one', 'many', 'Text', 'Integer', 'Float', 'Boolean', 'Delimited',
    'Timestamp', 'TimestampMs']
