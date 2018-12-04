from pyramid.security import Allow


# TODO: get client_id from settings?
#       configure on startup or during runtime?
class Root(object):
    # Context object to map roles to permissions

    __parent__ = None
    __name__ = None

    __acl__ = [
        (Allow, 'token/user', 'view'),
        (Allow, 'token/admin', 'admin'),
    ]

    def __init__(self, request):
        pass
