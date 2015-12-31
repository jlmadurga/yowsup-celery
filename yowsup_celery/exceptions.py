# -*- coding: utf-8 -*-
class YowsupCeleryError(Exception):
    pass


class UnexpectedError(YowsupCeleryError):
    """ Raised for unknown or unexpected errors. """
    pass


class ConfigurationError(YowsupCeleryError):
    """
    Raised when YowsupStack detects and error in configurations
    """
    pass


class ConnectionError(YowsupCeleryError):
    """
    Raised when CeleryLayer tries to perform an action which requires to be
    connected to WhatsApp
    """
    pass


class AuthenticationError(YowsupCeleryError):
    """
    Raised when YowsupStack cannot authenticate with the whatsapp.  This means the
    password for number is incorrect. Check if registration was correct
    """
    pass
