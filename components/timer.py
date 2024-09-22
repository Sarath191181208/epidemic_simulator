from collections.abc import Callable
import time

SECOND = 1
MINUTE = 60 

class Timer():
    """
        Creates a timer to call a function periodically
        Methods:
        - update : should be in game loop to update the timer
        - start_timer : starts the timer
        - stop_timer : stops the timer 
    """

    def __init__(self, time: float, func: Callable[[], None] | None = None, loop: bool = False) -> None:
        """
            Parameters:
                - time: amount of time in seconds
                - func: the function that needs to be called
                - loop: should repeat the function 
        """
        self.time = time
        self.start_time = 0
        self.start = False
        self.func = func
        self.loop = loop

    @property
    def is_running(self) -> bool:
        return self.start

    def update(self):
        if self.start:
            current = time.time()
            if abs(current-self.start_time) >= self.time:
                self.reset()

    def start_timer(self):
        self.start = True
        self.start_time = time.time()

    def reset(self):
        if self.func is not None:
            self.func()
        if self.start and self.loop:
            self.start_timer()
        else:
            self.stop()

    def stop(self):
        self.start = False
        self.start_time = 0
