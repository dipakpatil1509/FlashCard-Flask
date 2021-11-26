class APIException(Exception):
    def __init__(self, error_code, error_desc):
        self.error_desc = error_desc
        self.error = dict(error_code=error_code, error_message=error_desc)
    
    def __str__(self) -> str:
        return self.error_desc