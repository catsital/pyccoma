class PyccomaError(Exception):
    """Any error caused by Pyccoma will be caught
       with this exception."""


class PageError(PyccomaError):
    def __init__(self, url):
        err = f"Unable to access page on {url}"
        Exception.__init__(self, err)


class LoginError(PyccomaError):
    def __init__(self):
        err = "Login required."
        Exception.__init__(self, err)
