from threading import Thread
import unittest

from jsonweb._local import LocalStack

stack = LocalStack()

class TestLocalStack(unittest.TestCase):
    def test_each_thread_has_own_stack(self):
        stack.push(42)
        
        self.assertEqual(stack.top, 42)
        
        class TestThread(Thread):
            def run(inst):
                self.assertEqual(stack.top, None)
                stack.push(10)
                self.assertEqual(stack.top, 10)
                
        t = TestThread()
        t.start()
        t.join()
        
        self.assertEqual(stack.top, 42)
        stack.clear()
        
    def test_pop_on_empty_stack_returns_None(self):
        self.assertEqual(stack.pop(), None)
        
    def test_push_and_pop(self):
        stack.push(66)
        stack.push(166)
        
        self.assertEqual(stack.top, 166)
        self.assertEqual(stack.pop(), 166)
        self.assertEqual(stack.pop(), 66)
        
        
        
        
        
        