from staircase.logger import StaircaseLogger
from staircase.types import StepRegistration
from utils.strings import pad_to
from colorama import Fore
from typing import Dict
from enum import Enum


class StaircasePrintMode(Enum):
    SUMMARY = 1
    DISPLAY = 2
    RESULTS = 3


class StaircasePrinter:
    HEADER_WIDTH = 100
    RES_NUM_PADDING = 10
    STEP_TYPE_PADDING = 10
    DESC_PADDING = 30

    def __init__(self, steps, step_registry: Dict[str, StepRegistration], logger: StaircaseLogger):
        self.logger = logger
        self.steps = steps
        self.step_registry: Dict[str, StepRegistration] = step_registry

    def print(self, mode=StaircasePrintMode.SUMMARY):
        match mode:
            case StaircasePrintMode.SUMMARY:
                self._print_header("Staircase Execution Summary")
                self._print_table_cap()
                self._print_steps(print_substeps=True)
            case StaircasePrintMode.DISPLAY:
                self._print_header("Staircase Execution Preview")
                self._print_table_cap()
                self._print_steps(print_substeps=False, display_mode=True)
            case StaircasePrintMode.RESULTS:
                self._print_header("Staircase Test Results")
                self._print_table_cap()
                self._print_steps(print_substeps=True, only_tests=True)
            case _:
                self.logger.error(f"Staircase print mode not recognized. Mode: {mode}")

    def _print_table_cap(self):
        self.logger.info(
            f"\n{pad_to('STEP #', StaircasePrinter.RES_NUM_PADDING)}{pad_to('TYPE', StaircasePrinter.STEP_TYPE_PADDING)}{'STATUS'}   {pad_to('NAME', StaircasePrinter.DESC_PADDING)}{'DESCRIPTION'}")
        self.logger.info("-"*StaircasePrinter.HEADER_WIDTH)

    def _print_header(self, content):
        cap = f"*" * StaircasePrinter.HEADER_WIDTH
        mid_whitespace = " " * (int((StaircasePrinter.HEADER_WIDTH - len(content)) / 2) - 1)
        mid = f"*{mid_whitespace}{content}{mid_whitespace}{'' if (StaircasePrinter.HEADER_WIDTH - len(content)) % 2 == 0 else ' '}*"
        self.logger.info(cap)
        self.logger.info(mid)
        self.logger.info(cap)

    def _print_steps(self, print_substeps, display_mode=False, only_tests=False):
        step_counter = 1

        for step in self.steps:
            self._print_result_line(step_counter, step, self.step_registry, print_substeps, display_mode, only_tests)
            step_counter += 1

    def _print_result_line(self, step_no, step, step_registry: Dict[str, StepRegistration], substeps=True, display_mode=False, only_tests=False):
        stype = step_registry[step].step_type[1:]
        if only_tests and (stype != "Test" and stype != "Substep"):
            return

        passed = step_registry[step].results[0]
        step_return = step_registry[step].results[1]
        desc = step_registry[step].desc

        pf = f"SKIP" if display_mode or passed is None else f'{Fore.GREEN}PASS{Fore.RESET}' if passed else f'{Fore.RED}FAIL{Fore.RESET}'

        self.logger.info(
            f"{pad_to(str(step_no), StaircasePrinter.RES_NUM_PADDING)}{pad_to(stype, StaircasePrinter.STEP_TYPE_PADDING)}{pf}     {pad_to(step, StaircasePrinter.DESC_PADDING)}{desc}")

        if not passed and step_return is not None:
            self.logger.info(" " * (StaircasePrinter.RES_NUM_PADDING + StaircasePrinter.STEP_TYPE_PADDING - 1), f"{Fore.RED if passed is not None else ''}└{'x' if passed is not None else ''} {str(step_return)}{Fore.RESET if passed is not None else ''}")

        if substeps and len(self.step_registry[step].substeps) > 0:
            self._print_substeps(step_no, step)

    def _print_substeps(self, step_no, step_name):
        for i, substep in enumerate(self.step_registry[step_name].substeps):
            full_step_no = f" └{step_no}.{i + 1}"
            self._print_result_line(full_step_no, substep.substep_name, {substep.substep_name: substep}, substeps=False, only_tests=True)
