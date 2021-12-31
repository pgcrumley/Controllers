/*
MIT License

Copyright (c) 2018, 2021 Paul G Crumley

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
This provides an Arduino program which takes commands from the serial
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

The digital pins can be placed in a monitor mode which will watch the pins
and when debounced changes are detected, asynchronously send the change
with a single character (c-n for a change to low, C-N for a change to high)
followed by a NL character.

All messages are returned without interruption, so, for example, the response
to the '?', '0'-'9', '=', '-', or '`' commands will be returned in full
before an asynchronous event message is sent.

Signals are "debounced" and a stable signal must be observed for at least 3
consecutive observations separated by no less than 1 mSec.

All messages from the device end with a \n character.

Commands:
  0-7 return the value of the named analog input pin
  c-n set pin 2-13 LOW and return nothing
  C-N set pin 2-13 HIGH (mode INPUT_PULLUP) and return nothing
  ? returns "xxx...xxx\n" where each x is a lower or UPPER case letter in the
    range of pins that the board supports to indicate if the pin is low or high
    For example an UNO returns "cdefghijklmn\n" as only those pins are
    supported.  Additionally, pins 0 and 1 are used for the serial port
    leaving pins 2-13 for use.
  + saves the current state of the outputs to be restored at POWER-ON.
  - returns the current values restored at POWER-ON
  }x places pin x in  monitor mode (x is C-N)
  {x removes pin x from monitor mode (x is C-N)
  ` returns the version and name of the code as a string
  = returns the 16 byte name from EEPROM as a string
  # reads next 16 bytes from Serial and saves as name in EEPROM
Everything else received is ignored.

NOTES:
- This will work for first 14 pins on Arduino cards with more than 14 pins.
- Monitor mode is off at POWER-ON and the setting is not saved across reboot.

Version History:
0   Initial version
1   Added analog capability
V2  Added sketch name in version string
    Added ability to store a persistent name in EEPROM
V3  Added '-', '{', and '}' commands.  Cleaned up some of the implementation.

Note to implementors:  Remaining characters for commands:
    !"$%&'()*,./:;<>@[\]^_{|}~

Note to implementors:  While creating this code some odd behaviors were
    observed in requiring a delay in the main loop.
    I did not debug this to root cause but accepted that the 1 mSec delay would
    cause the problem to not occur.  pgc
 */

#include <EEPROM.h>

#define DEBUG 0
#define SERIAL_BAUD_RATE 115200

#define FIRST_VALID_PIN 2
#define LAST_VALID_PIN 13
/* allow control of these pins */
/*                           c  d  e  f  g  h  i  j   k   l   m   n */
const byte PINS_TO_USE[] = { 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 };
/* pins 0 & 1 are used for serial communication so may not be altered */

/* where we place the 16 bytes of name in EEPROM */
const int EEPROM_NAME_OFFSET = 64;
/* exact size of name in EEPROM */
const int EEPROM_NAME_SIZE = 16;

const char VERSION_STRING[] = "V3_SerialArduinoGpio\n";


/* has some extra slots       0      1      2      3      4 */
bool monitor_active[] = { false, false, false, false, false,
/*                            5      6      7      8      9 */
                          false, false, false, false, false,
/*                           10,    11,    12     13     14 */
                          false, false, false, false, false
};
/* also extra slots      0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 */
int  monitor_states[] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};

#define STATE_RESET 0
#define STATE_1_ZERO 1
#define STATE_2_ZEROES 2
#define STATE_3_ZEROES 3
#define STATE_SPARE 4
#define STATE_1_ONE 5
#define STATE_2_ONES 6
#define STATE_3_ONES 7


/*
 Set the value for a pin.
 */
void setPin(int pin, int state) {
	if (state) {
		pinMode(pin, INPUT_PULLUP);
	} else {
		pinMode(pin, OUTPUT);
		digitalWrite(pin, LOW);
	}
}

/*
 Send back a string with the current pin states.
 */
void retrieveValues() {
	char output_str[] = "cdefghijklmn\n"; // string includes final null
	for (unsigned int i = 0; i < sizeof(PINS_TO_USE); i++) {
		if (LOW == digitalRead(PINS_TO_USE[i])) {
			output_str[i] = 'c' + i;
		} else {
			output_str[i] = 'C' + i;
		}
	}
	Serial.print(output_str);
} /* end of retrieveValues() */

/*
 Send back a string with the analog value of a pin.
 */
void retrieveAnalog(int pin) {
	int value = analogRead(pin);
	Serial.print(value);
	Serial.print('\n');
} /* end of retrieveAnalog(int pin) */

/*
 Save current pin states for use at next power on.
 */
void savePowerOnValues() {
	for (unsigned int i = 0; i < sizeof(PINS_TO_USE); i++) {
		int pin = PINS_TO_USE[i];
		EEPROM.update(pin, digitalRead(pin));
	}
} /* savePowerOnValues() */

/*
 Save current pin states for use at next power on.
 */
void retrievePowerOnValues() {
	char output_str[] = "cdefghijklmn\n"; // string includes final null
	for (unsigned int i = 0; i < sizeof(PINS_TO_USE); i++) {
		int pin = PINS_TO_USE[i];
		if (EEPROM[pin]) {
			output_str[i] = 'C' + i;
		} else {
			output_str[i] = 'c' + i;
		}
	}
	Serial.print(output_str);


} /* end of retrievePowerOnValues() */

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
	Serial.print(name);
	Serial.print('\n');
} /* end of retrieveName() */

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
} /* end of saveName() */

/*
 * Register a pin to be monitored.
 */
void startMonitoringPin() {
	int pin = Serial.read() - 'A';
	if ((pin >= FIRST_VALID_PIN) && (pin <= LAST_VALID_PIN)) {
		monitor_active[pin] = true;
		if (digitalRead(pin)) {
			monitor_states[pin] = STATE_3_ONES;
		} else {
			monitor_states[pin] = STATE_3_ZEROES;
		}
	}
} /* end of startMonitoringPin(pin) */

/*
 * Unregister a pin to be monitored.
 */
void stopMonitoringPin() {
	int pin = Serial.read() - 'A';
	if ((pin >= FIRST_VALID_PIN) && (pin <= LAST_VALID_PIN)) {
		monitor_active[pin] = false;
	}
} /* end of stopMonitoringPin(pin) */

/*
 * For each pin that is being monitored, check for changes and emit a
 * message if a change is found.
 */
void lookForChanges() {
  if (DEBUG) {
    Serial.print("in lookForChanges()\n");
  }
	for (unsigned int i = 0; i < sizeof(PINS_TO_USE); i++) {
		int pin = PINS_TO_USE[i];
		int value = digitalRead(pin);
/*    if (DEBUG) {
        Serial.println(pin);
        Serial.println(value);
        Serial.println(monitor_active[pin]);
        Serial.println(monitor_states[pin]);
      } */
		if (monitor_active[pin]) {
      int last_state = monitor_states[pin];
			switch (last_state) {
			/* case STATE_RESET: // same as default case so save some code
				monitor_state[pin] = (value ? STATE_1_ONE : STATE_1_ZERO);
				break; */
			case STATE_1_ZERO:
				monitor_states[pin] = (value ? STATE_1_ONE : STATE_2_ZEROES);
				break;
			case STATE_2_ZEROES:
				if (value) {
					monitor_states[pin] = STATE_1_ONE;
				} else {
					monitor_states[pin] = STATE_3_ZEROES;
          char message = 'a'+pin;
          Serial.print(message);
					Serial.print('\n');
				}
				break;
			case STATE_3_ZEROES:
				monitor_states[pin] = (value ? STATE_1_ONE : STATE_3_ZEROES);
				break;
			case STATE_1_ONE:
				monitor_states[pin] = (value ? STATE_2_ONES : STATE_1_ZERO);
				break;
			case STATE_2_ONES:
			  if (value) {
          char message = 'A'+pin;
				  Serial.print(message);
				  Serial.print('\n');
				  monitor_states[pin] = STATE_3_ONES;
		  	} else {
			  	monitor_states[pin] = STATE_1_ZERO;
		  	}
				break;
			case STATE_3_ONES:
				monitor_states[pin] = (value ? STATE_3_ONES : STATE_1_ZERO);
				break;
			default:
				monitor_states[pin] = (value ? STATE_1_ONE : STATE_1_ZERO);
				break;
			} /* switch (monitor_state[pin]) */
		} /* if (monitor_active[pin]) */
	} /* for (unsigned int i = 0; i < sizeof(PINS_TO_USE); i++) */
} /* end of lookForChanges() */

/*
 * Determine what to do when a command is received.
 */
void decodeCommand(int c) {
    if (('c' <= c) && ('n' >= c)) {
      setPin(c - 'a', LOW);
    } else if (('C' <= c) && ('N' >= c)) {
      setPin(c - 'A', HIGH);
    } else if ('?' == c) {
      retrieveValues();
    } else if (('0' <= c) && ('7' >= c)) {
      retrieveAnalog(c-'0');
    } else if ('+' == c) {
      savePowerOnValues();
    } else if ('-' == c) {
      retrievePowerOnValues();
    } else if ('`' == c) {
      Serial.print(VERSION_STRING);
    } else if ('=' == c) {
      retrieveName();
    } else if ('#' == c) {
      saveName();
    } else if ('}' == c) {
      startMonitoringPin();
    } else if ('{' == c) {
      stopMonitoringPin();
    } else if ('\n' == c) {
      /* ignore this */
    } else if (DEBUG) {
      Serial.print("got unknown command\n");
    }

} /* end of decodeCommand(int c) */


/*
 Standard Arduino setup() function -- runs once at restart.
 */
void setup(void) {
	for (unsigned int i = 0; i < sizeof(PINS_TO_USE); i++) {
		int pin = PINS_TO_USE[i];
		setPin(pin, EEPROM[pin]);
	}

	Serial.begin(SERIAL_BAUD_RATE);
	while (!Serial) {
		; // wait for serial port to connect. Needed for native USB port only
	}
}

/*
 * The usual Arduino loop() function -- goes "forever"
 */
void loop(void) {
  /* go around no faster than once per mSec */
  delay(1);
  /* handle a command if one is received */
	char c = Serial.read();
	if (c > 0) {
    if (DEBUG) {
			Serial.print("Command: 0x");
			Serial.print(c, HEX);
			Serial.print('\n');
		}
    decodeCommand(c);
	}

	/* Look for changes since last samples */
  lookForChanges();
} // loop()
