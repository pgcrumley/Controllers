#!env python3
"""
MIT License

Copyright (c) 2017 Paul G Crumley

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

Control a relay made by Etekcity using a 433 MHz transmitter connected to a 
Raspberry Pi pin.  Specify the pin with the board numbers.
"""

import sys
import time
import RPi.GPIO as GPIO

DEBUG = False

class Transmitter:
    """
    Create one of these for each 433 MHz transmitter that is used to 
    control the relays.
    
    The signal to the device is a sequence of:
        address bits (0-255)
        unit bits (1-5 encoded as per table below)
        action bits (on / off encoded as per table below)
        end bits (as per table below)
    The signal is then idle to allow the device to decode and act
    
    I have not found documentation on the chips or signals so the 
    above has been determined by measuring existing devices.
    """
    # first valid address
    FIRST_VALID_ADDRESS = 0
    # last valid address
    LAST_VALID_ADDRESS = 255
    
    # first valid unit
    FIRST_VALID_UNIT = 1
    # last valid unit
    LAST_VALID_UNIT = 5
    
    # special address for ALL_ON and ALL_OFF function
    ALL_ADDRESS = 85
    # special unit for ALL_ON and ALL_OFF function
    ALL_UNIT = 3
    
    VALID_PINS = [3, 5, 7, 8, 10, 
                  11, 12, 13, 15, 16, 18, 19, 
                  21, 22, 23, 24, 26, 29, 
                  31, 32, 33, 35, 36, 37, 38, 40]

    # this might be increased in noisy environments
    DEFAULT_COPIES_TO_TRANSMIT = 6
    
    #
    # internal details
    #
    
    _TOTAL_BIT_TIME_IN_SECONDS = 720 / 1000000.0
    _ZERO_BIT_TIME_HIGH_IN_SECONDS = 180 / 1000000.0
    _ONE_BIT_TIME_HIGH_IN_SECONDS = (
        _TOTAL_BIT_TIME_IN_SECONDS 
        - _ZERO_BIT_TIME_HIGH_IN_SECONDS
        )
    _DELAY_AFTER_TRANSMIT_IN_SECONDS = 5000 / 1000000.0
    
    # these appear to be stable across units 
    _UNIT_BITS = {1:[0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1],
                  2:[0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 0],
                  3:[0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0],
                  4:[0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0],
                  5:[0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0],
                  }
    _ON_BITS = [0, 0, 1, 1]
    _OFF_BITS = [1, 1, 0, 0]
    _END_BITS = [0]
    
    def __init__(self, board_pin, retries=DEFAULT_COPIES_TO_TRANSMIT):
        """
        Create a transmitter give the board_pin to which the 433 MHz
        transmitter is connected.
        """
        if board_pin not in Transmitter.VALID_PINS:
            raise ValueError('board_pin of {} must be in {}'.format(
                board_pin,
                VALID_PINS
                )
            )
        self._board_pin = board_pin
        if retries < 1:
            raise ValueError('retries value of {} is not > 0'.format(retries))
        self.__retries = retries

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self._board_pin, GPIO.OUT)
        GPIO.output(self._board_pin, GPIO.LOW)

        self.__alive = True

    def close(self):
        """
        Release resources and mark controller as dead
        """
        self.__alive = False
        self._board_pin = None
        GPIO.cleanup()
            
    def __transmit_bits(self, values):
        """
        transmit a sequence of bits.  Leaves signal in LOW state.
        """
        for value in values:
            if value:
                high_time = self._ONE_BIT_TIME_HIGH_IN_SECONDS
            else:
                high_time = self._ZERO_BIT_TIME_HIGH_IN_SECONDS
            
            start_time = time.time()
            GPIO.output(self._board_pin, GPIO.HIGH)
            high_end_time = time.time() + high_time
            total_end_time = time.time() + self._TOTAL_BIT_TIME_IN_SECONDS
            while time.time() < high_end_time:
                pass
            GPIO.output(self._board_pin, GPIO.LOW) 
            while time.time() < total_end_time:
                pass
            
    def __addr_to_bits(self, addr):
        if (addr < Transmitter.FIRST_VALID_ADDRESS 
                or addr > Transmitter.LAST_VALID_ADDRESS):
            raise ValueError('address of {} is not between {} and {}'.format(
                addr,
                Transmitter.FIRST_VALID_ADDRESS,
                Transmitter.LAST_VALID_ADDRESS
                )
            )
        result = []
        for i in [7, 6, 5, 4, 3, 2, 1, 0]:
            result.append((addr >> i) & 1 )
        return result
    
    def transmit_on(self, addr, unit):
        """
        Send a command to turn on the relay specified by addr & unit. 
        
        The command is normally sent multiple times for some degree of
        robustness.
        """
        if not self.__alive:
            raise RuntimeError('etekcity_controller has been closed')
        
        for i in range(self.__retries):
            self.__transmit_bits(self.__addr_to_bits(addr))
            self.__transmit_bits(self._UNIT_BITS[unit])
            self.__transmit_bits(self._ON_BITS)
            self.__transmit_bits(self._END_BITS)
            time.sleep(self._DELAY_AFTER_TRANSMIT_IN_SECONDS)
        
    def transmit_off(self, addr, unit):
        """
        Send a command to turn off the relay specified by addr & unit. 
        
        The command is normally sent multiple times for some degree of
        robustness.
        """
        if not self.__alive:
            raise RuntimeError('etekcity_controller has been closed')
        
        for i in range(self.__retries):
            self.__transmit_bits(self.__addr_to_bits(addr))
            self.__transmit_bits(self._UNIT_BITS[unit])
            self.__transmit_bits(self._OFF_BITS)
            self.__transmit_bits(self._END_BITS)
            time.sleep(self._DELAY_AFTER_TRANSMIT_IN_SECONDS)

    def transmit_action(self, addr, unit, action):
        """
        Send a command to set the relay specified by addr & unit.  Action can be
        True, False, 'on', or 'off'. 
        
        The command is normally sent multiple times for some degree of
        robustness.
        """
        if not self.__alive:
            raise RuntimeError('etekcity_controller has been closed')
        
        if isinstance(action, bool):
            if action:
                self.transmit_on(addr, unit)
            else:
                self.transmit_off(addr, unit)
        elif isinstance(action, str):
            if action.upper() == 'ON':
                self.transmit_on(addr, unit)
            elif action.upper() == 'OFF':
                self.transmit_off(addr, unit)
            else:
                raise ValueError('expect value of "ON" or "OFF"')
        else:
            raise ValueError('expect value of "ON", "OFF", True or False')

    def transmit_all_on(self):
        """
        Turn on all the relays. 
        
        The command is normally sent multiple times for some degree of
        robustness.
        
        I found sequence this while coding test cases.  (pgc)
        """
        if not self.__alive:
            raise RuntimeError('etekcity_controller has been closed')
        
        for i in range(self.__retries):
            self.transmit_on(Transmitter.ALL_ADDRESS, Transmitter.ALL_UNIT)
            
    def transmit_all_off(self):
        """
        Turn off all the relays. 
        
        The command is normally sent multiple times for some degree of
        robustness.

        I found sequence this while coding test cases.  (pgc)
        """
        if not self.__alive:
            raise RuntimeError('etekcity_controller has been closed')
        
        for i in range(self.__retries):
            self.transmit_off(Transmitter.ALL_ADDRESS, Transmitter.ALL_UNIT)
    #
    # end of class Transmitter        
    #
    
def usage():
    print('usage:  Etekcity.py board_pin address unit on|off',
          file=sys.stderr)    
    print('          board_pin is the pin connected to the transmitter',
          file=sys.stderr)    
    print('          address is a number from 0 to 255 inclusive',
          file=sys.stderr)    
    print('          unit is a number between 1 and 5 inclusive',
          file=sys.stderr)    
    print('          on|off are the characters "on" or "off"',
          file=sys.stderr)    
    exit(1)

if '__main__' == __name__ :
    """
    Simple command to operate devices.
    """
    
    ## special case
    if 2 == len(sys.argv):
        board_pin = int(sys.argv[1])
        transmitter = Transmitter(board_pin)
        transmitter.transmit_all_off()
        exit(0)
    
    ## normal case
    if 5 != len(sys.argv):
        print('len(sys.argv) is {}'.format(len(sys.argv)), file=sys.stderr)
        usage()

    board_pin = None
    addr = None
    unit = None
    action = None
    try:
        board_pin = int(sys.argv[1])
        if DEBUG:
            print('board_pin:  {}'.format(board_pin))
        if board_pin not in Transmitter.VALID_PINS:
            print('board_pin of {} is not in {}'.format(
                    board_pin, 
                    Transmitter.VALID_PINS),
                  file=sys.stderr)
            usage()
            
        addr = int(sys.argv[2])
        if DEBUG:
            print('address:    {}'.format(addr))
        if (0 > addr) or (255 < addr):
            print('address of {} is not >= 0 and <= 255'.format(addr),
                  file=sys.stderr)
            usage()
        
        unit = int(sys.argv[3])
        if DEBUG:
            print('unit:       {}'.format(unit))
        if unit not in Transmitter._UNIT_BITS:
            print('unit of {} is not in {}'.format(
                    unit, 
                    list(Transmitter._UNIT_BITS.keys())),
                  file=sys.stderr)
            usage()

        if DEBUG:
            print('action:     {}'.format(sys.argv[4]))                    
        if  'ON' == sys.argv[4].upper():
            action = True;
        elif 'OFF' == sys.argv[4].upper():
            action = False;
        else:
            print('action of "{}" is not in {}'.format(
                    action,
                    ['on','off']),
                  file=sys.stderr)
            usage()
    except Exception as e:
        print('caught "{}"'.format(e))
        usage()
        

    if DEBUG:
        print('board_pin:  {}'.format(board_pin), file=sys.stderr)
        print('address:    {}'.format(addr), file=sys.stderr)
        print('unit:       {}'.format(unit), file=sys.stderr)
        print('action:     {}'.format(action), file=sys.stderr)
    
    transmitter = Transmitter(board_pin)
    transmitter.transmit_action(addr, unit, action)
    
    transmitter.close()
    