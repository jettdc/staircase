## staircase

A simple, step-based testing framework.

Useful for tests with complex setups, teardowns, and dependencies between the tests.

### Getting Started

#### Defining A Test

Tests are defined in staircase via classes that inherit from the base test class.

```python
from staircase import StaircaseTest


class MyTest(StaircaseTest):
    pass
```

#### Adding Steps

Steps in staircase are broken up into 3 main "flights" (groups of steps):

1) Setup
2) Main (consists of `Task` and `Test` steps)
3) Teardown

All qualifying `Setup` steps are run before any main steps (`Task` and `Test`), and those steps are run before any
qualifying `Teardown` steps.

Steps are defined as methods on the class and wrapped in decorators that designate their type.

Steps return a tuple or a pass/fail bool:

- `return pass/fail bool, return value`
- `return pass/fail bool` (None return value)

```python
from staircase import StaircaseTest, Setup, Task, Test, Teardown


class MyTest(StaircaseTest):
    @Setup
    def my_setup_step(self):
        return True, 'Successfully setup.'

    @Task
    def prime_the_file(self):
        return True

    @Test
    def file_has_correct_contents(self):
        return True

    @Teardown
    def delete_artifacts(self):
        try:
            self._delete('...')
            return True
        except:
            return False, 'Exception occurred'
```

Dependencies can also be added between the steps. They will only run if their dependency
passes or fails, depending on the specified condition. Steps without dependencies will be run in an
arbitrary order (within their respective flights).

```python
from staircase import StaircaseTest, Setup, Task, Test, Teardown


class MyTest(StaircaseTest):
    @Setup
    def my_setup_step(self):
        return True, 'Successfully setup.'

    @Task(on_pass='my_setup_step')
    def prime_the_file(self):
        return True

    @Test
    def file_has_correct_contents(self):
        return True

    @Teardown(desc='Delete unprimed file', on_fail='prime_the_file')
    def delete_artifacts(self):
        try:
            self._delete('...')
            return True
        except:
            return False, 'Exception occurred'
```

### Running Tests
Tests can be run by instantiating the class and calling the `run` method.

```python
test = MyTest()
test.run()
```