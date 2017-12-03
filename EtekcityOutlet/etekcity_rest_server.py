#!/usr/bin/env python3
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

Very simple web server to control Etekcity relays using a 433 MHz transmitter
connected to a Raspberry Pi pin.

Send a JSON dictionary with keys of:
  "addr" (0-255)
  "unit" (1-5)
  "action" ("on"|"off")
  optional "pin" (valid board pin number)
The default pin number is 18.

try a curl command such as:
  curl -H 'Content-Type: application/json' -X POST -d '{"addr":21, 
    "unit":1, "action": "on"}'  http://localhost:11111/

The server must run as root to have access to the GPIO pins.

"""

import datetime
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

from etekcity_controller import Transmitter

DEBUG = 0

DEFAULT_LISTEN_ADDRESS = '127.0.0.1' # responds to only requests from localhost
#DEFAULT_LISTEN_ADDRESS = '0.0.0.0'  # respond to request from any address
DEFAULT_LISTEN_PORT = 11111                 # IP port
DEFAULT_SERVER_ADDRESS = (DEFAULT_LISTEN_ADDRESS, DEFAULT_LISTEN_PORT)

USE_MESSAGE = ('send a JSON dictionary with keys of '
               '<UL>'
               '<LI>"addr" (0-255)'
               '<LI>"unit" (1-5)'
               '<LI>"action" ("on"|"off")'
               '<LI>optional "pin" (valid board pin number)'
               '</UL>'
               )

DEFAULT_PIN = 18


class Simple_RequestHandler(BaseHTTPRequestHandler):
    '''
    A subclass of BaseHTTPRequestHandler for our work.
    '''
    
    
    def do_GET(self):
        '''
        handle the HTTP GET request
        '''        
        if DEBUG:
            print('got GET request', file=sys.stderr)

        # Send response status code
        self.send_response(200)
 
        # Send headers
        self.send_header('Content-type','text/html')
        self.end_headers()

        # Write content as utf-8 data
        self.wfile.write(bytes(USE_MESSAGE, 'utf8'))
        return


    def do_POST(self):
        '''
        handle the HTTP POST request
        '''
        if DEBUG:
            print('got POST request', file=sys.stderr)
            print(self.headers, file=sys.stderr)
        content_len = int(self.headers['Content-Length'])
        post_body = self.rfile.read(content_len).decode('utf8')
        if DEBUG:
            print('post_body: "{}"'.format(post_body), file=sys.stderr)     
        data = json.loads(post_body)
        if DEBUG:
            print('post data: "{}"'.format(data), file=sys.stderr)

        try:
            pin_num = DEFAULT_PIN
            if 'pin' in data:
                pin_num = data['pin']
            addr_num = data['addr']
            unit_num = data['unit']
            action = data['action']
        
            if DEBUG:
                print('pin:     {}'.format(pin_num), file=sys.stderr)
                print('addr:    {}'.format(addr_num), file=sys.stderr)
                print('unit:    {}'.format(unit_num), file=sys.stderr)
                print('action:  {}'.format(action), file=sys.stderr)
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write(bytes(USE_MESSAGE, 'utf8'))
            return

        
        ec = Transmitter(pin_num)    
        ec.transmit_action(addr_num, unit_num, action)

        # Send response status code
        self.send_response(200)

        # Send headers
        self.send_header('Content-type','application/json')
        self.end_headers()

        result=[]
        sample = {}
        sample['status'] = 200
        sample['pin'] = pin_num
        sample['addr'] = addr_num
        sample['unit'] = unit_num
        sample['action'] = action
        result.append(sample)

        self.wfile.write(bytes(json.dumps(result, indent=1), "utf8"))
        return
 
 
def run():
    httpd_server = HTTPServer(DEFAULT_SERVER_ADDRESS, Simple_RequestHandler)
    print('running server listening on {}...'.format(DEFAULT_SERVER_ADDRESS))
    httpd_server.serve_forever()

if '__main__' == __name__:
    try:
        run()
    except Exception as ex:
        print('caught "{}"'.format(ex))
