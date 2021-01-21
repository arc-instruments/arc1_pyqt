from dataclasses import dataclass
from abc import abstractmethod
from serial import Serial, PARITY_EVEN, STOPBITS_ONE, serialutil
import numpy as np
import time
import struct


@dataclass
class HWConfig:
    words: int = 32
    bits: int = 32
    cycles: int = 50
    readmode: int = 2
    sessionmode: int = 0
    sneakpath: int = 1
    Vread: float = 0.5


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
    def queue_select(self, w, b):
        pass

    @abstractmethod
    def select(self, w, b):
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

        # current firmware version. It's not available unless
        # explicitly queried. When that's done the value is cached
        # until force reloaded
        # special value (-1, -1) means that version reporting is
        # not supported by current firmware
        self._firmware = None

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

    def queue_select(self, word, bit):
        """
        Send a word-/bitline pair to the uC. Note that this does not actively
        select a device, as this is expected to be done separately from the
        module loaded just before.
        """
        self.write_b("%d\n" % int(word))
        self.write_b("%d\n" % int(bit))

    def select(self, word, bit):
        """
        Actively select a device. This will close the specified crosspoint
        """
        self.write_b("02\n")
        self.queue_select(word, bit)

    def read_one(self, word, bit):
        """
        Read resistance of device located at word, bit
        """
        self.write_b("1\n")
        self.queue_select(word, bit)

        return float(self.read_floats(1))

    def pulseread_one(self, word, bit, voltage, pw):
        """
        Pulse a device at `word × bit` and read its value
        """
        self.write_b("3\n")
        self.queue_select(word, bit)

        self.write_b("%f\n" % voltage)
        self.write_b("%f\n" % pw)

        return float(self.read_floats(1))

    def pulse_active(self, voltage, pw):
        """
        Pulse currently selected device. Selection must be previously
        done with `arc1pyqt.instrument.ArC1.select`.
        """
        self.write_b("04\n")
        self.write_b("%f\n" % voltage)
        self.write_b("%f\n" % pw)

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

    def firmware_version(self, force=False):

        if (not force) and (self._firmware is not None):
            return self._firmware

        timeout = self._port.timeout
        try:
            self._port.timeout = 2
            time.sleep(0.2)
            self._port.write(b"999\n")
            data = self._port.read(size=4)
            (major, minor) = struct.unpack("2H", data)
            ret = (major, minor)
        except Exception as exc:
            ret = (-1, -1)

        # restore timeout
        self._port.timeout = timeout
        self._firmware = ret

        return ret

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
        if self._port is None:
            return
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
