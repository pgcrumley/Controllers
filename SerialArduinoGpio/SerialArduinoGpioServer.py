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

GET    PUT    URL
 Y            /          (usage as HTML)
 Y            /favicon
 Y            /version
 Y            /name
 Y            /analog_pins/<0-7>
 Y      Y     /digital_pins/<2-13>   (send '{"value":int}' with int of 0 or 1)
 
By default runs on IP v4 port 10000
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

DEFAULT_COM_PORT = '/dev/ttyUSB0'    # usual USB for Arduino on Raspberry Pi

DEFAULT_ICON_FILE_NAME = '/opt/Controllers/SerialArduinoGpio/favicon.ico'
FAVICON = None

DEFAULT_LOG_FILE_NAME = '/opt/Controllers/logs/SerialArduinoGpioServer.log'
log_file = None

USAGE_MESSAGE = ('<P>Welcome to the SerialArduinoGpioController</P>'
                 '<P>Valid URLs include:'
                 '<UL>'
                 '<LI><A HREF="/">/</A>'
                 '<LI><A HREF="/version">/version</A>'
                 '<LI><A HREF="/name">/name</A>'
                 '<LI><A HREF="/digital_pins">/digital_pins</A>'
                 '<LI><A HREF="/analog_pins">/analog_pins</A>'
                 '</UL>'
                 '</P>'
                 '<P>The latest code is available at <a HREF="https://github.com/pgcrumley/Controllers">my GitHub</A></P>'
                 )

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
    output.write(f'{json.dumps(items)}\n')
    output.flush()
    
class Gpio_HTTPServer_RequestHandler(BaseHTTPRequestHandler):
    '''
    A subclass of BaseHTTPRequestHandler to provide GPIO output.
    '''

    def do_GET(self):
        '''
        handle the HTTP GET request
        '''
        global FAVICON
        global USAGE_MESSAGE
        global log_file
        global controller

        if DEBUG:
            print(f'GET request path = "{self.path}"',
                  file=sys.stderr, flush=True)
        
        log_event(log_file, f'GET request of "{self.path}," from {self.client_address}')
        # deal with site ICON 
        if self.path == '/favicon.ico':
            self.send_response(200)
            self.send_header('Content-type','image/x-icon')
            self.end_headers()
            self.wfile.write(FAVICON)
            log_event(log_file, f'done sending favicon.ico of length {len(FAVICON)}')
            return
        
        # send a usage message 
        if self.path == '/':
            self.send_response(200)
            # Send headers
            self.send_header('Content-Type','text/html')
            self.end_headers()

            # Write content as utf-8 data
            self.wfile.write(bytes(USAGE_MESSAGE, 'utf8'))
            log_event(log_file, 'done sending USAGE_MESSAGE')
            return
        
        # not the icon request, determine request and return data as json
        try:
            if self.path == '/version':
                result = {'version':controller.get_version()}
            elif self.path == '/name':
                result = {'name':controller.get_persistent_name()}
            elif self.path == '/analog_pins':
                result = {'values':controller.read_analog_values()}
            elif self.path == '/digital_pins':
                result = {'values':controller.read_digital_values()}
            elif self.path.startswith('/analog_pins/'):
                pin = int(self.path.replace('/analog_pins/',''))
                result = {'value':controller.read_analog_value(pin)}
            elif self.path.startswith('/digital_pins/'):
                pin = int(self.path.replace('/digital_pins/',''))
                result = {'value':controller.read_digital_value(pin)}
            else:
                if DEBUG:
                    print('did not match a valid GET URL pattern',
                          file=sys.stderr, flush=True)
                raise Exception('unknown URL')
    
            # Send response status code
            self.send_response(200)
            # Send headers
            self.send_header('Content-type','text/json')
            self.end_headers()
            self.wfile.write(bytes(json.dumps(result), 'utf8'))
            log_event(log_file, f'done sending response of  "{result}"')
            if DEBUG:
                print('successful response returned',
                      file=sys.stderr, flush=True)
            return
        except Exception as e:
            if DEBUG:
                print(f'caught "{e}" in do_GET()',
                      file=sys.stderr, flush=True)
            # Bad Request
            self.send_response(400)
            # Send headers
            self.send_header('Content-Type','text/html')
            self.end_headers()
            result = '<H1>Bad Request</H1>' + \
                     '<P>Unsupported URL of <B>' + \
                      str(self.path) + \
                      '</B></P>' + \
                      str(USAGE_MESSAGE)
            # Write content as utf-8 data
            self.wfile.write(bytes(result, 'utf8'))
            log_event(log_file, 
                      f'done sending response to bad URL of "{self.path}"')
            if DEBUG:
                print('Bad Request response returned',
                      file=sys.stderr, flush=True)
            return
        
    
    def do_PUT(self):
        '''
        handle the HTTP PUT request
        '''
        global log_file
        global controller

        if DEBUG:
            print(f'PUT request path = "{self.path}"',
                  file=sys.stderr, flush=True)
            print(f'headers = "{self.headers}"', file=sys.stderr, flush=True)
        
        log_event(log_file, f'PUT request of "{self.path}," from {self.client_address}')
        result = {}
        try:
            if self.path.startswith('/digital_pins/'):
                content_len = int(self.headers['Content-Length'])
                put_body = self.rfile.read(content_len).decode('utf8')
                data = json.loads(put_body)
                value = int(data['value'])
                pin = int(self.path.replace('/digital_pins/',''))
                controller.set_digital_value(pin, value)
                result = {'value':value}
            else:
                if DEBUG:
                    print('did not match a valid GET URL pattern',
                          file=sys.stderr, flush=True)
                raise Exception('unknown URL')

            # Send response status code
            self.send_response(200)
            # Send headers
            self.send_header('Content-type','text/json')
            self.end_headers()
            self.wfile.write(bytes(json.dumps(result), 'utf8'))
            log_event(log_file, f'done sending response of  "{result}"')
            if DEBUG:
                print('successful response returned',
                      file=sys.stderr, flush=True)
            return
        except Exception as e:
            if DEBUG:
                print(f'caught "{e}" in do_PUT()',
                      file=sys.stderr, flush=True)
            # Bad Request
            self.send_response(400)
            # Send headers
            self.send_header('Content-Type','text/html')
            self.end_headers()
            result = '<H1>Bad Request</H1>' + \
                     '<P>Unsupported URL of <B>' + \
                      str(self.path) + \
                      '</B> or missing or incorrect <B>{"value":0|1}</B> in sent JSON ' + \
                      '</P>' + \
                      str(USAGE_MESSAGE) 
            # Write content as utf-8 data
            self.wfile.write(bytes(result, 'utf8'))
            log_event(log_file, 
                      f'done sending response to bad PUT request')
            if DEBUG:
                print('Bad Request response returned',
                      file=sys.stderr, flush=True)
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
    log_event(log_file, f'address: {server_address}')
    log_event(log_file, f'com port: {given_com_port}')
    log_event(log_file, f'icon filename: {given_icon_filename}')
        
    with open(given_icon_filename, 'rb') as icon_file:
        FAVICON = bytearray(icon_file.read())
    log_event(log_file, f'read icon file of length = {len(FAVICON)}')
    if DEBUG:
        print(f'read icon file of length = {len(FAVICON)}',
              file=sys.stderr, flush=True)
        print(f'log_filename = {log_filename}',
              file=sys.stderr, flush=True)
        print(f'server_address = {server_address}',
              file=sys.stderr, flush=True)
        print(f'com_port = {given_com_port}',
              file=sys.stderr, flush=True)

    try:
        controller = SerialArduinoGpioController.SerialArduinoGpioController(given_com_port)
        version = controller.get_version()
        if version >= 'V2':
            controller_name = controller.get_persistent_name()
        if DEBUG:
            print(f'found controller "{controller_name}" on port "{given_com_port}" with version "{version}"\n',
                  file=sys.stderr, flush=True)
            
        else:
            if DEBUG:
                print(f'controller on port "{given_com_port}" has old version "{version}"\n',
                      file=sys.stderr, flush=True)
    except Exception as e:
        if DEBUG:
            printf('while creating controller on port "{given_com_port}" caught "{e}"\n',
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
        print(f'running server listening on {server_address}...',
              file=sys.stderr, flush=True)
    log_event(log_file, 'entering httpd_server.serve_forever()')
    httpd_server.serve_forever()
