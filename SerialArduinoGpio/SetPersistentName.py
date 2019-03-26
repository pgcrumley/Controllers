#!/usr/bin/env python3
"""
MIT License

Copyright (c) 2019 Paul G Crumley

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

Set the persistent name of the device.

usage: SetPersistentName
    -p, --port is the serial of the device
    -n, --name is the persistent name to write to the device (16 characters)           
"""

import argparse
import serial
import sys

import SerialArduinoGpioController

import serial.tools.list_ports

DEBUG = None


#
# main
#
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Set the persistent name of the device')
    parser.add_argument('-d', '--debug', 
                        help='turn on debugging', 
                        action='store_true')
    parser.add_argument('-p', '--port', 
                        help='port to which Arduino is connected', 
                        default=None)
    parser.add_argument('-n', '--name', 
                        help='persistent name to set in the device (must be {} characters)'.format(SerialArduinoGpioController.PERSISTENENT_NAME_SIZE), 
                        default=None)

    args = parser.parse_args()

    if (args.debug):
        DEBUG = 1
        print('turned on DEBUG from command line.',
              file=sys.stderr, flush=True)

    given_port = args.port
    persistent_name = args.name
    if given_port is None:
        print('port parameter is required')
        parser.print_help(sys.stdout)
        exit(1)
    if persistent_name is None:
        print('name parameter is required')
        parser.print_help(sys.stdout)
        exit(1)

    new_name = persistent_name.encode('UTF-8')
    if len(new_name) != SerialArduinoGpioController.PERSISTENENT_NAME_SIZE:
        print('name is not of length {}'.format(SerialArduinoGpioController.PERSISTENENT_NAME_SIZE))
        parser.print_usage(sys.stdout)
        exit(1)

    print('Setting name of device on port "{}" to "{}"'.format(persistent_name,
                                                               given_port))  

    try:
        c = SerialArduinoGpioController.SerialArduinoGpioController(given_port)
        version = c.get_version()
        if version >= 'V2':
            current_name = c.get_persistent_name()
            print('found controller with name of "{}" on port "{}" with version "{}"\n'.format(current_name,
                                                                                               given_port, 
                                                                                               version),
                                                                                               flush=True)
            if DEBUG:
                print('about to store_persistent_name()',
                      file=sys.stderr, flush=True)
            c.store_persistent_name(new_name)
            if DEBUG:
                print('back from store_persistent_name()',
                      file=sys.stderr, flush=True)
        else:
            print('controller on port "{}" has old version "{}" which has no persistent name capability\n'.format(given_port, version))
    except Exception as e:
        print('while creating controller on port "{}" caught "{}"\n'.format(given_port, e),
              file=sys.stderr, flush=True)
        exit(10)

    print('done.')
    