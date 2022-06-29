import inspect


def _to_tuple(item):
    if isinstance(item, tuple) or isinstance(item, list):
        return item
    return (item,)  # Must leave parentheses


class _StepDecorator:
    def __init__(self, func, desc=None, on_pass=None, on_fail=None):
        self.function = func
        self.desc = desc

        # Always pass in as None or a tuple
        self.on_pass = on_pass if on_pass is None else _to_tuple(on_pass)
        self.on_fail = on_fail if on_fail is None else _to_tuple(on_fail)

        if self.on_pass and self.on_fail:
            raise Exception(f"Step {self.function.__name__} cannot have both on_pass and on_fail")

    def __call__(self, *args, **kwargs):
        results = self.function(args[0])

        # Returning a boolean will always be interpreted as indicating pass/fail and NOT the result.
        # To return a boolean, must return (pass/fail bool, result bool)
        if not isinstance(results, tuple):
            passed = results if isinstance(results, bool) else True
            return_val = results if not isinstance(results, bool) else None
            results = (passed, return_val)

        # Store the result for later analysis as well as returning it
        args[0].step_directory[self.function.__name__]['results'] = results
        return results

    @classmethod
    def get_name(cls):
        return cls.__name__[1:]  # ex. _Step => Step


def _get_step_decorator_func(cls):
    def dec(func=None, desc=None, on_pass=None, on_fail=None):
        if func:
            return cls(func)
        else:
            def wrapper(function):
                return cls(function, desc, on_pass, on_fail)

            return wrapper

    return dec


class _Substep:
    call_history = {}

    def __init__(self, func, desc=None):
        self.function = func
        self.desc = desc

        # ex. parent_function.substep_function
        self.substep_name = f"{inspect.stack()[2].function}.{self.function.__name__}"
        if _Substep.call_history.get(self.substep_name) is None:
            _Substep.call_history[self.substep_name] = []

    def __call__(self, *args, **kwargs):
        results = self.function(*args)

        # Result is interpreted in the same way as other steps
        if not isinstance(results, tuple):
            passed = results if isinstance(results, bool) else True
            return_val = results if not isinstance(results, bool) else None
            results = (passed, return_val)

        _Substep.call_history[self.substep_name].append({
            "results": results,
            "desc": self.desc,
            "name": self.function.__name__,
            "type": "_Substep"
        })
        return results

    @classmethod
    def get_name(cls):
        return cls.__name__[1:]

    @staticmethod
    def get_substeps_for_parent(parent):
        subs = _Substep.call_history
        results = []
        for key in subs:
            if parent in key:
                results += subs[key]
        return results

    @staticmethod
    def parent_has_substeps(parent):
        subs = _Substep.call_history
        for key in subs:
            if parent in key and "." in key:
                return True
        return False


def Substep(func=None, desc=None):
    if func:
        return _Substep(func)
    else:
        def wrapper(function):
            return _Substep(function, desc)

        return wrapper


# Define the different flight types
class _Setup(_StepDecorator):
    pass


def Setup(*args, **kwargs):
    return _get_step_decorator_func(_Setup)(*args, **kwargs)


###

class _Task(_StepDecorator):
    pass


def Task(*args, **kwargs):
    return _get_step_decorator_func(_Task)(*args, **kwargs)


###

class _Test(_StepDecorator):
    pass


def Test(*args, **kwargs):
    return _get_step_decorator_func(_Test)(*args, **kwargs)


###

class _Teardown(_StepDecorator):
    pass


def Teardown(*args, **kwargs):
    return _get_step_decorator_func(_Teardown)(*args, **kwargs)
