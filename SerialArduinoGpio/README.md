# Serial Arduino GPIO Controller

This software, when used with an Arduino connected to a USB serial port
on a Raspberry Pi, allows the Raspberry Pi to read and set the values of
most GPIO pins on the Arduino.  (pins 0 and 1 are used by the serial 
port function)  

Since the Arduino gets power from the USB connection no
extra power supply is needed.  This arrangement allows a Raspberry Pi to 
control powered devices with a less
direct connection to hazardous voltages.

The use of USB allows longer distances
between the Raspberry Pi and the controlled device.  (some extenders can 
reach 100 meters).  One may also have many GPIO ports on a single Raspberry
Pi by connecting many Arduinos (each supports 12 GPIO pins) to USB ports.

The python code provides a simple interface to the functions, allowing one
to set a pin HIGH (which is really putting the pin in INPUT_PULLUP mode) or
LOW which (which sets OUTPUT mode with a value of LOW)

This allows the pins to be used a inputs or outputs with minimal fuss.

A command to save the current pin state to be used when the device is
reset is also provided as some devices need particular values at startup.

### Configure the software (15 minutes -- longer if system is not up-to-date)

Install python3 and the RPi.GPIO library using a command of:

    sudo apt-get -y install python3 python3-dev git python3-rpi.gpio

Make sure `python3` works and RPi.GPIO is installed by typing:

    python3
    import RPi.GPIO
    exit()

Your console should look like this:

    $ python3
    Python 3.4.2 (default, Oct 19 2014, 13:31:11)
    [GCC 4.9.1] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import RPi.GPIO
    >>> exit()
    $

The version numbers may vary but there should not be any messages after the
`import RPi.GPIO` line.    

### Install the software in the Raspberry Pi (5 minutes)

The software and scripts assume the software is installed in `/opt`, a
standard directory for "optional" software.  To install the software use

    sudo sh -c 'cd /opt ; git clone https://github.com/pgcrumley/Controllers.git'

This will place a copy of the software in `/opt` and leave behind
information that makes it easy to retrieve updates later if needed.

Next 

    cd /opt/Controllers/SerialArduinoGpio/
    
and make sure there are
a number of python and other scripts present.

### Attach Arduino to development system and program sketch. (15 minutes)

If you are new to Arduino you probably want to do some of the basic tutorials
first.  See TBD

If you use a system other than your Raspberry Pi as your Arduino development
system you will need to get a copy of the `SerialArduinoGpio.ino` file
to the development system.  

Attach your Arduino to your development computer (which might be your 
Raspbery Pi) and download the sketch called `SerialArduinoGpio.ino`
using the normal Arduino tools.  

You can use the serial port of the IDE to try out the operation of the 
Arduino.  Remember to set the serial port speed to 115200.

On most Arduino boards the LED is on GPIO pin 13 so you can turn it on
and off by sending 'n' and 'N' characters.  You can read all the pin
values with '?'

### Attach the Arduion to the Raspberry Pi USB port (5 minutes)

Once this is working attach the Arduino to a USB port on the Raspberry Pi.

Look for the device in `/dev`.  It will have a name such as 
`/dev/ttyxxx#  ` where `xxx` is `AMC` or `USB` depending on the 
version of Arduino card you have and `#` is a number.

Try

    sudo python ./SerialArduinoGpioController.py
    
and you should get some messages telling the card was found and is working:

    pgc@tjbot:~ $ sudo python ./SerialArduinoGpioController.py
    reading pins /dev/ttyACM0: {2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1, 13: 1}
    
    set pin 5 on /dev/ttyACM0 LOW
    
    reading pins /dev/ttyACM0: {2: 1, 3: 1, 4: 1, 5: 0, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1, 13: 1}
    
    set pin 5 on /dev/ttyACM0 HIGH
    
    reading pins /dev/ttyACM0: {2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1, 13: 1}
    
    saving reset state of /dev/ttyACM0
    
    pgc@tjbot:~ $

If you don't see something like the above there is a problem.

Note:  If your Arduino had values written to the EEPROM the pins might not
start off as `1`.
 

 
### Enjoy! 







