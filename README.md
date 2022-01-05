# Controllers

This project holds code to control various devices which are
attached to a Raspberry Pi.  The `SerialArduinoGpio` controller can  
also be attached to other types of host system (e. g. Raspberry Pi, Linux systems).

The code and ancillary files assume the projects are placed in /opt.  A simple 
  `sudo sh -c 'cd /opt ; git clone https://github.com:pgcrumley/Controllers.git'`
will put the code in the appropriate location.
The code can then be updated with `git pull` commands run as root.
An example would be: `sudo bash -c 'cd /opt ; git pull'`
  
The Etekcity Outlet controller connects to a Raspberry Pi using pins for 3.3V, GND and Board pin 18

The SerialArduinoGpio device connects using a USB port.
    
Simple web servers are provided for the controllers.

The EtekCity server 
only allows programs on the Raspberry Pi which is running the REST server to 
access the device.  

The SerialArduinoGpioServer REST server allows access to any program with
network connectivity by default.

In addition to the REST servers, `python` code can control both of these controllers.

The REST servers use JSON format for the data which sent to control
the devices.  

The default port numbers for the REST servers are:

  Port | Device
  -----: | -------
  11111 | [Etekcity Outlet](./Etekcity/) Controller
  10000 | SerialArduinoGpioServer
  
  