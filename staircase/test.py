from staircase.decorators import _Task, _Setup, _Test, _Teardown
from staircase.logger import StaircaseLogger, DefaultLogger
from staircase import StaircasePrinter, StaircasePrintMode
from staircase.types import StepRegistration
from utils.classes import get_members
from typing_extensions import final
from typing import Dict

"""
  █████████  ███████████   █████████   █████ ███████████     █████████    █████████    █████████  ██████████
 ███░░░░░███░█░░░███░░░█  ███░░░░░███ ░░███ ░░███░░░░░███   ███░░░░░███  ███░░░░░███  ███░░░░░███░░███░░░░░█
░███    ░░░ ░   ░███  ░  ░███    ░███  ░███  ░███    ░███  ███     ░░░  ░███    ░███ ░███    ░░░  ░███  █ ░ 
░░█████████     ░███     ░███████████  ░███  ░██████████  ░███          ░███████████ ░░█████████  ░██████   
 ░░░░░░░░███    ░███     ░███░░░░░███  ░███  ░███░░░░░███ ░███          ░███░░░░░███  ░░░░░░░░███ ░███░░█   
 ███    ░███    ░███     ░███    ░███  ░███  ░███    ░███ ░░███     ███ ░███    ░███  ███    ░███ ░███ ░   █
░░█████████     █████    █████   █████ █████ █████   █████ ░░█████████  █████   █████░░█████████  ██████████
 ░░░░░░░░░     ░░░░░    ░░░░░   ░░░░░ ░░░░░ ░░░░░   ░░░░░   ░░░░░░░░░  ░░░░░   ░░░░░  ░░░░░░░░░  ░░░░░░░░░░ 
                                                                                                            

                                               @teardown  ┏━━━━━━━━━━━━━━
                                             @teardown  ┏━┛ Flight: Teardown
                                           @teardown  ┏━┛
                                      @Task   ┏━━━━━━━┛━━━━━━━━━━
                                    @Test   ┏━┛ Flight: Main
                                  @Task   ┏━┛
                                @Test   ┏━┛
                          @Setup  ┏━━━━━┛━━━━━━━━━━
                        @Setup  ┏━┛ Flight: Setup


Staircase is a testing framework, built to be an intuitive way to layer testing functionality over an existing
program. To implement Staircase, decorators are placed above the function definitions in the script
that describe what the function is used for and in what step it will be called.

A cohesive set of testing functionality, which is divided into flights of stairs. Flights hold a group of steps.
There are three flights:
- Setup: contains any functionality needed to prepare for the main steps.
- Main: contains the majority of the program, and is composed further of Tasks and Tests
- Teardown: contains any functions that close the program or cleanup after testing activities (including failures)

The flights are then subdivided into steps and substeps. Steps are individual functions, and substeps are
functions defined within those functions. Steps and substeps are named for what flight that they are in. (i.e. setup
steps are contained in the setup flight).

The exception is the main flight, which only holds task and test steps. In this case these steps can be interwoven 
within the flight.

Each step takes the following parameters:
- desc: A short description of what the function does.
- on_pass: A list of step names. It will wait for these steps to pass in order to run this step.
- on_fail: A list of step names. It will wait for these steps to fail in order to run this step.

The steps are run in an arbitrary order unless the on_pass or on_fail parameters are specified.
"""


class ResetSignal(Exception):
    pass

class MaxResetsExceeded(Exception):
    pass


class StaircaseTest:
    RESULT_FORMAT = {
        "step_no_padding": 6
    }

    def __init__(self, logger: StaircaseLogger = None, restart_retries=1):
        if self.__class__.__name__ == "StaircaseTest":
            raise Exception("StaircaseTest cannot be instantiated on its own, it must be subclassed by the test class.")

        if logger is None:
            self.logger = DefaultLogger.get_default()
        elif isinstance(logger, StaircaseLogger):
            self.logger = logger
        else:
            raise Exception("Invalid logger. Must be a subclass of StaircaseLogger.")

        self.max_restart_retries = restart_retries
        self.retries = 0

        self.ordered_list = []
        self.run_args = {}

        self.step_registry: Dict[str, StepRegistration] = {}
        self._register_steps()

        self._setup_steps, self._main_steps, self._teardown_steps = self._get_sorted_steps()
        self.ordered_list = self._setup_steps + self._main_steps + self._teardown_steps

        self._assign_indices_to_directory()

    def __repr__(self):
        return 'StaircaseTest'

    @final
    def run(self, first_step=1, last_step=None, show_all=True):
        if last_step is None:
            last_step = len(self.ordered_list)

        self.run_args = {
            'first_step': first_step,
            'last_step': last_step,
            'show_all': show_all,
        }

        self._check_first_last(first_step, last_step)

        self._reset()

        try:
            self._run_flight(first_step, last_step, self._setup_steps)
            self._run_flight(first_step, last_step, self._main_steps)
            self._run_flight(first_step, last_step, self._teardown_steps)

            self._log_test_results(show_all)
        except ResetSignal:
            self.run(**self.run_args)

    def display(self):
        printer = StaircasePrinter(self.ordered_list, self.step_registry, self.logger)
        printer.print(StaircasePrintMode.DISPLAY)

    def _reset(self):
        # Clear step and substep results
        for step in self.step_registry:
            self.step_registry[step].results = (None, None)
            self.step_registry[step].substeps = []

    def _run_flight(self, first_step, last_step, steps):
        for step in steps:
            if self._step_is_qualified_to_run(first_step, last_step, step):
                self._call_step_function(step)

    def _step_is_qualified_to_run(self, first_step, last_step, step):
        in_range = first_step <= self.step_registry[step].step_index <= last_step

        # Always run if setup or teardown (contingent on dependencies being met of course)
        is_setup_teardown = self.step_registry[step].step_type == '_Setup' \
                            or self.step_registry[step].step_type == '_Teardown'
        return in_range or is_setup_teardown

    def _call_step_function(self, step_name):
        try:
            self._run_step(step_name)

        except MaxResetsExceeded as max_resets_exception:
            self.step_registry[step_name].results = (False, str(max_resets_exception))

        except Exception as e:
            self.logger.error(f'An exception occurred while executing step {step_name}. {str(e)}')
            raise e

        results = self.get_step_results(step_name)
        if results == (None, None):
            raise Exception(f'Step {step_name} requires a success value of the form (pass/fail [bool], result [any])')

    def _run_step(self, step_name):
        if self._check_pre_requisites_for_step(step_name):
            self.step_registry[step_name].method_reference(self)
        else:
            self.step_registry[step_name].results = (None, "Did not run due to step dependency check failure.")

    def _check_pre_requisites_for_step(self, step):
        on_pass = self.step_registry[step].on_pass
        on_fail = self.step_registry[step].on_fail

        if on_pass:
            dependencies_have_passed = []
            for dep in on_pass:
                dependencies_have_passed.append(self.step_registry[dep].results[0])
            return all(dependencies_have_passed)

        elif on_fail:
            dependencies_have_failed = []
            for dep in on_fail:
                dependencies_have_failed.append(not self.step_registry[dep].results[0])
            return all(dependencies_have_failed)

        return True

    def _register_steps(self):
        for step_name in get_members(self):
            for step in self._get_flight_classes():
                if isinstance(getattr(self, step_name), step):
                    self.register_step(step.__name__, -1,
                                       step_name,
                                       getattr(self, step_name),
                                       self._get_attr_for_step(step_name, 'on_pass'),
                                       self._get_attr_for_step(step_name, 'on_fail'),
                                       getattr(self, step_name).desc)
                    break

        for registered_step in self.step_registry:
            on_pass = self.step_registry[registered_step].on_pass
            on_fail = self.step_registry[registered_step].on_fail

            if on_pass == ('$ALL',):
                all_steps = tuple([])
                for step in self.step_registry:
                    if step != registered_step:
                        all_steps += (step,)
                on_pass = all_steps

            if on_fail == ('$ALL',):
                all_steps = tuple([])
                for step in self.step_registry:
                    if step != registered_step:
                        all_steps += (step,)
                on_fail = all_steps

            self.step_registry[registered_step].on_pass = on_pass
            self.step_registry[registered_step].on_fail = on_fail

    def _get_flight_classes(self):
        return [
            _Setup,
            _Task,
            _Test,
            _Teardown
        ]

    def register_step(self, stype, index, name, ref, on_pass, on_fail, desc):
        self.step_registry[name] = StepRegistration(
            step_type=stype,
            step_index=index,
            on_pass=on_pass,
            on_fail=on_fail,
            desc=desc,
            method_reference=ref,
        )

    def _get_attr_for_step(self, step_name: str, attr_name: str):
        res = None
        try:
            res = getattr(getattr(self, step_name), attr_name)
        except AttributeError:
            pass

        return res

    def get_return_from_step(self, step):
        results = self.step_registry[step].results
        if results == (None, None):
            raise Exception(f"Error attempting to fetch results from step {step}, which has not yet run.")
        return results[1]

    def step_passed(self, step):
        results = self.step_registry[step].results
        if results == (None, None):
            raise Exception(f"Error attempting to fetch pass status from step {step}, which has not yet run.")

        return results[0]

    def get_step_results(self, step):
        results = self.step_registry[step].results
        if results == (None, None):
            raise Exception(f"Error attempting to fetch results from step {step}, which has not yet run.")
        return results

    def _log_test_results(self, show_all):
        printer = StaircasePrinter(self.ordered_list, self.step_registry, self.logger)
        printer.print(StaircasePrintMode.SUMMARY if show_all else StaircasePrintMode.RESULTS)

    def _get_sorted_steps(self):
        ordered_list = []

        try:
            for step_name in self.step_registry:
                ordered_list = self._recur_step_dependencies(step_name, ordered_list)
        except Exception as e:
            if 'recursion depth' in str(e):
                raise Exception(f"Dependency loop found between steps on_fail and/or on_pass for step {step_name}.")
            raise Exception(f'An error occurred while ordering steps. {str(e)}')

        setup_steps = []
        task_steps = []
        teardown_steps = []

        for step_name in ordered_list:
            match self.step_registry[step_name].step_type:
                case '_Setup':
                    setup_steps.append(step_name)
                case '_Task':
                    task_steps.append(step_name)
                case '_Test':
                    task_steps.append(step_name)
                case '_Teardown':
                    teardown_steps.append(step_name)
                case _:
                    raise Exception(
                        f'An error occurred while ordering steps. Step {self.step_registry[step_name]} with type {self.step_registry[step_name].step_type} is invalid.')

        return setup_steps, task_steps, teardown_steps

    def _recur_step_dependencies(self, node, ordered_list):
        if self.step_registry[node].on_pass:
            for pointer in self.step_registry[node].on_pass:
                self._recur_step_dependencies(pointer, ordered_list)

        if self.step_registry[node].on_fail:
            for pointer in self.step_registry[node].on_fail:
                self._recur_step_dependencies(pointer, ordered_list)

        if node not in ordered_list:
            ordered_list.append(node)

        return ordered_list

    def _assign_indices_to_directory(self):
        for index, step in enumerate(self.ordered_list, 1):
            self.step_registry[step].step_index = index

    def _check_first_last(self, first_step, last_step):
        if first_step > last_step or first_step < 1 or last_step > len(self.ordered_list):
            raise Exception(f'The first step function comes after the last step function listed.')
        else:
            return True

    def restart(self):
        if self.retries > self.max_restart_retries:
            raise MaxResetsExceeded('Can not restart test: Max retries exceeded.')

        self.logger.info('Attempting to restart the test...')
        self.retries += 1

        raise ResetSignal('Attempting to restart...')
