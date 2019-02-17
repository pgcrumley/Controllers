#!/usr/bin/env python3
"""
MIT License

Copyright (c) 2017, 2019 Paul G Crumley

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

Periodically read the GPIO signals from SerialArduinoGpioController(s)

The raw data is stored with a timestamp for later processing.

The Arduino(s) is(are) accessed by serial port(s) on a Raspberry Pi.

"""

import argparse
import datetime
import json
import serial
import sys
import time

import SerialArduinoGpioController

import serial.tools.list_ports

DEBUG = 0

DEFAULT_SAMPLE_INTERVAL_IN_SECONDS = 5 * 60
DEFAULT_LOG_FILE_NAME = '/opt/Controllers/logs/SerialArduinoGpioMonitor.log'

# remove these devices from list -- this list is ad hoc
# probably best to put the port names on the command line
FILTERED_OUT_DEVICES = ['COM1', 'COM3', # windows seems to use these
                        '/dev/ttyAMA0'] # raspberry pi console


def emit_json_map(output, json_map):
    '''
    generate a time stamp in UTC for use in the output
    
    A 'time' entry with the time stamp is added to the json_map.
    '''
    when = datetime.datetime.now(datetime.timezone.utc)
    when_str = when.isoformat()
    json_map['time'] = when_str
    output.write('{}\n'.format(json.dumps(json_map)))
    output.flush()


def emit_event(output, event_text):
    '''
    send a line with an event to the output with a time stamp
    '''
    item = {'event':event_text}
    emit_json_map(output, item)

    
def emit_sample(output, controller_name, values):
    '''
    send a line with sample values to the output with a time stamp
    '''
    item = {'controller_name':controller_name,
            'values':values}
    emit_json_map(output, item)

    
def determine_ports():
    '''
    Go through serial ports available and try to find ports for the controller.
    
    Return a list of ports
    '''
    filtered_devices = []

    # this will hold the names of serial port devices which might have Arduino
    serial_devices = [comport.device for comport in serial.tools.list_ports.comports()]
    for d in serial_devices:
        if d not in FILTERED_OUT_DEVICES:
            filtered_devices.append(d)
        else:
            print('removed "{}" from device list'.format(d),
                  file=sys.stderr, flush=True)
    if DEBUG:
        print('found devices include:  {}\n'.format(filtered_devices), 
              file=sys.stderr, flush=True)
    
    return filtered_devices

#
# main
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture and log GPIO pin data from an Arduino attached via a serial port.")
    parser.add_argument("-d", "--debug", 
                        help="turn on debugging", 
                        action="store_true")
    parser.add_argument("-l", "--log_filename", 
                        help="file to log data, create or append", 
                        default=DEFAULT_LOG_FILE_NAME)
    parser.add_argument("-p", "--port", 
                        help="port to which Arduino is connected", 
                        default=None)
    parser.add_argument("-i", "--interval", 
                        help="how often to sample sensors in seconds", 
                        default=DEFAULT_SAMPLE_INTERVAL_IN_SECONDS)
    args = parser.parse_args()

    if (args.debug):
        DEBUG = 1
        print('turned on DEBUG from command line.',
              file=sys.stderr, flush=True)

    log_filename = args.log_filename
    sample_interval = int(args.interval)
    given_port = args.port
    
    if DEBUG:
        print('log_filename = {}'.format(log_filename),
              file=sys.stderr, flush=True)
        print('sample_interval = {}'.format(sample_interval),
              file=sys.stderr, flush=True)
        print('given_port = {}'.format(given_port),
              file=sys.stderr, flush=True)

    if sample_interval < 0:
        sample_interval = 0
        if DEBUG:
            print('negative sample interval set to 0',
                  file=sys.stderr, flush=True)

    if given_port:
        port_name_list = [given_port]
    else:
        port_name_list = determine_ports()

    # get serial port access for each serial device
    controllers = set()
    for serial_port_name in port_name_list:
        c = SerialArduinoGpioController.SerialArduinoGpioController(serial_port_name)
        controllers.add(c)
        if DEBUG:
            print('include controller:  {}\n'.format(c.get_name()),
                  file=sys.stderr, flush=True)
            print('VERSION = "{}"'.format(c.get_version()),
                                          file=sys.stderr, flush=True)

    # open file to log pressure over time
    with open(log_filename, 'a') as output_file:

        emit_event(output_file, 'STARTING MONITOR')
        for c in controllers:
            event_text = 'FOUND CONTROLLER ON PORT {}'.format(c.get_name())
            emit_event(output_file, event_text)

        next_sample_time = time.time()
        while True:
            for c in controllers:
                values = c.read_pin_values()
                emit_sample(output_file, c.get_name(), values)

            # wait till next sample time            
            next_sample_time = next_sample_time + sample_interval
            delay_time = next_sample_time - time.time()
            if DEBUG:
                print('delay_time = {}'.format(delay_time),
                      file=sys.stderr, flush=True)
        
            if 0 < delay_time:  # don't sleep if already past next sample time
                time.sleep(delay_time)
