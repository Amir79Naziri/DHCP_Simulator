import time
from threading import Thread, Semaphore


class Timer(Thread):

    def __init__(self, init_time):
        super().__init__()
        self.exception = None
        self.init_time = init_time
        self.lock = Semaphore()

    def run(self) -> None:
        try:
            while True:
                time.sleep(1)
                self.lock.acquire()
                self.init_time -= 1

                if self.init_time == 0:
                    self.lock.release()
                    raise TimeoutError('time out')
                elif self.init_time < 0:
                    self.lock.release()
                    return
        except TimeoutError as e:
            self.exception = e

    def wait(self):
        Thread.join(self)

        if self.exception:
            raise self.exception

    def kill(self):
        self.lock.acquire()
        self.init_time = -1
        self.lock.release()
