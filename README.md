# Controllers

This project holds code to control various devices which are
attached to Raspberry Pi systems.

The code and ancillary files assume the project is placed in /opt.  A simple 
  `sudo sh -c 'cd /opt ; git clone https://github.com:pgcrumley/Controllers.git'`
will put the code in the appropriate location.  
The code can then be updated with `git pull` commands run as root.
An example would be: `sudo bash -c 'cd /opt ; git pull'`
  
The devices attach to the Raspberry Pi in a variety of ways including:

    Other GPIO pins (you pick, stay away predefined pins)
    Etekcity Outlet controller connects to 3.3V, GND and Board pin 18
    
Simple web servers are provided for the controllers.  By default these 
only allow programs on the Raspberry Pi which with the running REST server to 
access the device.  The REST servers can be configured with command line
parameters to move the port or allow access from other systems.

The REST servers use JSON format for the data which sent to control
the devices.  

The default port numbers for the REST servers are:

  Port | Device
  -----: | -------
  11111 | [Etekcity Outlet](./Etekcity/) Controller
  22222 | GPIO on Arduino
  
  Note:  The REST server for GPIO on Arduino is not available at this time
  
  