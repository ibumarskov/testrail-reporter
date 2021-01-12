class ReporterException(Exception):
    """Base class for exceptions in TestRail Reporter."""
    message = "An unknown exception occurred"

    def __init__(self, *args, **kwargs):
        super(ReporterException, self).__init__()
        try:
            self._error_string = self.message.format(**kwargs)
        except Exception:
            # at least get the core message out if something happened
            self._error_string = self.message
        if args:
            # If there is a non-kwarg parameter, assume it's the error
            # message or reason description and tack it on to the end
            # of the exception message
            # Convert all arguments into their string representations...
            # args = ["{}".format(arg for arg in args)]
            # self._error_string = (self._error_string +
            #                       "\nDetails:\n%s" % '\n'.join(args))
            self._error_string = (self._error_string + "\nDetails:\n")
            for arg in args:
                self._error_string = self._error_string + '{}\n'.format(arg)

    def __str__(self):
        return self._error_string


class NotFound(ReporterException):
    message = "TestRail reporter hasn't found object"


class Conflict(ReporterException):
    message = "Conflict detected"


class UnknownAction(ReporterException):
    message = "Unknown action: {action}"
