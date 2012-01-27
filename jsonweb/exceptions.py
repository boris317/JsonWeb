class JsonWebError(Exception):
    def __init__(self, message, error_type=None, error_sub_type=None, **extras):
        Exception.__init__(self, message)
        self.error_type = error_type
        self.error_sub_type = error_sub_type
        self.extras = extras