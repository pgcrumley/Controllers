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

Each line is a map of {'time' : 'iso-time', 
                       'name': <persistent_name>,
                       'values': {<pin>:<value>}
                       }
                         
or a map of {'time' : 'iso-time', 
             'event': 'event data'
             }
                
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

DEFAULT_SAMPLE_INTERVAL_IN_SECONDS = 60
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
    item = {'name':controller_name,
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


def get_controllers(port_list):
    '''
    Try to find usable controllers on the given ports.
    
    return a map of {name, controller}
    '''
    result = {}
    for p in port_list:

        for serial_port_name in port_name_list:
            try:
                c = SerialArduinoGpioController.SerialArduinoGpioController(serial_port_name)
                version = c.get_version()
                if version >= 'V2':
                    name = c.get_persistent_name()
                    result[name] = c
                if DEBUG:
                    print('found controller "{}" on port "{}" with version "{}"\n'.format(name, serial_port_name, version),
                          file=sys.stderr, flush=True)
                    
                else:
                    if DEBUG:
                        print('controller on port "{}" has old version "{}"\n'.format(serial_port_name, version),
                              file=sys.stderr, flush=True)
            except Exception as e:
                if DEBUG:
                    print('while creating controller on port "{}" caught "{}"\n'.format(serial_port_name, e),
                          file=sys.stderr, flush=True)
    
    return result


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
    controllers = get_controllers(port_name_list)
    
    # open file to log values
    with open(log_filename, 'a') as output_file:

        emit_event(output_file, 'STARTING MONITOR')
        if len(controllers) > 0:
            for ck in controllers.keys():
                event_text = 'Found controller {} of version {}'.format(ck, controllers[ck].get_version())
                emit_event(output_file, event_text)
        else:
            event_text = 'NO CONTROLLERS FOUND'.format()
            emit_event(output_file, event_text)
            

        next_sample_time = time.time()
        while True:
            # making copy of names so we can remove controllers in loop
            c_name_list = []
            for c_name in controllers:
                c_name_list.append(c_name)
            # operate on copy of keys
            for c_name in c_name_list:
                try:
                    values = controllers[c_name].read_pin_values()
                    emit_sample(output_file, c_name, values)
                except Exception as e:
                    event_text = 'While reading controller {} caught exception of {}.  removing'.format(ck, e)
                    emit_event(output_file, event_text)
                    controllers.pop(c_name, None)
                    if DEBUG:
                        print(event_text.format(),
                              file=sys.stderr, flush=True)
                    
            # wait till next sample time            
            next_sample_time = next_sample_time + sample_interval
            delay_time = next_sample_time - time.time()
            if DEBUG:
                print('delay_time = {}'.format(delay_time),
                      file=sys.stderr, flush=True)
        
            if 0 >= delay_time:  # don't sleep if already past next sample time
                time.sleep(delay_time)
