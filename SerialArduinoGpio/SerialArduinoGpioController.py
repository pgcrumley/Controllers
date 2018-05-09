#!/usr/bin/python3
"""
MIT License

Copyright (c) 2018 Paul G Crumley

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

@author: pgcrumley@gmail.com

Control an Arduino which contains a sketch that reads simple commands
from the serial port and sets the GPIO pins (2-13) to either HIGH
(which is mode INPUT_PULLUP) or LOW (in OUTPUT mode).

The GPIOs can be read which returns a map of pin_number:value.

The current output state can be stored in EEPROM and will be loaded at
power-on / reset in the future.

This code must run as root to access the serial ports.
"""

import glob
import serial
import sys
import time

import RPi.GPIO as GPIO

DEBUG = 0

SERIAL_FILENAME_GLOBS = ('/dev/ttyUSB*', '/dev/ttyACM*')
PORT_SPEED = 115200
VALID_GPIO_PINS = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13}

NL = '\n'.encode('UTF-8')
READ_COMMAND = '?'.encode('UTF-8')
SAVE_COMMAND = '+'.encode('UTF-8')

class SerialArduinoGpioController:
    '''
    This class allows an Arduino on a Raspberry Pi serial port to used
    as a very basic GPIO device
    '''
        
    def __init__(self, serial_port):
        '''
        Try to create a controller using the passed serial port name.
        
        Names are a string of the form '/dev/ttyXXX' where XXX is a 
        string such as ACM# or USB#
        '''
        self._name = serial_port;
        self._port = serial.Serial(serial_port, PORT_SPEED)
        # give Arduino time to reset after serial open which causes a reset
        time.sleep(3)  
        values = self.get_pins()


    def get_name(self):
        '''
        return the serial device name
        '''
        return self._name
    
    
    def set_pin(self, pin, value):
        '''
        Set a GPIO pin to HIGH (INPUT mode with PULLUP) or LOW.
        '''
        if pin not in VALID_GPIO_PINS:
            raise ValueError('pin value of {} is not in {}'.format(pin, VALID_GPIO_PINS))
        if value:
            c = chr(ord('A') + pin)
        else:
            c = chr(ord('a') + pin)
        self._port.write(c.encode('UTF-8'))
        self._port.flush()
                        

    def get_pins(self):
        '''
        read the pin values and return a map of {pin:value}
        '''
        self._port.write(READ_COMMAND)
        self._port.flush()
        l = self._port.readline().decode('UTF-8')
        if DEBUG:
            print('line: "{}"'.format(l))  # don't need a \n

        result = {}
        for c in l:
            if c == 'c': result[2] = 0
            elif c == 'C': result[2] = 1
            elif c == 'd': result[3] = 0
            elif c == 'D': result[3] = 1
            elif c == 'e': result[4] = 0
            elif c == 'E': result[4] = 1
            elif c == 'f': result[5] = 0
            elif c == 'F': result[5] = 1
            elif c == 'g': result[6] = 0
            elif c == 'G': result[6] = 1
            elif c == 'h': result[7] = 0
            elif c == 'H': result[7] = 1
            elif c == 'i': result[8] = 0
            elif c == 'I': result[8] = 1
            elif c == 'j': result[9] = 0
            elif c == 'J': result[9] = 1
            elif c == 'k': result[10] = 0
            elif c == 'K': result[10] = 1
            elif c == 'l': result[11] = 0
            elif c == 'L': result[11] = 1
            elif c == 'm': result[12] = 0
            elif c == 'M': result[12] = 1
            elif c == 'n': result[13] = 0
            elif c == 'N': result[13] = 1
                    
        return result


    def save_pins(self):
        '''
        Save the current output pin values so they are reloaded at reset
        '''
        self._port.write(SAVE_COMMAND)
        self._port.flush()
        return



#
# main
#
if __name__ == "__main__":
    
    # this will hold the names of serial port devices which might have Arduino
    serial_devices = [] 
    for g in SERIAL_FILENAME_GLOBS:
        serial_devices.extend(glob.glob(g))
    if DEBUG:
        print('available devices include:  {}\n'.format(serial_devices))

    # get serial port access for each serial device
    controllers = set()
    for s in serial_devices:
        controllers.add(SerialArduinoGpioController(s))
    
    # Find the serial port(s) that holds the water pipe sensors
    for p in controllers:
        print('reading pins {}: {}\n'.format(p.get_name(), p.get_pins()))

    # Find the serial port(s) that holds the water pipe sensors
    for p in controllers:
        print('set pin 5 on {} LOW\n'.format(p.get_name(), p.set_pin(5, 0)))

    # Find the serial port(s) that holds the water pipe sensors
    for p in controllers:
        print('reading pins {}: {}\n'.format(p.get_name(), p.get_pins()))

    # Find the serial port(s) that holds the water pipe sensors
    for p in controllers:
        print('set pin 5 on {} HIGH\n'.format(p.get_name(), p.set_pin(5, 1)))

    # Find the serial port(s) that holds the water pipe sensors
    for p in controllers:
        print('reading pins {}: {}\n'.format(p.get_name(), p.get_pins()))

    # Find the serial port(s) that holds the water pipe sensors
    for p in controllers:
        print('saving reset state of {}\n'.format(p.get_name(), p.save_pins()))
