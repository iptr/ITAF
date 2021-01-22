#!/usr/bin/python

import sys
import telnetlib as tl

if __name__ == '__main__':
	tel = tl.Telnet("192.168.6.102")
	tel.read_until("login: ")
	tel.write("root\n")
	tel.read_until("Password: ")
	tel.write("PNPsecure00))\n")
	tel.write("ls -al\n")
	print(tel)
