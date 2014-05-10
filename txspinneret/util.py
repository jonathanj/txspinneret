import cgi
import datetime
from collections import OrderedDict
from functools import wraps
from itertools import chain


# Why does Python not have this built-in?
identity = lambda x: x



def _parseAccept(headers):
    """
    Parse and sort an ``Accept`` header.

    The header is sorted according to the ``q`` parameter for each header value.

    @rtype: `OrderedDict` mapping `bytes` to `dict`
    @return: Mapping of media types to header parameters.
    """
    def sort(value):
        return float(value[1].get('q', 1))
    return OrderedDict(sorted(_splitHeaders(headers), key=sort, reverse=True))



def _splitHeaders(headers):
    """
    Split an HTTP header whose components are separated with commas.

    Each component is then split on semicolons and the component arguments
    converted into a `dict`.

    @return: `list` of 2-`tuple` of `bytes`, `dict`
    @return: List of header arguments and mapping of component argument names
        to values.
    """
    return [cgi.parse_header(value)
            for value in chain.from_iterable(
                s.split(',') for s in headers
                if s)]



def contentEncoding(requestHeaders, encoding=None):
    """
    Extract an encoding from a ``Content-Type`` header.

    @type  requestHeaders: `twisted.web.http_headers.Headers`
    @param requestHeaders: Request headers.

    @type  encoding: `bytes`
    @param encoding: Default encoding to assume if the ``Content-Type``
        header is lacking one. Defaults to ``UTF-8``.

    @rtype: `bytes`
    @return: Content encoding.
    """
    if encoding is None:
        encoding = b'utf-8'
    headers = _splitHeaders(
        requestHeaders.getRawHeaders(b'Content-Type', []))
    if headers:
        return headers[0][1].get(b'charset', encoding)
    return encoding



def maybe(f, default=None):
    """
    Create a nil-safe callable decorator.

    If the wrapped callable receives ``None`` as its argument, it will return
    ``None`` immediately.
    """
    @wraps(f)
    def _maybe(x, *a, **kw):
        if x is None:
            return default
        return f(x, *a, **kw)
    return _maybe



# Thank you epsilon.extime.
class FixedOffset(datetime.tzinfo):
    """
    Fixed offset timezone.
    """
    _zeroOffset = datetime.timedelta()

    def __init__(self, hours, minutes):
        self._hours = hours
        self._minutes = minutes
        self.offset = datetime.timedelta(minutes=hours * 60 + minutes)


    def utcoffset(self, dt):
        return self.offset


    def dst(self, tz):
        return self._zeroOffset


    def __repr__(self):
        return b'%s(%d, %d)' % (
            type(self).__name__, self._hours, self._minutes)



UTC = FixedOffset(0, 0)
