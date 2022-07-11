from staircase.logger import StaircaseLogger
from utils.strings import pad_to
from colorama import Fore
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

    def __init__(self, steps, step_directory, logger: StaircaseLogger):
        self.logger = logger
        self.steps = steps
        self.step_directory = step_directory

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
            self._print_result_line(step_counter, step, self.step_directory, print_substeps, display_mode, only_tests)
            step_counter += 1

    def _print_result_line(self, step_no, step, step_dir, substeps=True, display_mode=False, only_tests=False):
        stype = step_dir[step]['type'][1:]
        if only_tests and (stype != "Test" and stype != "Substep"):
            return

        passed = step_dir[step]['results'][0]
        step_return = step_dir[step]['results'][1]
        desc = step_dir[step]['desc']

        pf = f"SKIP" if display_mode or passed is None else f'{Fore.GREEN}PASS{Fore.RESET}' if passed else f'{Fore.RED}FAIL{Fore.RESET}'

        self.logger.info(
            f"{pad_to(str(step_no), StaircasePrinter.RES_NUM_PADDING)}{pad_to(stype, StaircasePrinter.STEP_TYPE_PADDING)}{pf}     {pad_to(step, StaircasePrinter.DESC_PADDING)}{desc}")

        if not passed and step_return is not None:
            self.logger.info(" " * (StaircasePrinter.RES_NUM_PADDING + StaircasePrinter.STEP_TYPE_PADDING - 1), f"{Fore.RED if passed is not None else ''}└{'x' if passed is not None else ''} {str(step_return)}{Fore.RESET if passed is not None else ''}")

        if substeps and len(self.step_directory[step]['substeps']) > 0:
            self._print_substeps(step_no, step)

    def _print_substeps(self, step_no, step_name):
        for i, substep in enumerate(self.step_directory[step_name]['substeps']):
            full_step_no = f" └{step_no}.{i + 1}"
            self._print_result_line(full_step_no, substep["name"], {substep["name"]: substep}, substeps=False, only_tests=True)
