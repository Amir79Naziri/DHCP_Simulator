import time
from threading import Thread


class Timer(Thread):

    def __init__(self, init_time):
        super().__init__()
        self.exception = None
        self.init_time = init_time

    def run(self) -> None:
        try:
            while True:
                time.sleep(1)
                self.init_time -= 1
                if self.init_time <= 0:
                    raise TimeoutError('time out')
        except TimeoutError as e:
            self.exception = e

    def wait(self):
        Thread.join(self)

        if self.exception:
            raise self.exception
