#!/usr/bin/env python

#IR Photon Emitter Service

import RPi.GPIO as GPIO
import select
import socket
import json
import sys

sys.path.insert(0, '/var/scripts/ir-photon-emitter')

import irpe_config

config = irpe_config.IRPE_Config()



#Pin Definitons
pin1 = 17
pin2 = 18

GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
GPIO.setup(pin1, GPIO.OUT)
GPIO.setup(pin2, GPIO.OUT) 

GPIO.output(pin1, GPIO.LOW)
GPIO.output(pin2, GPIO.LOW)



# Create a UDP socket 
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(0)
server_address = (config.serverIP, config.serverPort)
		
# Bind the socket to the port	
while True:
	try: 
		sock.bind(server_address)
		break
	except:
		sleep(5)
		
		
		
def TurnOn(level):
	GPIO.output(pin1, GPIO.HIGH)
	GPIO.output(pin2, GPIO.HIGH)

def TurnOn_Half(level):
	GPIO.output(pin1, GPIO.HIGH)
	GPIO.output(pin2, GPIO.LOW)

def TurnOff():
	GPIO.output(pin1, GPIO.LOW)
	GPIO.output(pin2, GPIO.LOW)

	
		
		


#Inputs to monitor
inputs = [sock]

#Main Loop
if __name__ == "__main__":

	while inputs:
	
		# Wait for at least one of the sockets to be ready for processing
		readable, writable, exceptional = select.select(inputs, [], inputs)
		
		# Handle inputs
		for s in readable:
		
			#UPD Socket
			if s is sock:

				data, address = sock.recvfrom(4096)

				print >>sys.stderr, 'received %s bytes from %s' % (len(data), address)

				if data:
					try:
						command = json.loads(data)

						if command['Operation'] == "GET":
						
							dbg("GET command received")
							
							#Get settings and encode to JSON
							json_str = json.dumps(get_status())
							
							sent = sock.sendto(json_str, address)	

							#dbg('sent %s bytes back to %s' % (sent, address))
							dbg("")						

						if command['Operation'] == "SET":
								
							dbg("SET command received")
							#print "Command: " + command
							operate(command)
							
							dbg("")                                             

					except:
							dbg('Error receiving UPD JSON data')
							log_event("An Exception Occured")			
		
