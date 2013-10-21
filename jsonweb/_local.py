try:
    from threading import local
except ImportError:
    from dummy_threading import local


class LocalStack(local):
    def __init__(self):
        self.stack = []
        
    def push(self, obj):
        self.stack.append(obj)
        
    def pop(self):
        try:
            return self.stack.pop()
        except IndexError:
            return None
        
    def clear(self):
        self.stack = []
        
    @property
    def top(self):
        try:
            return self.stack[-1]
        except IndexError:
            return None
