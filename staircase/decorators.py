import inspect


def _to_tuple(item):
    if isinstance(item, tuple):
        return item

    if isinstance(item, list):
        return tuple(item)

    return (item,)  # Must leave parentheses to make tuple


def _convert_results(results):
    if results is None:
        return True, None  # No result is interpreted as a pass
    elif isinstance(results, tuple) or isinstance(results, list):
        if len(results) == 0 or len(results) > 2:
            return None
        val = None if len(results) == 1 else results[1]
        return bool(results[0]), val
    else:
        # if a single return value
        # if the return value is a bool, it indicates pass fail
        # if its another value, that is the return value of the func
        passed = results if isinstance(results, bool) else True
        return_val = results if not isinstance(results, bool) else None
        return passed, return_val


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
        if len(args) < 1 or not inspect.isclass(type(args[0])):
            raise Exception("Step decorated function must be called with an instance of staircase.")

        is_staircase_test_subclass = False
        for resolver in args[0].__class__.__mro__:
            if resolver.__name__ == 'StaircaseTest':
                is_staircase_test_subclass = True

        if not is_staircase_test_subclass:
            raise Exception(
                'Step decorator can only be called when it decorates an instance method defined in a class.')

        results = self.function(args[0])

        results = _convert_results(results)
        if results is None:
            raise Exception('Invalid return from step function. Must be a tuple of type (bool, any)')

        # Store the result for later analysis as well as returning it
        args[0].step_directory[self.function.__name__]['results'] = results
        return results

    @classmethod
    def get_name(cls):
        return cls.__name__[1:]  # ex. _Step => Step

    @staticmethod
    def _get_test_instance():
        """
        Walk the stack until it finds the calling StaircaseTest instance
        """
        obj_in_frame = None
        i = 0

        try:
            while repr(obj_in_frame) != 'StaircaseTest':
                obj_in_frame = _Substep._get_args_for_frame(i)[3].get('self')
                i += 1
            return obj_in_frame
        except IndexError as e:
            return None


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

    def __init__(self, func, desc=None, on_pass=None, on_fail=None):
        self.function = func
        self.desc = desc

        self.test_instance = self._get_test_instance()
        if self.test_instance is None:
            raise Exception('Substep can only be defined within a test instance.')

        self.parent_function = self._get_parent_function_name()

        # ex. parent_function.substep_function
        self.substep_name = f"{self.parent_function}.{self.function.__name__}"

        self.on_pass = on_pass if on_pass is None else _to_tuple(on_pass)
        self.on_fail = on_fail if on_fail is None else _to_tuple(on_fail)

        if not self._dependencies_are_ok():
            raise Exception('A substep cannot rely on a on_pass or on_fail that the parent step does not rely on.')

    def __call__(self, *args, **kwargs):
        results = self.function(*args)

        # Result is interpreted in the same way as other steps
        results = _convert_results(results)
        if results is None:
            raise Exception('Invalid return from substep function. Must be a tuple of type (bool, any)')

        self.test_instance.step_directory[self.parent_function]['substeps'].append({
            "results": results,
            "desc": self.desc,
            "name": self.function.__name__,
            "type": "_Substep"
        })

        return results

    def _dependencies_are_ok(self):
        parent_on_pass = self.test_instance.step_directory[self.parent_function]['on_pass']
        parent_on_fail = self.test_instance.step_directory[self.parent_function]['on_fail']

        on_pass_ok = True
        if self.on_pass is None and parent_on_pass is not None or self.on_pass is not None and parent_on_pass is None:
            on_pass_ok = False

        if self.on_pass is not None and parent_on_pass is not None:
            on_pass_ok = set(self.on_pass) <= set(parent_on_pass)

        on_fail_ok = True
        if self.on_fail is None and parent_on_fail is not None or self.on_fail is not None and parent_on_fail is None:
            on_fail_ok = False

        if self.on_fail is not None and parent_on_fail is not None:
            on_fail_ok = set(self.on_fail) <= set(parent_on_fail)

        return on_pass_ok and on_fail_ok

    def _get_parent_function_name(self):
        print(inspect.stack()[3])
        return inspect.stack()[3].function

    @classmethod
    def get_name(cls):
        return cls.__name__[1:]

    @staticmethod
    def _get_test_instance():
        """
        Walk the stack until it finds the calling StaircaseTest instance
        """
        obj_in_frame = None
        i = 0

        try:
            while repr(obj_in_frame) != 'StaircaseTest':
                obj_in_frame = _Substep._get_args_for_frame(i)[3].get('self')
                i += 1
            return obj_in_frame
        except IndexError as e:
            return None

    @staticmethod
    def _get_args_for_frame(stack_level: int):
        frame = inspect.currentframe()
        outer_frames = inspect.getouterframes(frame)
        caller_frame = outer_frames[stack_level][0]
        return inspect.getargvalues(caller_frame)


def Substep(func=None, desc=None, on_pass=None, on_fail=None):
    if func:
        return _Substep(func)
    else:
        def wrapper(function):
            return _Substep(function, desc, on_pass, on_fail)

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
