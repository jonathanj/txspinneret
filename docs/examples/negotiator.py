import json
from twisted.web.resource import Resource
from twisted.web.template import Element, TagLoader, tags
from txspinneret.resource import (
    ContentTypeNegotiator, INegotiableResource, ISpinneretResource)
from zope.interface import implementer

@implementer(INegotiableResource)
class FooJSON(Resource):
    contentType = 'application/json'
    acceptTypes = ['application/json', 'application/javascript']

    def __init__(self, obj):
        self.obj = obj
        Resource.__init__(self)

    def render_GET(self, request):
        return json.dumps(self.obj)

class FooElement(Element):
    loader = TagLoader(tags.h1('Try accepting JSON!'))

@implementer(INegotiableResource, ISpinneretResource)
class FooHTML(object):
    contentType = 'text/html'
    acceptTypes = ['text/html']

    def render_GET(self, request):
        return FooElement()

def start():
    data = {'name': 'Bob'}
    resource = ContentTypeNegotiator(
        [FooHTML(), FooJSON(data)],
        fallback=True)
    resource.isLeaf = True
    return resource
