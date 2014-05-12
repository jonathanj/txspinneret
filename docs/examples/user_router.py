from collections import namedtuple
from twisted.web.static import Data
from txspinneret.route import Router, Any

class UserRouter(object):
    router = Router()

    def __init__(self, user):
        self.user = user

    def getFriend(self, name):
        return self.user.friends[name]

    @router.route('/')
    def name(self, request, params):
        return Data(self.user.name, 'text/plain')

    @router.subroute('friend', Any('name'))
    def friend(self, request, params):
        return UserRouter(self.getFriend(params['name'])).router.resource()

def start():
    User = namedtuple(b'User', ['name', 'friends'])
    bob = User('bob', {})
    chuck = User('chuck', {'bob': bob})
    default = User('default', {'bob': bob, 'chuck': chuck})
    return UserRouter(default).router.resource()
