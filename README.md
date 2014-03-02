ConfPlate is a configuration file generator. After doing some configurations over and over again I got bored and built this script. Boring tasks often lead to mistakes in configurations which you want to avoid I assume.

The script is based on Python and uses Jinja2 as template language. Due to the lack of error handling and not enough
testing some features supported by Jinja2 might not work (template inheritence, for loops, ...) yet.


Design goals
============

* Code should run on Linux, OSX, Windows
* Simplicity (Just generate configs from a template. No querying of other devices via SNMP for input, yadayada...)
* Userfriendly command line interface
* Make it easy to create UIs on top of the main code base


Usage Examplse
==============

Example template cat3560.txt:

	hostname {{HOSTNAME|lower}}
	!
	ip domain name {{DOMAINNAME}}
	!
	interface range FastEthernet0/1 - 24
	 swtichport mode access
	 switchport access vlan {{ACCESS_VLAN}}
	 switchport nonegotiate
	 no shut
	!
	interface {{MGMT_IFACE}}
	 ip address {{MGMT_IFACE_IP}} {{MGMT_IFACE_NM}}
	!
	ip default-gateway {{MGMT_DEFAULT_GW}}


This template makes use of Jinja2 filters in the HOSTNAME variable. The value for the
hostname variable will always be converted to lower case.


Get a list of variables used in a template
------------------------------------------

	$ ./confplate.py -l examples/cat3560.txt 
	 
	Variables used in template cat3560.txt

		ACCESS_VLAN
		DOMAINNAME
		HOSTNAME
		MGMT_DEFAULT_GW
		MGMT_IFACE
		MGMT_IFACE_IP
		MGMT_IFACE_NM


Interactive mode
----------------

Will prompt you for every variable used in the template


	$ ./confplate.py examples/cat3560.txt
	ACCESS_VLAN: 23
	DOMAINNAME: lab.verbosemo.de
	HOSTNAME: brewery-sw010
	MGMT_IFACE: Vlan200
	MGMT_IFACE_IP: 10.33.200.10
	MGMT_IFACE_NM: 255.255.255.0
	MGMT_DEFAULT_GW: 10.33.200.1


Variables as arguments
----------------------

Set all variable values as arguments on the command line


	./confplate.py examples/cat3560.txt ACCESS_VLAN=23 DOMAINNAME=lab.verbosemo.de HOSTNAME=brewery-sw010 MGMT_IFACE=Vlan200 MGMT_IFACE_IP=10.33.200.10 MGMT_IFACE_NM=255.255.255.0 MGMT_DEFAULT_GW=10.33.200.1


Bulk configuration
------------------

* Variable values read from CSV file
* Creates config per line in CSV file


new-subnets.csv

	VLAN_ID,VLAN_NAME,IP,NM,HSRP_IP,IP_HELPER
	40,Floor1,192.168.40.2,255.255.255.0,192.168.40.1,192.168.100.100
	50,Floor2,192.168.50.2,255.255.255.0,192.168.50.1,192.168.100.100
	60,Floor3,192.168.60.2,255.255.255.0,192.168.60.1,192.168.100.100

new-subnets.txt

	vlan {{VLAN_ID}}
	 name {{VLAN_NAME}}
	!
	interface Vlan{{VLAN_ID}}
	 ip address {{IP}} {{NM}}
	 ip ospf 1 area 0.0.0.0
	 ip ospf passive-interface
	 ip helper-address {{IP_HELPER}}

Use new-subnets.csv as input and create a config per line

	$ ./confplate.py -i examples/new-subnets.csv examples/new-subnets.txt 
	vlan 40
	 name Floor1
	!
	interface Vlan40
	 ip address 192.168.40.2 255.255.255.0
	 ip ospf 1 area 0.0.0.0
	 ip ospf passive-interface
	 ip helper-address 192.168.100.100

	vlan 50
	 name Floor2
	!
	interface Vlan50
	 ip address 192.168.50.2 255.255.255.0
	 ip ospf 1 area 0.0.0.0
	 ip ospf passive-interface
	 ip helper-address 192.168.100.100

	vlan 60
	 name Floor3
	!
	interface Vlan60
	 ip address 192.168.60.2 255.255.255.0
	 ip ospf 1 area 0.0.0.0
	 ip ospf passive-interface
	 ip helper-address 192.168.100.100

Generate a CSV header from an existing template. This should make generating a CSV header in your favourite spreadsheet application manually unnecessary


	$ ./confplate.py --generate-csv-header examples/cat3560.txt
	ACCESS_VLAN,DOMAINNAME,HOSTNAME,MGMT_DEFAULT_GW,MGMT_IFACE,MGMT_IFACE_IP,MGMT_IFACE_NM
	
	$ ./confplate.py --generate-csv-header examples/cat3560.txt > /tmp/cat3560.csv
	
	$ ./confplate.py -g -F ";" examples/cat3560.txt 
	ACCESS_VLAN;DOMAINNAME;HOSTNAME;MGMT_DEFAULT_GW;MGMT_IFACE;MGMT_IFACE_IP;MGMT_IFACE_NM



**Feedback, bug reports and patches are welcome.**


Links
-----

http://jinja.pocoo.org/docs/

