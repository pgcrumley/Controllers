#!/usr/bin/env python3
"""
MIT License

Copyright (c) 2018, 2021 Paul G Crumley

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

It is also possible to read analog pin values. 

A name (16 bytes in length) for the Arduino device can be written to 
EEPROM for later retrieval

This code must have access to write the serial ports which can require
running with elevated user authorization (e. g. as "root")
"""

import sys
import time

import serial
import serial.tools.list_ports


DEBUG = None

ARDUINO_CODE_NAME = 'SerialArduinoGpio'
PORT_SPEED = 115200
TIMEOUT_IN_SEC = 2.0
RESET_TIME_IN_SEC = 3.0
VALID_DIGITAL_PINS = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13}
VALID_ANALOG_PINS = {0, 1, 2, 3, 4, 5, 6, 7}


NL = '\n'.encode('UTF-8')
READ_VERSION_COMMAND = '`'.encode('UTF-8')
READ_PERSISTENT_NAME_COMMAND = '='.encode('UTF-8') #V2 and later
SAVE_PERSISTENT_NAME_COMMAND = '#'.encode('UTF-8') #V2 and later
PERSISTENENT_NAME_SIZE = 16
READ_GPIO_PINS_COMMAND = '?'.encode('UTF-8')
SET_GPIO_PIN_HIGH_COMMAND = {2:'C'.encode('UTF-8'),
                               3:'D'.encode('UTF-8'),
                               4:'E'.encode('UTF-8'),
                               5:'F'.encode('UTF-8'),
                               6:'G'.encode('UTF-8'),
                               7:'H'.encode('UTF-8'),
                               8:'I'.encode('UTF-8'),
                               9:'J'.encode('UTF-8'),
                               10:'K'.encode('UTF-8'),
                               11:'L'.encode('UTF-8'),
                               12:'M'.encode('UTF-8'),
                               13:'N'.encode('UTF-8')
                               }
SET_GPIO_PIN_LOW_COMMAND = {2:'c'.encode('UTF-8'),
                              3:'d'.encode('UTF-8'),
                              4:'e'.encode('UTF-8'),
                              5:'f'.encode('UTF-8'),
                              6:'g'.encode('UTF-8'),
                              7:'h'.encode('UTF-8'),
                              8:'i'.encode('UTF-8'),
                              9:'j'.encode('UTF-8'),
                              10:'k'.encode('UTF-8'),
                              11:'l'.encode('UTF-8'),
                              12:'m'.encode('UTF-8'),
                              13:'n'.encode('UTF-8')
                              }
SAVE_POWER_ON_VALUES_COMMAND = '+'.encode('UTF-8') # V2 and later
READ_POWER_ON_VALUES_COMMAND = '-'.encode('UTF-8') # V3 and later
READ_ANALOG_PIN_COMMAND = {0:'0'.encode('UTF-8'), # version 1 and later
                             1:'1'.encode('UTF-8'),
                             2:'2'.encode('UTF-8'),
                             3:'3'.encode('UTF-8'),
                             4:'4'.encode('UTF-8'),
                             5:'5'.encode('UTF-8'),
                             6:'6'.encode('UTF-8'),
                             7:'7'.encode('UTF-8')
                             }

    
class SerialArduinoGpioController:
    '''
    This class allows an Arduino on a Raspberry Pi serial port to used
    as a very basic GPIO device
    
    private variables are:
    __serial_port_name   the OS name of the serial port for attachment
    __serial_port        the python object for accessing the device
    __version            string of form 'V##_code_name'
    __version_number     ## part of version as an integer
    
    '''

    def __init__(self, serial_port_name):
        '''
        Try to create a controller using the passed serial port name.
        
        On *ix systems, names are a string of the form '/dev/ttyXXX',
        where XXX is a string such as ACM# or USB#
        
        On Windows systems, names are a string of the form 'COMx', 
        where 'x' is '1', '2', ...
        
        Does not try to work with versions < V2
        '''
        self.__serial_port_name = serial_port_name;
        self.__serial_port = serial.Serial(self.__serial_port_name, 
                                           PORT_SPEED, 
                                           timeout=TIMEOUT_IN_SEC)
        #if DEBUG:
        #    print(self.__serial_port.get_settings())
           
        # give Arduino time to reset after serial open which causes a reset
        time.sleep(RESET_TIME_IN_SEC) 
        self.__version = '<UNKNOWN>'
        try:
            self.__serial_port.write(READ_VERSION_COMMAND)
            self.__serial_port.flush()
            self.__version = self.__serial_port.readline().decode('UTF-8').strip()
            codename = self.__version.split('_')[1]
            if codename != ARDUINO_CODE_NAME:
                raise RuntimeError(f'expected "...{ARDUINO_CODE_NAME}..." but read {self.__version}')
            v = self.__version.split('_')[0]
            v = int(v.split('V')[1])
            if v < 2:
                raise RuntimeError(f'version must be >= V2 but read {self.__version}')
                
            self.__version_number = v

        except Exception as e:
            self.__version = None
            raise RuntimeError(f'while initializing device caught "{e}"')
        if DEBUG:
            print(f'created SerialArduinoGpioController for "{serial_port_name}"')
            print(f'found version of {self.__version}')


    def is_active(self):
        '''
        return True if device is active / usable
        '''
        return self.__version is not None

    
    def close(self):
        '''
        release resources. 
        
        After this call is_active() will return False.
        '''
        if self.is_active():
            self.__serial_port.close()
            self.__version = None

    
    def get_serial_port_name(self):
        '''
        return the serial port name to which this device is attached
        '''
        if not self.is_active():
            raise RuntimeError('get_serial_portname() called on inactive controller')

        return self.__serial_port_name
    

    def get_name(self):
        '''
        deprecated -- use the get_serial_port_name function instead
        '''
        return self.get_serial_port_name()
    
    
    def get_persistent_name(self):
        '''
        return the persistent device name
        '''
        if not self.is_active():
            raise RuntimeError('get_persistent_name() called on inactive controller')

        self.__serial_port.write(READ_PERSISTENT_NAME_COMMAND)
        self.__serial_port.flush()
        persistent_name = self.__serial_port.readline().decode('UTF-8').strip()
        if DEBUG:
            print(f'line from READ_PERSISTENT_NAME_COMMAND is: "{persistent_name}"')  # don't need a \n
        
        return persistent_name
    
    
    def store_persistent_name(self, name):
        '''
        Save the persistent device name.
        
        name must be 16 characters long.
        '''
        if not self.is_active():
            raise RuntimeError('get_persistent_name() called on inactive controller')
        
        if isinstance(name, bytes):
            passed_name = name
        else:
            passed_name = str(name).encode('UTF-8')
            
        if len(passed_name) != PERSISTENENT_NAME_SIZE:
            raise RuntimeError(f'passed name of "{passed_name}" is not of size {PERSISTENENT_NAME_SIZE}')
            
        self.__serial_port.write(SAVE_PERSISTENT_NAME_COMMAND + passed_name)
        self.__serial_port.flush()

        # verify operation
        new_name = self.get_persistent_name()
        if DEBUG:
            print(f'line from get_persistent_name() is: "{new_name}"')  # don't need a \n
        new_name = new_name.encode('UTF-8')    
        if passed_name != new_name:
            raise RuntimeError(f'new_name of "{new_name}" does not match passed name "{passed_name}"')
        
        return
    
    
    def get_version(self):
        '''
        return the version of the code running in the Arduino.
        '''
        if not self.is_active():
            raise RuntimeError('get_verion() called on inactive controller')
        
        return self.__version


    def get_version_number(self):
        '''
        return the version number (as an integer) of the code running in the Arduino.
        '''
        if not self.is_active():
            raise RuntimeError('get_verion_number() called on inactive controller')
        
        return self.__version_number


    def set_digital_value(self, pin, value):
        '''
        Set a digital GPIO pin to HIGH (INPUT mode with PULLUP) or LOW.
        '''
        if not self.is_active():
            raise RuntimeError('set_digital_value() called on inactive controller')

        if pin not in VALID_DIGITAL_PINS:
            raise ValueError(f'pin value of {pin} is not in {VALID_DIGITAL_PINS}')
        if value:
            c = SET_GPIO_PIN_HIGH_COMMAND[pin]
        else:
            c = SET_GPIO_PIN_LOW_COMMAND[pin]
        self.__serial_port.write(c)
        self.__serial_port.flush()
        return

    def set_pin(self, pin, value):
        '''
        deprecated -- use the read_digital_values function instead
        '''          
        self.set_digital_value(pin, value)
        return


    def read_digital_values(self):
        '''
        read the digital pin values and return a map of {pin:value}
        '''
        if not self.is_active():
            raise RuntimeError('read_pin_values() called on inactive controller')

        self.__serial_port.write(READ_GPIO_PINS_COMMAND)
        self.__serial_port.flush()
        l = self.__serial_port.readline().decode('UTF-8').strip()
        if DEBUG:
            print(f'in read_pin_values device sent: "{l}"')

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

    def read_digital_value(self, pin):
        '''
        return the value of a single pin
        '''
        return self.read_digital_values()[pin]

    def read_pin_values(self):
        '''
        deprecated -- use the read_digital_values function instead
        '''
        return self.read_digitial_values()

    def save_power_on_pin_values(self):
        '''
        Save the current output pin values so they are reloaded at reset
        '''
        if not self.is_active():
            raise RuntimeError('save_pins() called on inactive controller')

        self.__serial_port.write(SAVE_POWER_ON_VALUES_COMMAND)
        self.__serial_port.flush()
        return

    def read_power_on_pin_values(self):
        '''
        Read and return the power-on values stored in EEPROM
        
        Only works for V3 and later.
        '''
        if self.__version < 'V3':
            raise NotImplementedError('function only available on V3 and above')

        if not self.is_active():
            raise RuntimeError('save_pins() called on inactive controller')

        self.__serial_port.write(READ_POWER_ON_VALUES_COMMAND)
        self.__serial_port.flush()
        l = self.__serial_port.readline().decode('UTF-8').strip()
        if DEBUG:
            print(f'in read_power_on_values device sent: "{l}"')

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
        if DEBUG:
            print(f'read_power_on_values() returning : "{result}"')
        return result        

    def save_pins(self):
        '''
        deprecated -- use the save_power_on_pin_values function instead
        '''
        self.save_power_on_pin_values()
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
        
        self.__serial_port.write(READ_ANALOG_PIN_COMMAND[pin])
        self.__serial_port.flush()
        l = self.__serial_port.readline().decode('UTF-8').strip()
        if DEBUG:
            print(f'line read from device: "{l}"')  # don't need a \n
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

    # remove these devices from list -- this list is ad hoc
    # probably best to put the port names on the command line
    FILTERED_OUT_DEVICES = ['COM1', 'COM4', # windows seems to use these
                            '/dev/ttyAMA0'] # raspberry pi console
    
    filtered_ports = []
    # use list from command line if provided
    if len(sys.argv) > 1:
        filtered_ports = sys.argv[1:]
    # otherwise look for possible devices to try
    else:
        # this will hold the names of serial port devices which might have Arduino
        serial_devices = [comport.device for comport in serial.tools.list_ports.comports()]
        for d in serial_devices:
            if d not in FILTERED_OUT_DEVICES:
                filtered_ports.append(d)
            else:
                print(f'removed "{d}" from device list')
        if DEBUG:
            print(f'found ports include:  {filtered_ports}\n')

    # get serial port access for each serial device
    print(f'looking for devices on {filtered_ports}')
    for s in filtered_ports:
        try:
            print(f'trying {s}')
            sagc = SerialArduinoGpioController(s)
            print(f'made controller on port "{s}"')
            if not sagc.is_active():
                print('CONTROLLER DOES NOT CLAIM TO BE ACTIVE AFTER CREATION!!')
    
            print(f'serial_port: "{sagc.get_serial_port_name()}":')
            print(f'code version is: "{sagc.get_version()}"')
            print(f'persistent name: "{sagc.get_persistent_name()}":')
            print(f'digital values are: "{sagc.read_digital_values()}"')
            print(f'analog values are: "{sagc.read_analog_values()}"')
            if sagc.get_version_number() >= 3:
                print(f'power-on values: "{sagc.read_power_on_pin_values()}"')
            else:
                print(f'power-on values: NOT AVAILABLE ON < V3')
            
            sagc.close()
            if sagc.is_active():
                print('CONTROLLER IS STILL CLAIMING TO BE ACTIVE AFTER CLOSE()!!')
        except Exception as e:
            print(f'caught "{e}"')

        print('\n')
        sys.stdout.flush()
    print ('done looking for devices')
    