class BlacklistedError(Exception):
    pass

class InvalidGuildError(Exception):
    pass

class CommandDisabledError(Exception):
    pass

class ApiError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class MojangError(BaseException):
    def __init__(self, error):
        self.error = error