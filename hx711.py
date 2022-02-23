#!/usr/bin/python3
import statistics
import time
import RPi.GPIO as GPIO


class HX711:
    def __init__(self, dout=5, pd_sck=6, gain=128, bitsToRead=24):
        self._PD_SCK = pd_sck
        self._DOUT = dout

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.PD_SCK, GPIO.OUT)
        GPIO.setup(self.DOUT, GPIO.IN)

        # The value returned by the hx711 that corresponds to your
        # reference unit AFTER dividing by the SCALE.
        self._REFERENCE_UNIT = 1

        self._GAIN = 0
        self._OFFSET = 1
        self._lastVal = 0
        self._bitsToRead = bitsToRead
        self._twosComplementThreshold = 1 << (bitsToRead-1)
        self._twosComplementOffset = -(1 << (bitsToRead))
        self.setGain(gain)
        self.read()

    ### define property start ###

    def PD_SCK():
        doc = "The PD_SCK property."
        def fget(self):
            return self._PD_SCK
        def fset(self, value):
            self._PD_SCK = value
        def fdel(self):
            del self._PD_SCK
        return locals()
    PD_SCK = property(**PD_SCK())

    def DOUT():
        doc = "The DOUT property."
        def fget(self):
            return self._DOUT
        def fset(self, value):
            self._DOUT = value
        def fdel(self):
            del self._DOUT
        return locals()
    DOUT = property(**DOUT())

    def REFERENCE_UNIT():
        doc = "The REFERENCE_UNIT property."
        def fget(self):
            return self._REFERENCE_UNIT
        def fset(self, value):
            self._REFERENCE_UNIT = value
        def fdel(self):
            del self._REFERENCE_UNIT
        return locals()
    REFERENCE_UNIT = property(**REFERENCE_UNIT())

    def GAIN():
        doc = "The GAIN property."
        def fget(self):
            return self._GAIN
        def fset(self, value):
            self._GAIN = value
        def fdel(self):
            del self._GAIN
        return locals()
    GAIN = property(**GAIN())

    def OFFSET():
        doc = "The OFFSET property."
        def fget(self):
            return self._OFFSET
        def fset(self, value):
            self._OFFSET = value
        def fdel(self):
            del self._OFFSET
        return locals()
    OFFSET = property(**OFFSET())

    def lastVal():
        doc = "The lastVal property."
        def fget(self):
            return self._lastVal
        def fset(self, value):
            self._lastVal = value
        def fdel(self):
            del self._lastVal
        return locals()
    lastVal = property(**lastVal())

    def bitsToRead():
        doc = "The bitsToRead property."
        def fget(self):
            return self._bitsToRead
        def fset(self, value):
            self._bitsToRead = value
        def fdel(self):
            del self._bitsToRead
        return locals()
    bitsToRead = property(**bitsToRead())

    def twosComplementThreshold():
        doc = "The twosComplementThreshold property."
        def fget(self):
            return self._twosComplementThreshold
        def fset(self, value):
            self._twosComplementThreshold = value
        def fdel(self):
            del self._twosComplementThreshold
        return locals()
    twosComplementThreshold = property(**twosComplementThreshold())

    def twosComplementOffset():
        doc = "The twosComplementOffset property."
        def fget(self):
            return self._twosComplementOffset
        def fset(self, value):
            self._twosComplementOffset = value
        def fdel(self):
            del self._twosComplementOffset
        return locals()
    twosComplementOffset = property(**twosComplementOffset())

    ### define property end ###

    def isReady(self):
        return GPIO.input(self.DOUT) == 0

    def setGain(self, gain):
        if gain is 128:
            self.GAIN = 1
        elif gain is 64:
            self.GAIN = 3
        elif gain is 32:
            self.GAIN = 2

        GPIO.output(self.PD_SCK, False)
        self.read()

    def waitForReady(self):
        while not self.isReady():
            pass

    def correctTwosComplement(self, unsignedValue):
        if unsignedValue >= self.twosComplementThreshold:
            return unsignedValue + self.twosComplementOffset
        else:
            return unsignedValue

    def read(self):
        # hx711モジュールの出力の仕様に関連すると思われる。
        # 内部でACDがAD変換した値が、バッファに入ってるとかそんなとこでは？
        # そんで24bitの値を、CLKに応じて1bitずつ吐き出してきて、それは2の補数になってるから、こっちで解釈し直してやる。
        self.waitForReady()

        unsignedValue = 0
        for i in range(0, self.bitsToRead):
            GPIO.output(self.PD_SCK, True)
            bitValue = GPIO.input(self.DOUT)
            GPIO.output(self.PD_SCK, False)
            unsignedValue = unsignedValue << 1
            unsignedValue = unsignedValue | bitValue

        # 多分これもhx711の仕様に対応したコード
        # ほしいゲインの回数だけCLKのONOFF切り替わりがあると設定されるみたいな。
        # set channel and gain factor for next reading
        for i in range(self.GAIN):
            GPIO.output(self.PD_SCK, True)
            GPIO.output(self.PD_SCK, False)

        return self.correctTwosComplement(unsignedValue)

    def getValue(self):
        return self.read() - self.OFFSET

    def getWeight(self):
        value = self.getValue()
        value /= self.REFERENCE_UNIT
        return value

    def tare(self, times=25):
        reference_unit = self.REFERENCE_UNIT
        self.setReferenceUnit(1)

        # remove spikes
        cut = times//5
        values = sorted([self.read() for i in range(times)])[cut:-cut]
        offset = statistics.mean(values)

        # self.setOffset(offset)

        self.setReferenceUnit(reference_unit)

    def setOffset(self, offset):
        self.OFFSET = offset


    def setReferenceUnit(self, reference_unit):
        self.REFERENCE_UNIT = reference_unit

    # HX711 datasheet states that setting the PDA_CLOCK pin on high
    # for a more than 60 microseconds would power off the chip.
    # I used 100 microseconds, just in case.
    # I've found it is good practice to reset the hx711 if it wasn't used
    # for more than a few seconds.
    def powerDown(self):
        GPIO.output(self.PD_SCK, False)
        GPIO.output(self.PD_SCK, True)
        time.sleep(0.0001)

    def powerUp(self):
        GPIO.output(self.PD_SCK, False)
        time.sleep(0.0001)

    def reset(self):
        self.powerDown()
        self.powerUp()
