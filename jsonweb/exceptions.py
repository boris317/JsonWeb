class JsonWebError(Exception):
    def __init__(self, message, **extras):
        Exception.__init__(self, message)
        self.extras = extras