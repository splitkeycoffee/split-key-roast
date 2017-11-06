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
        self.exit = Event()

    def run(self):
        while not self._q.empty():
            self._config = self._q.get()

        while not self.exit.is_set():
            self._log.debug("Thread pulse")
            self._cb({'config': self._config})
            time.sleep(1)

    def shutdown(self):
        """Register a shutdown event."""
        self._log.debug("Shutdown initiated")
        self.exit.set()
