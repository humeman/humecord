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