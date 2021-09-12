class ClientError(Exception):
    def __init__(self, message, statusCode = 400):
        super().__init__(message)
        self.statusCode = statusCode

class AuthenticationError(ClientError):
    def __init__(self, message):
        super().__init__(message, 401)

class AuthorizationError(ClientError):
    def __init__(self, message):
        super().__init__(message, 403)

class NotFoundError(ClientError):
    def __init__(self, message):
        super().__init__(message, 404)

class ConflictError(ClientError):
    def __init__(self, message):
        super().__init__(message, 409)