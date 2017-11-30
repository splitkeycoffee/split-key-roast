from threading import Thread, Event
import time


class MockProcess(Thread):

    """Mock up a thread to play around with."""

    def __init__(self, config, q, logger, callback=None):
        Thread.__init__(self)
        self._config = config
        self._cb = callback
        self._log = logger
        self._q = q
        self.cooldown = Event()
        self.exit = Event()

    def run(self):
        import random
        self._config['environment_temp'] = 450
        self._config['bean_temp'] = 100
        while not self._q.empty():
            self._config = self._q.get()

        while not self.exit.is_set():
            self._log.debug("Thread pulse")
            # self._config['environment_temp'] -= random.uniform(0, 1)
            # self._config['bean_temp'] += random.uniform(0, 1)
            self._cb(self._config)  # This gives us a way to know when to read

            if self.cooldown.is_set():
                self._log.debug("Cool down process triggered")
                self._config['drum_motor'] = 0
                self._config['heater'] = 0
                self._config['solenoid'] = 1
                self._config['cooling_motor'] = 1
                self._config['main_fan'] = 10

            time.sleep(.5)

    def drop(self):
        """Register a drop event to begin the cool-down process.

        :returns: None
        """
        self._log.debug("Dropping the coffee")
        self.cooldown.set()

    def shutdown(self):
        """Register a shutdown event."""
        self._log.debug("Shutdown initiated")
        self.exit.set()
