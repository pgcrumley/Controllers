/*
MIT License

Copyright (c) 2018, 2019 Paul G Crumley

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
 */

/*
This provides a very simple program which takes commands from the serial
port and sets the pins to either a HIGH state (by setting the mode to
INPUT_PULLUP) or a LOW state (by setting the mode to OUTPUT and the value
to LOW).

To use a pin as an INPUT set the output HIGH.  There will be a weak pullup
on the pin so make sure input signals have a relatively low impedance.

The initial pin values are read from EEPROM.  The "shipped" version of ARDUINO
parts will default to setting the pins HIGH.  This allows one to create
projects that safely use the pins as inputs with new cards.

Other values for the initial state can be saved with the '+' command.

The analog pins can also be read with commands of '0'-'7'.  The value
read (0-1023) will be returned.

Very simple commands:  'a-n', 'A-N', '?', '+'
  0-7 return the value of the named analog input pin
  c-n set pin 2-13 LOW and return nothing
  C-N set pin 2-13 HIGH (mode INPUT_PULLUP) and return nothing
  ? returns "xxx...xxx\n" where each x is a lower or UPPER case letter in the
    range of pins that the board supports to indicate if the pin is low or high
    For example an UNO returns "cdefghijklmn\n" as only those pins are
    supported.  Additionally, since pins 0 and 1 are used for the serial port
    leaving pins 2-13 for use.
  + saves the current state of the outputs to be restored at POWER-ON.
  ` returns the version and name of the code as a string
  = returns the 16 byte name from EEPROM as a string
  # reads next 16 bytes from Serial and saves as name in EEPROM

Everything else received is ignored.

NOTE: This will work for first 14 pins on Arduino cards with more than 14 pins.

Version
0       initial version
1       added analog capability
V2      added sketch name in version string
		added ability to store a persistent name in EEPROM

 */
#include <EEPROM.h>

#define DEBUG 0
#define SERIAL_BAUD_RATE 115200

/* allow control of these pins */
/*                           c  d  e  f  g  h  i  j   k   l   m   n */
const byte PINS_TO_USE[] = { 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 };
/* pins 0 & 1 are used for serial communication so may not be altered */

/* where we place the 16 bytes of name in EEPROM */
const int EEPROM_NAME_OFFSET = 64;
/* exact size of name in EEPROM */
const int EEPROM_NAME_SIZE = 16;

const char VERSION[] = "V2_SerialArduinoGpio";

/*
 Set the value for a pin.
 */
void set_pin(int pin, int state) {
	if (state) {
		pinMode(pin, INPUT_PULLUP);
	} else {
		pinMode(pin, OUTPUT);
		digitalWrite(pin, LOW);
	}
}

/*
 Standard Arduino setup function -- runs once at restart.
 */
void setup(void) {
	for (unsigned int i = 0; i < sizeof(PINS_TO_USE); i++) {
		int pin = PINS_TO_USE[i];
		set_pin(pin, EEPROM[pin]);
	}

	Serial.begin(SERIAL_BAUD_RATE);
	while (!Serial) {
		; // wait for serial port to connect. Needed for native USB port only
	}
}

/*
 Send back a string with the current pin states.
 */
void sendValues() {
	char output_str[] = "cdefghijklmn\n";
	for (unsigned int i = 0; i < sizeof(PINS_TO_USE); i++) {
		if (LOW == digitalRead(PINS_TO_USE[i])) {
			output_str[i] = 'c' + i;
		} else {
			output_str[i] = 'C' + i;
		}
	}
	Serial.print(output_str);
} // sendValues

/*
 Send back a string with the analog value of a pin.
 */
void sendAnalog(int pin) {
	int value = analogRead(pin);
	Serial.println(value);
} // sendAnalog(int pin)

/*
 Save current pin states for use at next power on.
 */
void saveValues() {
	for (unsigned int i = 0; i < sizeof(PINS_TO_USE); i++) {
		int pin = PINS_TO_USE[i];
		EEPROM.update(pin, digitalRead(pin));
	}
} // saveValues

/*
 Retrieve EEPROM_NAME_SIZE bytes of the name from EEPROM and send to Serial
 */
void retrieveName() {
	char name[EEPROM_NAME_SIZE+1]; // extra space for \0
	for (unsigned int i = 0; i < sizeof(name); i++) {
		char c = EEPROM[EEPROM_NAME_OFFSET + i];
		if ((c < ' ') || (c > '~')) {
			c = '?';
		}
		name[i] = c;
	}
	name[EEPROM_NAME_SIZE] = '\0';
	Serial.println(name);
}

/*
 Read next EEPROM_NAME_SIZE characters from Serial and save those to EEPROM
 */
void saveName() {
	char name[EEPROM_NAME_SIZE];
	for (unsigned int i = 0; i < sizeof(name); i++) {
		char c = -1;
		while (-1 == (c = Serial.read())) {
		}
		if ((c < ' ') || (c > '~')) {
			c = '_';
		}
		EEPROM[EEPROM_NAME_OFFSET + i] = c;
	}
}

void loop(void) {
	/* wait till the controller tells us to do something by sending a '\n' */
	char c;
	while (-1 == (c = Serial.read())) {
	}
	if (DEBUG) {
		Serial.print("Command: 0x");
		Serial.println(c, HEX);
	}

	if (('c' <= c) && ('n' >= c)) {
		set_pin(c - 'a', LOW);
		return;
	}
	if (('C' <= c) && ('N' >= c)) {
		set_pin(c - 'A', HIGH);
		return;
	}
	if ('?' == c) {
		sendValues();
		return;
	}
	/* read analog inputs */
	if (('0' <= c) && ('7' >= c)) {
		sendAnalog(c-'0');
		return;
	}
	if ('+' == c) {
		saveValues();
		return;
	}
	if ('`' == c) {
		Serial.println(VERSION);
		return;
	}
	if ('=' == c) {
		retrieveName();
		return;
	}
	if ('#' == c) {
		saveName();
		return;
	}

	if ('\n' == c) {
		// ignore new line characters
		return;
	}

	if (DEBUG) {
		Serial.println("got unknown command");
	}

} // loop()
