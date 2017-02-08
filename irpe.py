#!/usr/bin/env python

"""
IR Photon Emitter Service
UPD server to operate IR light
"""

import sys
import socket
import select
import json
import threading
import logging
from time import sleep
import RPi.GPIO as GPIO

HOMEPATH = '/var/scripts/ir-photon-emitter/'

sys.path.insert(0, HOMEPATH)
import irpe_config

CONFIG = irpe_config.IRPE_Config()

logging.basicConfig(filename=HOMEPATH + CONFIG.logfile, level=logging.DEBUG)

logging.debug('ir-photon-emitter service starting')

#Pin Definitons
PIN1 = 17
PIN2 = 18

GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
GPIO.setup(PIN1, GPIO.OUT)
GPIO.setup(PIN2, GPIO.OUT)

GPIO.output(PIN1, GPIO.LOW)
GPIO.output(PIN2, GPIO.LOW)

#Globals / variables
STATE = 'Off'
MAXTIME = 900 #seconds
TIMERTHREADNAME = 'IRTIMER'
IRTIMER = None


def start_timer():
    """
    Start timer thread to turn off ir light after MAXTIME
    args: None
    returns : None
    """

    global IRTIMER

    IRTIMER = threading.Timer(MAXTIME, turn_off)
    IRTIMER.setName(TIMERTHREADNAME)
    IRTIMER.start()


def check_timer():

    """
    Check if Timer thread is running
    args: None
    returns: Boolean
    """

    for tds in threading.enumerate():

        if tds.getName() == TIMERTHREADNAME:
            return True

    return False


def set_timer():

    """Start timer if not running, otherwise reset"""

    global IRTIMER

    if check_timer():
        IRTIMER.cancel()
        start_timer()
    else:
        start_timer()


def turn_on():

    """turn on IR light at full power"""

    global STATE

    STATE = 'High'

    GPIO.output(PIN1, GPIO.HIGH)
    GPIO.output(PIN2, GPIO.HIGH)

    set_timer()

    logging.debug('turn_on')


def turn_on_half_1():

    """Turn on IR light at half power"""

    global STATE

    STATE = 'Low'

    GPIO.output(PIN1, GPIO.HIGH)
    GPIO.output(PIN2, GPIO.LOW)

    set_timer()

    logging.debug('turn_on_half_1')


def turn_on_half_2():

    """Turn on IR light at half power"""

    global STATE

    STATE = 'Low'

    GPIO.output(PIN1, GPIO.LOW)
    GPIO.output(PIN2, GPIO.HIGH)

    set_timer()

    logging.debug('turn_on_half_2')


def turn_off():

    """Turn off IR light"""

    global STATE, IRTIMER

    STATE = 'Off'

    GPIO.output(PIN1, GPIO.LOW)
    GPIO.output(PIN2, GPIO.LOW)

    IRTIMER.cancel()

    logging.debug('turn_off')


def operate(cmd):

    """Parse operations received via JSON over UDP"""

    if cmd['Power'] == 'Off':
        turn_off()

    elif cmd['Power'] == 'Low':
        turn_on_half_1()

    elif cmd['Power'] == 'Off':
        turn_on()


def get_state():

    """return current start of IR light"""
    return {'Power': STATE}


def setup_socket(s_ip, s_port):

    """Create UDP socket to communicate on the network"""

    sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sck.setblocking(0)
    server_address = (s_ip, s_port)

    # Bind the socket to the port
    while True:
        try:
            sck.bind(server_address)
            break
        except:
            logging.exception("Exception Occured:")
            sleep(5)

    return sck



#Main Loop to send/receive UDP packets

if __name__ == "__main__":

    sock = setup_socket(CONFIG.server_ip, CONFIG.server_port)

    #Inputs to monitor
    inputs = [sock]

    try:

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

                                #Get settings and encode to JSON
                                json_str = json.dumps(get_state())

                                sent = sock.sendto(json_str, address)

                            if command['Operation'] == "SET":

                                operate(command)


                        except:
                            logging.exception("Exception Occured:")
                            print "Error"

    except:
        logging.exception("Exception Occured:")

    finally:
        GPIO.cleanup()
        sock.close()
        logging.debug('ir-photon-emitter service shut down')
