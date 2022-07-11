from staircase import StaircaseTest, Setup, Task, Teardown, Substep


class DemoTest(StaircaseTest):
    @Setup(desc='opens a data file and stores its contents')
    def open_and_store(self):
        return True

    @Setup(desc='connects to a database')
    def connect_to_db(self):
        return True

    @Setup(desc='reads expected filename and opens file for write')
    def read_and_open_file(self):
        return True

    @Task(desc='processing...')
    def process_1(self):
        return True

    @Task(desc='processing again...')
    def process_2(self):
        return False

    @Task(desc='cleanup of processing failure', on_fail='process_2')
    def cleanup_process_fail(self):
        # Fix some conditions...
        # self.restart()
        return True

    @Task(desc='even more processing', on_pass='process_2')
    def process_files(self):
        return False, 'Yeah this messed up'

    @Task(on_pass=('process_files', 'process_1', 'process_2'))
    def final_processing(self):
        @Substep(desc='substep for success of process_files', on_pass='process_files')
        def process_a():
            return True

        @Substep(desc='substep for success of process_1 and process_2', on_pass=('process_1', 'process_2'))
        def process_b():
            return True

        process_a()
        process_b()

        return True

    @Teardown(desc='close the db connection', on_pass='$ALL')
    def close_db_conn(self):
        return True

    @Teardown(desc='generate a report if all steps pass')
    def generate_report(self):
        return True


if __name__ == "__main__":
    t = DemoTest()
    t.run()
