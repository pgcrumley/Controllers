# Serial Arduino GPIO Controller

This software, when used with an Arduino connected to a USB serial port
on a Raspberry Pi, Windows, or other type of system.  The software allows
the controlling system to read and set the values of
most GPIO pins on the Arduino.  (pins 0 and 1 are used by the serial 
port function).  It is also possible to read the values of the analog pins.

Since the Arduino gets power from the USB connection no
extra power supply is needed.  This arrangement allows the controlling
system to 
control powered devices with a less direct connection to hazardous voltages.

The use of USB allows relatively long distances
between the controlling system and the controlled device.  
(e.g. some USB extenders can 
reach 100 meters).  One may also have many GPIO ports on a single 
controlling system
by connecting many Arduinos (each supports 12 GPIO pins and 6 or more
analog signala) to USB ports.

The python code provides a simple interface to the functions, allowing one
to set a pin HIGH (which puts the pin in INPUT_PULLUP mode) or
LOW which (which sets OUTPUT mode with a value of LOW)

This use of a pullup for HIGH values allows pins to be used a inputs 
or outputs with minimal fuss or danger.

A command to save the current pin state to be used when the device is
reset is also provided as some devices need particular values at startup.

It is also possible to place a persistent name (16 characters) in to the 
Arduino so even if the USB ports get renamed over time you can keep track
of which Arduino is connected to various signals.
## Commands

Most commands are a single character in length.  The command to set an 
optional length is an exception as that has one character for the command 
followed by exactly 16 bytes of name.

### Commands to Retrieve Pin Data

Command | Description
------- | -----------
? | returns "xxx...xxx\n" where each x is a lower or UPPER case letter in the range of pins that the board supports to indicate if the pin is low or high.  For example an UNO returns "cdefghijklmn\n" as only those pins are supported.  Additionally, pins 0 and 1 are used for the serial port leaving pins 2-13 for use.
0-7 | return the value of the named analog input pin

### Commands to Control Pin Signals

Command | Description
------- | -----------
c-n | set pin 2-13 LOW and return nothing
C-N | set pin 2-13 HIGH (mode INPUT_PULLUP) and return nothing
\+ | saves the current state of the outputs to be restored at POWER-ON.


### Commands to Identify the Particular Devices

Command | Description
------- | -----------
` | returns the version and name of the Arduino sketch as a string
= | returns the 16 byte name from EEPROM as a string
\# | reads next 16 bytes from Serial and saves as name in EEPROM

Everything else received is ignored.

NOTE: This will work for first 14 pins on Arduino cards with more than 14 pins.

Version | Description
------- | -----------
0 | Initial version
1 | Aded analog capability
V2 | Added sketch name in version string and added ability to store a persistent name in EEPROM


### Configure the software (15 minutes -- longer if system is not up-to-date)

This is for Raspberry Pi or Ubuntu Linux.  Setup on other systems varies.

Install python3 using a command of:

    sudo apt-get -y install python3 python3-dev git
    
Install a python serial library using a command of:

    pip3 install -r requirements.txt

Make sure `python3` works and RPi.GPIO is installed by typing:

    python3
    import serial
    exit()

Your console should look like this:

    $ python3
    Python 3.4.2 (default, Oct 19 2014, 13:31:11)
    [GCC 4.9.1] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import serial
    >>> exit()
    $

The version numbers may vary but there should not be any messages after the
`import serial` line.    

### Install the software in the Raspberry Pi (5 minutes)

The software and scripts assume the software is installed in `/opt`, a
standard directory for "optional" software.  To install the software use

    sudo sh -c 'cd /opt ; git clone https://github.com/pgcrumley/Controllers.git'

This will place a copy of the software in `/opt` and leave behind
information that makes it easy to retrieve updates later if needed.

Next 

    cd /opt/Controllers/SerialArduinoGpio/
    
and make sure there are a number of python programs and other scripts present.

### Attach Arduino to development system and program sketch. (15 minutes)

If you are new to Arduino you probably want to do some of the
[tutorials](https://www.arduino.cc/en/Tutorial/HomePage)

If you use a system other than your Raspberry Pi as your Arduino development
system you will need to get a copy of the `SerialArduinoGpio.ino` file
to the development system.  

Attach your Arduino to your development computer (which might be your 
Raspbery Pi) and download the sketch called `SerialArduinoGpio.ino`
using the normal Arduino tools.  

You can use the serial port of the IDE to try out the operation of the 
Arduino.  Remember to set the serial port speed to 115200.

You can read all the pin values with '?'  The version command '`' (that 
is back-tic) prints a version number.

### Attach the Arduino to the Raspberry Pi USB port (2 minutes)

Once this is working attach the Arduino to a USB port on the Raspberry Pi.

If you programmed the Arduino on the same system it is already connected but
you may need to stop the Arduino IDE to release the serial port connection.

Look for the device in `/dev`.  It will have a name such as 
`/dev/ttyxxx#  ` where `xxx` is `ACM` or `USB` depending on the 
version of Arduino card you have and `#` is a number.

Try

    sudo python ./SerialArduinoGpioController.py <device-name>
    
and you should get some messages telling the card was found and is working:

    pgc@tjbot:~ $ sudo python ./SerialArduinoGpioController.py /dev/ttyACM0
	 made controller on port "/dev/ttyACM0"
	 serial_port: "/dev/ttyACM0":
    persistent name: "????????????????"
    code version is: "V2_SerialArduinoGpio"
	 reading pins gives "{2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1, 13: 0}"
	 analog values are {0: 464, 1: 413, 2: 374, 3: 343, 4: 311, 5: 287, 6: 299, 7: 309}

    pgc@tjbot:~ $

If you don't see something like the above there is a problem.

Note:  If your Arduino had values written to the EEPROM the pins might not
start off as `1`.  Also, if there are previous values in the EEPROM you 
might see some other persistent name.
 
 
### Enjoy! 






