#!/usr/bin/env python3
"""
MIT License

Copyright (c) 2019, 2021 Paul G Crumley

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

Very simple web server to collect GPIO values from an Arduino connected 
on a serial port running the SerialArduinoGpio code

By default will accept GET from any address on port 10000
"""

import argparse
import datetime
import json
import io
import sys
from time import sleep
from faulthandler import _read_null
# use newer, threading version, if available
if (sys.version_info[0] >= 3 and sys.version_info[1] >= 7):
    from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
else:
    from http.server import BaseHTTPRequestHandler, HTTPServer

import SerialArduinoGpioController


DEBUG = None

DEFAULT_LISTEN_ADDRESS = '0.0.0.0'    # respond to request from any address
DEFAULT_LISTEN_PORT = '10000'          # IP port 10000

DEFAULT_COM_PORT = '/dev/ttyUSB0'    # usual USB0 for Arduino on Raspberry Pi

DEFAULT_ICON_FILE_NAME = '/opt/Controllers/SerialArduinoGpio/favicon.ico'
FAVICON = None

DEFAULT_LOG_FILE_NAME = '/opt/Controllers/logs/SerialArduinoGpioServer.log'
log_file = None

#global holds the controller we are using
controller = None
controller_name = 'NA'


def log_event(output, event_text):
    '''
    send a line with an event to the output with a time stamp
    '''
    when = datetime.datetime.now(datetime.timezone.utc)
    when_str = when.isoformat()
    items = {'event':event_text,
             'time':when_str
             }
    output.write('{}\n'.format(json.dumps(items)))
    output.flush()

    
def collect_data():
    '''
    Get info from Arduino
    '''
    global controller
    global controller_name
    global log_file

    try:
        values = controller.read_pin_values()
        when = datetime.datetime.now(datetime.timezone.utc)
        when_str = when.isoformat()
        
        result = {'time':when_str,
                  'name':controller_name,
                  'values':values
                  }
        return result
    
    except Exception as e:
        event_text = 'While reading controller {} caught exception of {}.  removing'.format(ck, e)
        log_event(log_file, event_text)
        if DEBUG:
            print(event_text.format(),
                  file=sys.stderr, flush=True)

    
class Gpio_HTTPServer_RequestHandler(BaseHTTPRequestHandler):
    '''
    A subclass of BaseHTTPRequestHandler to provide GPIO output.
    '''

    def do_GET(self):
        '''
        handle the HTTP GET request
        '''
        global FAVICON
        global log_file

        if DEBUG:
            print('request path = "{}"'.format(self.path),
                  file=sys.stderr, flush=True)
        
#        log_event(log_file, 'request of "{}," from {}'.format(self.path,
#                                                               self.client_address))
        # deal with site ICON 
        if self.path == '/favicon.ico':
            self.send_response(200)
            self.send_header('Content-type','image/x-icon')
            self.end_headers()
            self.wfile.write(FAVICON)
            log_event(log_file, 'done sending favicon.ico of length {}'.format(len(FAVICON)))
            return
        
        # not the icon request, return data as json
        # Send response status code
        self.send_response(200)
        # Send headers
        self.send_header('Content-type','image/json')
        self.end_headers()

# TBD
        result = collect_data()
        self.wfile.write(bytes(json.dumps(result), "utf8"))
#        log_event(log_file, 'done sending response of  "{}"'.format(result))
        return
        
    
    def log_message(self, format, *args):
        '''
        Silence output from server
        '''
        return

#
# main
#
if __name__ == '__main__':
  
    parser = argparse.ArgumentParser(description='web server to capture data from Arduino running SerialArduionGpio code')
    parser.add_argument('-d', '--debug', 
                        help='turn on debugging', 
                        action='store_true')
    parser.add_argument('-a', '--address', 
                        help='v4 address for web server', 
                        default=DEFAULT_LISTEN_ADDRESS)
    parser.add_argument('-p', '--port', 
                        help='port number for web server', 
                        default=DEFAULT_LISTEN_PORT)
    parser.add_argument('-c', '--com_port', 
                        help='serial port for communication', 
                        default=DEFAULT_COM_PORT)
    parser.add_argument("-i", "--icon_filename", 
                        help="icon filenane", 
                        default=DEFAULT_ICON_FILE_NAME)
    parser.add_argument("-l", "--log_filename", 
                        help="file to log data, create or append", 
                        default=DEFAULT_LOG_FILE_NAME)
    args = parser.parse_args()

    if (args.debug):
        DEBUG = 1
        print('turned on DEBUG from command line.',
              file=sys.stderr, flush=True)

    log_filename = args.log_filename
    given_icon_filename = args.icon_filename
    given_address = args.address
    given_port = int(args.port)
    given_com_port = args.com_port

    server_address = (given_address, given_port)
    
    # open file to log pressure over time
    log_file = open(log_filename, 'a')
    log_event(log_file, 'STARTING SerialArduinoGpioServer')
    log_event(log_file, 'address: {}'.format(server_address))
    log_event(log_file, 'com port: {}'.format(given_com_port))
    log_event(log_file, 'icon filename: {}'.format(given_icon_filename))
        
    with open(given_icon_filename, 'rb') as icon_file:
        FAVICON = bytearray(icon_file.read())
    log_event(log_file, 'read icon file of length = {}'.format(len(FAVICON)))
    if DEBUG:
        print('read icon file of length = {}'.format(len(FAVICON)),
              file=sys.stderr, flush=True)
        print('log_filename = {}'.format(log_filename),
              file=sys.stderr, flush=True)
        print('server_address = {}'.format(server_address),
              file=sys.stderr, flush=True)
        print('com_port = {}'.format(given_com_port),
              file=sys.stderr, flush=True)

    try:
        controller = SerialArduinoGpioController.SerialArduinoGpioController(given_com_port)
        version = controller.get_version()
        if version >= 'V2':
            controller_name = controller.get_persistent_name()
        if DEBUG:
            print('found controller "{}" on port "{}" with version "{}"\n'.format(controller_name, given_com_port, version),
                  file=sys.stderr, flush=True)
            
        else:
            if DEBUG:
                print('controller on port "{}" has old version "{}"\n'.format(given_com_port, version),
                      file=sys.stderr, flush=True)
    except Exception as e:
        if DEBUG:
            print('while creating controller on port "{}" caught "{}"\n'.format(given_com_port, e),
                  file=sys.stderr, flush=True)


    # use newer, threading version, if available
    if (sys.version_info[0] >= 3 and sys.version_info[1] >= 7):
        httpd_server = ThreadingHTTPServer(server_address,
                                           Gpio_HTTPServer_RequestHandler)
    else:
        log_event(log_file, 'python version < 3.7 so using HTTPServer')
        httpd_server = HTTPServer(server_address,
                                  Gpio_HTTPServer_RequestHandler)
    
    if DEBUG:
        print('running server listening on {}...'.format(server_address),
              file=sys.stderr, flush=True)
    log_event(log_file, 'entering httpd_server.serve_forever()')
    httpd_server.serve_forever()
