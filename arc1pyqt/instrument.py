from recordtype import recordtype
from abc import abstractmethod
from serial import Serial, PARITY_EVEN, STOPBITS_ONE, serialutil
import numpy as np
import time


HWConfig = recordtype('HWConfig', ['words', 'bits', 'cycles', 'readmode', \
        'sessionmode', 'sneakpath', 'Vread'])


class Instrument:


    @abstractmethod
    def initialise(self):
        pass

    @abstractmethod
    def write_b(self, what):
        pass

    @abstractmethod
    def read_floats(self, how_many):
        pass

    @abstractmethod
    def readline(self):
        pass

    @abstractmethod
    def close(self):
        pass


class ArC1(Instrument):

    def __init__(self, port):
        """
        Initialise an ArC ONE connected at the specified ``port`` which must be
        a platform-specific string that points to a serial port. For example
        ``COM5`` on Windows, ``/dev/ttyACM0`` on Linux or
        ``/dev/tty.usbmodem12345`` on macOS.
        """
        self._port = Serial(port, baudrate=921600, timeout=7, \
                parity=PARITY_EVEN, stopbits=STOPBITS_ONE)

    def write(self, *args):
        """
        Write arguments to the serial port. This essentially wraps
        `serial.Serial`.
        """
        if self._port is not None:
            self._port.write(*args)

    def write_b(self, what):
        """
        Write an encodable stream to the serial port. Argument ``what``
        should implement __bytes__ for this to work.
        """
        if self._port is not None:
            self._port.write(what.encode())

    def reset(self):
        """
        Force an mbed reset
        """
        self._port.write_b("00\n")
        time.sleep(0.5)

    def initialise(self, config):
        """
        Initialise instrument with the given configuration which should be
        an instance of `HWConfig`.
        """
        self.write_b("00\n")
        time.sleep(1)

        self.write_b("0\n")
        self.write_b("%d\n" % config.cycles)
        self.write_b("%d\n" % config.words)
        self.write_b("%d\n" % config.bits)
        self.write_b("%d\n" % config.readmode)
        self.write_b("%d\n" % config.sessionmode)
        self.write_b("%d\n" % config.sneakpath)
        self.write_b("%f\n" % config.Vread)

        confirmation = 0
        confirmation = int(self._port.readline())

        if confirmation != 1:
            try:
                self._port.close()
            except serialutil.SerialException:
                pass
            self._port = None
            raise Exception("No confirmation received; port closed")

        self.write_b("01\n")
        self.write_b("%d\n" % config.readmode)
        self.write_b("%f\n" % config.Vread)

    def update_read(self, config):
        """
        Update read type and voltage from the supplied configuration. Rest
        of the arguments supplied by `config` will be ignored.
        """
        if self._port is None:
            return

        self.write_b("01\n")
        if config.Vread < 0 and config.readmode == 2:
            self.write_b("3\n")
        else:
            self.write_b("%d\n" % config.readmode)
        self.write_b("%f\n" % config.Vread)

    @property
    def port(self):
        """
        Exposes the wrapped serial port.
        """
        return self._port

    def close(self):
        """
        Disconnect from the tool closing the serial port.
        """
        self._port.close()
        self._port = None

    def read_floats(self, how_many):
        """
        Read a number of floating point numbers from the serial port.
        """
        if self._port is None:
            return

        while self._port.inWaiting() < how_many*4:
            pass

        values = self._port.read(size=how_many*4)
        buf = memoryview(values)

        return np.frombuffer(buf, dtype=np.float32)

    def readline(self):
        """
        Read a string up to a line terminator
        """
        if self._port is None:
            return

        return self._port.readline()
