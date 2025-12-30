class FantraxException(Exception):
    """ Base class for all FantraxService exceptions. """
    pass

class Unauthorized(FantraxException):
    """ Exception thrown when accessing a private endpoint without Authorization """
    pass
