import humecord

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

# -- any --
class TestException(Exception):
    pass

class LookupError(Exception):
    pass

class DevError(Exception):
    pass

class NotFound(Exception):
    pass

class InitError(Exception):
    def __init__(self, message, traceback = True, log = True):
        super().__init__(message)

        self.message = message

        self.traceback = traceback

        self.log = log

class CriticalError(Exception):
    def __init__(self, message, traceback = True):
        super().__init__(message)

        self.message = message

        self.traceback = traceback

class CloseLoop(Exception):
    pass

# -- argparse --
class InvalidRule(Exception):
    pass

class InvalidData(Exception):
    pass

# -- messenger --
class InvalidKey(Exception):
    pass