from staircase import StaircaseTest, Task, Setup, Teardown, Test, Substep, StaircaseLogger


class DatTest(StaircaseTest):
    @Setup(desc='Open files')
    def open_files(self):
        return True, 'files opened'

    @Setup(desc="Read dat file", on_pass='open_files')
    def read_dat(self):
        return True, 3

    @Task(desc='Process dat file', on_pass='threshold')
    def loop_dat2(self):
        return True, ['lines']

    @Test(desc='Process dat file', on_pass='loop_dat2')
    def loop_dat(self):

        @Substep(desc='Test for things in a for loop')
        def do_some_substep(item):
            if item:
                return True, 'Looks good to me'
            else:
                return False, 'What the hell'

        for i in range(5):
            do_some_substep(i)

        @Substep(desc="This is a second substep")
        def second_substep():
            self.logger.info("SECOND")
            return True, "Wowza"

        second_substep()

        return True, "Passed with flying colors."

    @Test(desc="Make sure that each record has integers.", on_pass=['threshold', 'loop_dat'])
    def all_have_int(self):
        for line in self.get_return_from_step('loop_dat'):
            if not isinstance(line, int):
                return False, "Found a non-integer value on line 34."
        return True, "Passed"

    @Test(desc="Dat errors for NULLs are < 30%")
    def threshold(self):
        return True, "The thresshold of dat errors of 30% was exceeded. Got 34%."

    @Teardown(desc="Closing files.")
    def close_files(self):
        print("RUNNING CLOSE")
        return True, True


def my_logger(*args):
    print(*args, flush=True)


class ExampleLogger(StaircaseLogger):
    def info(self, *args, **kwargs):
        print(*args, **kwargs)
        # EX: logAndPrint("info", *args, **kwargs)

    def error(self, *args, **kwargs):
        print("CUSTOM ERROR", *args, **kwargs)

if __name__ == "__main__":
    t = DatTest(logger=ExampleLogger())
    print(">>>>>>>>>>>>>>>> DISPLAY")
    t.display()

    print("\n\n\n>>>>>>>>>>>>>>>> STANDARD RUN")
    t.run()

    print("\n\n\n>>>>>>>>>>>>>>>> WITH START AND END")
    t.run(first_step=2, last_step=5)

    print("\n\n\n>>>>>>>>>>>>>>>> ONLY SHOW TESTS")
    t.run(last_step=5, show_all=False)
