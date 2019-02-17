#! env python
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

This code must run as root to access the serial ports on some systems.
"""

import sys
import time

import serial
import serial.tools.list_ports

DEBUG = 0

# remove these devices from list -- this list is ad hoc
# probably best to put the port names on the command line
FILTERED_OUT_DEVICES = ['COM1', 'COM2', # windows seems to use these
                        'COM3', 'COM4', # windows seems to use these
                        'COM5', 'COM6', # windows seems to use these
                        'COM7', 'COM8', # windows seems to use these
                        '/dev/ttyAMA0'] # raspberry pi console

PORT_SPEED = 115200
TIMEOUT_IN_SEC = 2.0
RESET_TIME_IN_SEC = 3.0
VALID_GPIO_PINS = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13}

NL = '\n'.encode('UTF-8')
READ_COMMAND = '?'.encode('UTF-8')
SAVE_COMMAND = '+'.encode('UTF-8')
VERSION_COMMAND = '`'.encode('UTF-8')
GET_ANALOG_PIN_COMMAND = ['0'.encode('UTF-8'),
                          '1'.encode('UTF-8'),
                          '2'.encode('UTF-8'),
                          '3'.encode('UTF-8'),
                          '4'.encode('UTF-8'),
                          '5'.encode('UTF-8'),
                          '6'.encode('UTF-8'),
                          '7'.encode('UTF-8')
                          ]
class SerialArduinoGpioController:
    '''
    This class allows an Arduino on a Raspberry Pi serial port to used
    as a very basic GPIO device
    '''
        
    def __init__(self, serial_port_name):
        '''
        Try to create a controller using the passed serial port name.
        
        Names are a string of the form '/dev/ttyXXX' where XXX is a 
        string such as ACM# or USB#
        '''
        self._name = serial_port_name;
        self._port = serial.Serial(serial_port_name, 
                                   PORT_SPEED, 
                                   timeout=TIMEOUT_IN_SEC)
        #if DEBUG:
        #    print(self._port.get_settings())
           
        # give Arduino time to reset after serial open which causes a reset
        time.sleep(RESET_TIME_IN_SEC)  
        v='<TBD>'
        try:
            self._port.write(VERSION_COMMAND)
            self._port.flush()
            v = self._port.readline().decode('UTF-8').strip()
            self._version = int(v)
        except:
            self._version = None
            raise RuntimeError('invalid version of "{}" received from device'.format(v))
        if DEBUG:
            print('created SerialArduinoGpioController for "{}"'.format(serial_port_name))
            print('found version of {}'.format(self._version))


    def is_active(self):
        '''
        return True if device is active / usable
        '''
        return self._version is not None

    
    def close(self):
        '''
        release resources. 
        
        After this call is_active() will return False.
        '''
        if self.is_active():
            self._port.close()
            self._version = None

    
    def get_name(self):
        '''
        return the serial device name
        '''
        if not self.is_active():
            raise RuntimeError('get_name() called on inactive controller')

        return self._name
    
    
    def get_version(self):
        '''
        return the version of the code running in the Arduino.
        '''
        if not self.is_active():
            raise RuntimeError('get_verion() called on inactive controller')
        
        return self._version


    def set_pin(self, pin, value):
        '''
        Set a GPIO pin to HIGH (INPUT mode with PULLUP) or LOW.
        '''
        if not self.is_active():
            raise RuntimeError('set_pin() called on inactive controller')

        if pin not in VALID_GPIO_PINS:
            raise ValueError('pin value of {} is not in {}'.format(pin, VALID_GPIO_PINS))
        if value:
            c = chr(ord('A') + pin)
        else:
            c = chr(ord('a') + pin)
        self._port.write(c.encode('UTF-8'))
        self._port.flush()
        return
                        

    def read_pin_values(self):
        '''
        read the pin values and return a map of {pin:value}
        '''
        if not self.is_active():
            raise RuntimeError('read_pin_values() called on inactive controller')

        self._port.write(READ_COMMAND)
        self._port.flush()
        l = self._port.readline().decode('UTF-8').strip()
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
        if not self.is_active():
            raise RuntimeError('save_pins() called on inactive controller')

        self._port.write(SAVE_COMMAND)
        self._port.flush()
        return


    def read_analog_value(self, pin):
        '''
        Retrieve the analog value for a given pin.
        
        Return 0-1023.
        '''
        if not self.is_active():
            raise RuntimeError('read_analog_value() called on inactive controller')

        if ((pin < 0) or (pin > 7)):
            raise IndexError('valid analog pins are 0 to 7')
        
        self._port.write(GET_ANALOG_PIN_COMMAND[pin])
        self._port.flush()
        l = self._port.readline().decode('UTF-8').strip()
        if DEBUG:
            print('line: "{}"'.format(l))  # don't need a \n
        # return what we get from the Arduino
        return int(l)
    
    def read_analog_values(self):
        '''
        return a map with all analog pin values
        '''
        if not self.is_active():
            raise RuntimeError('read_analog_values() called on inactive controller')

        result = {}
        for a_pin in range(8):
            result[a_pin] = self.read_analog_value(a_pin)
        return result

#
# main
#
if __name__ == "__main__":
    
    filtered_devices = []
    # use list from command line if provided
    if len(sys.argv) > 1:
        filtered_devices = sys.argv[1:]
    # otherwise look for possible devices to try
    else:
        # this will hold the names of serial port devices which might have Arduino
        serial_devices = [comport.device for comport in serial.tools.list_ports.comports()]
        for d in serial_devices:
            if d not in FILTERED_OUT_DEVICES:
                filtered_devices.append(d)
            else:
                print('removed "{}" from device list'.format(d))
        if DEBUG:
            print('found devices include:  {}\n'.format(filtered_devices))

    # get serial port access for each serial device
    for s in filtered_devices:
        print('trying {}'.format(s))
        p = SerialArduinoGpioController(s)
        print('made controller for "{}"'.format(s))
        if not p.is_active():
            print('CONTROLLER DOES NOT CLAIM TO BE ACTIVE AFTER CREATION!!')

        # exercise this port if version > 0
        if p._version >= 0:
            print('controller "{}":'.format(p.get_name()))
            print('  code version is {}'.format(p.get_version()))
            print('  reading pins gives "{}"'.format(p.read_pin_values()))
            print('  analog values are {}'.format(p.read_analog_values()))
        
        p.close()
        if p.is_active():
            print('CONTROLLER IS STILL CLAIMING TO BE ACTIVE AFTER CLOSE()!!')

        print('\n')
