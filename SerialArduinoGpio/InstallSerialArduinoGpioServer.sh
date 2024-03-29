#!/bin/sh
# MIT License
#
# Copyright (c) 2021 Paul G Crumley
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# @author: pgcrumley@gmail.com
#

if [ $# -lt 1 ]; then
    echo "using default COM port of /dev/ttyUSB0"
    sed -e "s;REPLACE-COM-ARG; -c ${1};" \
      < /opt/Controllers/SerialArduinoGpio/SerialArduinoGpioServer.service \
      > /lib/systemd/system/SerialArduinoGpioServer.service
else
    echo "adding ' -c ${1}' to exec command"
    sed -e "s;REPLACE-COM-ARG;;" \
      < /opt/Controllers/SerialArduinoGpio/SerialArduinoGpioServer.service \
      > /lib/systemd/system/SerialArduinoGpioServer.service
fi

pip3 install -r requirements.txt

mkdir -p /opt/Controllers/logs

systemctl enable SerialArduinoGpioServer
systemctl start SerialArduinoGpioServer
