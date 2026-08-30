from pkg.a import foo
import pkg.b as b_mod


def helper():
    return 1


def caller_same_file():
    return helper()


def caller_from_import():
    return foo()


def caller_module_qualified():
    return b_mod.use_foo()


class Greeter:
    def greet(self):
        return self.build_message()

    def build_message(self):
        return "hello"
