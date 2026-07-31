from rest_framework.exceptions import APIException

class NoFreeSpaceAvailable(Exception):
    """Exception raised for custom error in the application."""

    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        return f"{super().__str__()} (Error Code: {self.error_code})"
class NoCandidateFound(Exception):
    """Exception raised for custom error in the application."""

    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        return f"{super().__str__()} (Error Code: {self.error_code})"

class IPVersionInvalid(Exception):
    """Exception raised for custom error in the application."""

    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        return f"{super().__str__()} (Error Code: {self.error_code})"


class RestNoFreeSpaceAvailable(APIException):
    status_code = 500
    default_detail = 'There is not enough free IP Space to handle this request.'
    default_code = 'no_free_space'

class RestNoFreeSpaceAvailable(APIException):
    status_code = 500
    default_detail = 'The requested IP Space is not available to be allocated.'
    default_code = 'no_requested_space'

class RestIPVersionInvalid(APIException):
    status_code = 400
    default_detail = '4 or 6 are the only supported IP Versions'
    default_code = 'bad_ip_version'

class RestIPAddressInvalid(APIException):
    status_code = 400
    default_detail = 'IP Address is malformed'
    default_code = 'bad_ip_address'

class RestGenericAPIException(APIException):
    status_code = 500
    default_detail = 'Other Exception'
    default_code = 'other_error'
    def __init__(self, message, error_code):
        self.detail = str(message)
        self.code = error_code
