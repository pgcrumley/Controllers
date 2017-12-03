#!/usr/bin/python3
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

Exercise a set of relays made by Etekcity using a 433 MHz transmitter connected
to a Raspberry Pi pin in order to determine the device addr value.

This assumes the 433 MHz transmitter is attached to the Raspberry Pi on pin 18.  
"""

import sys
import time

from etekcity_controller import Transmitter

# change  if the transmitter connected to a different board pin
TRANSMIT_PIN = 18
# try increasing this if the relays never turn on
RETRY_COUNT = 3

if len(sys.argv) > 1:
    if sys.argv[1] == '-h' or sys.argv[1] == '-?' or sys.argv[1] == '--help':
        print('usage: etekcity_try_addrs.py [start-addr [end-addr]]', 
              file=sys.stderr)
        print('    start and end must be between 0 and 256', file=sys.stderr)
        print('    start must be < end', file=sys.stderr)
        print('    start and end default to 0 and 256', file=sys.stderr)
        print('    setting start addr slows down tests', file=sys.stderr)
        exit(1)

start = 0
end = 256
delay = 0.5
if len(sys.argv) > 1:
    try:
        start = int(sys.argv[1])
        delay = 3
    except Exception as e:
        print('parameter of "{}" is not "0" to "256"', sys.argv[1])
        exit(2)
if len(sys.argv) > 2:
    try:
        end = int(sys.argv[2])
    except Exception as e:
        print('parameter of "{}" is not "0" to "256"', sys.argv[2])
        exit(2)

if start < 0 or start > 256:
    print('start must be between 0 and 256 inclusive', file=sys.stderr)
    exit(2)

if end < 0 or end > 256:
    print('end must be between 0 and 256 inclusive', file=sys.stderr)
    exit(2)

if start >= end:
    print('end must be > start', file=sys.stderr)
    exit(2)


print('looking for addrs between {} and {}'.format(start, end))

ec = Transmitter(TRANSMIT_PIN, retries=RETRY_COUNT)
for addr in range(start, end):
    print('addr {}'.format(i))
    for unit in [1, 2, 3, 4, 5]:
        ec.transmit_on(addr, unit)
    time.sleep(1)
    for unit in [1, 2, 3, 4, 5]:
        ec.transmit_off(addr, unit)
