import cgi
from collections import OrderedDict
from functools import wraps
from itertools import chain


# Why does Python not have this built-in?
identity = lambda x: x



def _parseAccept(headers):
    """
    Parse and sort an I{Accept} header.

    The header is sorted according to the I{q} parameter for each header value.

    @rtype: L{OrderedDict} mapping L{bytes} to L{dict}
    @return: Mapping of media types to header parameters.
    """
    def sort((contentType, args)):
        return float(args.get('q', 1))
    return OrderedDict(sorted(_splitHeaders(headers), key=sort, reverse=True))



def _splitHeaders(headers):
    """
    Split an HTTP header whose components are separated with commas.

    Each component is then split on semicolons and the component arguments
    converted into a L{dict}.

    @return: L{list} of C{(bytes, dict)}
    @return: List of header arguments and mapping of component argument names
        to values.
    """
    return [cgi.parse_header(value)
            for value in chain.from_iterable(
                s.split(',') for s in headers
                if s)]



def contentEncoding(requestHeaders, encoding=None):
    """
    Extract an encoding from a I{Content-Type} header.

    @type  requestHeaders: L{twisted.web.http_headers.Headers}
    @param requestHeaders: Request headers.

    @type  encoding: L{bytes}
    @param encoding: Default encoding to assume if the I{Content-Type}
        header is lacking one. Defaults to C{UTF-8}.

    @rtype: L{bytes}
    @return: Content encoding.
    """
    if encoding is None:
        encoding = b'utf-8'
    headers = _splitHeaders(
        requestHeaders.getRawHeaders(b'Content-Type', []))
    if headers:
        return headers[0][1].get(b'charset', encoding)
    return encoding



def maybe(f):
    """
    Create a nil-safe callable decorator.

    If the wrapped callable receives C{None} as its argument, it will return
    C{None} immediately.
    """
    @wraps(f)
    def _maybe(x, *a, **kw):
        if x is None:
            return None
        return f(x, *a, **kw)
    return _maybe
