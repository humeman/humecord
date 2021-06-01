# *
class NotImplemented(Exception):
    pass

# -- utils -> Colors --
class InvalidColorException(Exception):
    pass

# -- interfaces -> APIInterface --
class APIError(Exception):
    pass

class RequestError(Exception):
    pass

class EmptyResponse(Exception):
    pass

class InvalidRoute(Exception):
    pass

class UnsuccessfulRequest(Exception):
    pass

class APIOffline(Exception):
    pass

# -- utils -> Subprocess --
class SubprocessError(Exception):
    pass

# -- utils -> DateUtils --
class InvalidFormat(Exception):
    pass

# -- utils -> Components
class InvaldComponent(Exception):
    pass

class NotDefined(Exception):
    pass

# -- classes -> Permissions
class InvalidPermission(Exception):
    pass