#! /usr/bin/sh python3

import RPi.GPIO as gpio
import time


class TempHumiditySensor(object):

    def __init__(self, pin):
        self.pin = pin

        print('RPi information:')
        print(gpio.RPI_INFO)

        print(f'GPIO version: {gpio.VERSION}')

        # init the board/data pin
        gpio.setmode(gpio.BOARD)
        # gpio.setup(self.pin, gpio.IN, pull_up_down=gpio.PUD_UP)

    def read(self):
        self.sample()
        self.parse()

    def confirm(self, microseconds, level):
        for i in range(microseconds // 10 + 1):
            if gpio.input(self.pin) != level:
                return False
            else:
                time.sleep(0.00001)

        return True

    def bits2byte(self, data):
        data = map(str, data)
        return int(''.join(data), 2)

    def sample(self):
        self.data = []
        # syn
        gpio.setup(self.pin, gpio.OUT)
        gpio.output(self.pin, 0)
        # must wait at least 18ms
        time.sleep(0.02)
        gpio.output(self.pin, 1)
        # must wait "20-40" microseconds
        time.sleep(30e-6)
        # prep for input
        gpio.setup(self.pin, gpio.IN, pull_up_down=gpio.PUD_DOWN)

        # ack
        if not self.confirm(80, 0):
            raise RuntimeError('DHT did not ack properly - low')
        if not self.confirm(80, 1):
            raise RuntimeError('DHT did not ack properly - high')

        # data transmission begins
        # this is bit-by-bit
        # there's a 50microsecond period at 0, then either:
        # 26-28microseconds at 1 == 0
        # 70 microseconds at 1 == 1
        # then it starts again

        for _ in range(40):
            if not self.confirm(50, 0):
                raise RuntimeError('DHT start is wrong')

            read_successful = False
            ms_wait = 0
            for i in range(8):
                if gpio.input(self.pin) != 1:
                    read_successful = True
                    break
                ms_wait += 10
                time.sleep(10e-6)

            if not read_successful:
                raise RuntimeError('DHT reading unsuccessful')
            self.data.append(int(ms_wait > 30))

        # confirm end of transmission
        if not self.confirm(50, 0):
            raise RuntimeError('DHT transmission finished unsuccessfully')

    def parse(self, data):
        humid_1 = self.bits2byte(data[:8])
        humid_2 = self.bits2byte(data[8:16])
        temp_1 = self.bits2byte(data[16:24])
        temp_2 = self.bits2byte(data[24:32])
        checksum = self.bits2byte(data[32:])

        calculated_checksum = humid_1 + humid_2 + temp_1 + temp_2

        if checksum != calculated_checksum:
            error_str = f'Readings: {humid_1}, {humid_2}, {temp_1}, {temp_2}'
            raise RuntimeError(error_str)
        self.temp = temp_1
        self.humidity = humid_1

    def __enter__(self):
        return self

    def __exit__(self, *args):
        gpio.cleanup()


if __name__ == '__main__':
    with TempHumiditySensor(pin=36) as sensor:
        # test parsing:
        # 0011 0011 0000 0000 0001 0110 0000 0000 0100 1001
        # 22c, 51%
        # 0011 0010 0000 0000 0001 0111 0000 0000 0100 1001
        # 23c, 50%

        data = [0, 0, 1, 1,
                0, 0, 1, 1,
                0, 0, 0, 0,
                0, 0, 0, 0,
                0, 0, 0, 1,
                0, 1, 1, 0,
                0, 0, 0, 0,
                0, 0, 0, 0,
                0, 1, 0, 0,
                1, 0, 0, 1,
                ]
        sensor.parse(data)
        assert sensor.temp == 22
        assert sensor.humidity == 51

        data = [0, 0, 1, 1,
                0, 0, 1, 0,
                0, 0, 0, 0,
                0, 0, 0, 0,
                0, 0, 0, 1,
                0, 1, 1, 1,
                0, 0, 0, 0,
                0, 0, 0, 0,
                0, 1, 0, 0,
                1, 0, 0, 1,
                ]
        sensor.parse(data)
        assert sensor.temp == 23
        assert sensor.humidity == 50
