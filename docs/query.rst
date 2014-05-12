.. py:currentmodule:: txspinneret.query

Query Arguments
===============

The tedious process of processing query arguments usually follows this pattern:

    * Check for the existence of the argument;
    * Check that the argument has at least one value;
    * Convert the argument from its text representation into something more
      useful.


Parsing query arguments
-----------------------

This small set of utility functions can relieve some of that pain, for example
assume the query string is
``count=1&fields=a,b,c&includeHidden=yes&start=1399473753&end=&flags=FOO&flags=BAR``,
Twisted Web parses this into the following `IRequest.args` result:

.. code-block:: python

    {'count':         ['1'],
     'fields':        ['a,b,c'],
     'includeHidden': ['yes'],
     'start':         ['1399473753'],
     'end':           [],
     'flags':         ['FOO', 'BAR']}

Instead of performing all the necessary checks and transformations yourself
this could be parsed with the following:

.. code-block:: python

    from txspinneret import query as q
    from twisted.python.constants import Names, NamedConstant

    class FlagConstants(Names):
        FOO = NamedConstant()
        BAR = NamedConstant()

    flag = lambda value: FlagConstants.lookupByName(q.Text(value))
    q.parse({
        'count':         q.one(q.Integer),
        'fields':        q.one(q.Delimited),
        'includeHidden': q.one(q.Boolean),
        'start':         q.one(q.Timestamp),
        'end':           q.one(q.Timestamp),
        'flags':         q.many(flag)}, request.args)

Which would produce the result:

.. code-block:: python

    {'count':         1,
     'end':           None,
     'fields':        [u'a', u'b', u'c'],
     'start':         datetime.datetime(2014, 5, 7, 16, 42, 33),
     'flags':         [<FlagConstant=FOO>, <FlagConstant=BAR>],
     'includeHidden': True}
