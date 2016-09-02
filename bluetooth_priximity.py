#! /usr/bin/env python

#### To use external USB bluetooth dongle #####
# run once to deactivate internal bluetooth
# sudo systemctl disable hciuart
# stays even after reboot
# in /boot/config.txt add
# dtoverlay=pi3-disable-bt

# run once to activate internal bluetooth
# sudo systemctl enable hciuart
# remove in /boot/config.txt
# dtoverlay=pi3-disable-bt
##### #####

import threading
import fcntl
import struct
import array
import bluetooth
import bluetooth._bluetooth as bt
import time
import os
import datetime
import RPi.GPIO as GPIO
import httplib, urllib
import json


class bluetooth_scan(threading.Thread):
    def __init__(self, name, addr, threshold = 2):
        threading.Thread.__init__(self)
        self.addr = addr
        self.name = name
        self.threshold = threshold
        self.status = 'undefined'
        
        # Fastest possible time seems to be 2 sec
        self.sleep_time = 2
        
    def bluetooth_rssi(self):
        # Thanks to https://github.com/dagar/bluetooth-proximity
        
        # Open hci socket
        hci_sock = bt.hci_open_dev()
        hci_fd = hci_sock.fileno()

        # Connect to device (to whatever you like)
        bt_sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
        bt_sock.settimeout(10)
        result = bt_sock.connect_ex((self.addr, 1))      # PSM 1 - Service Discovery
        
        if result != 0:
            # Timeout or other error during connection
            return None
        
        try:
            # Get ConnInfo
            reqstr = struct.pack("6sB17s", bt.str2ba(self.addr), bt.ACL_LINK, "\0" * 17)
            request = array.array("c", reqstr )
            handle = fcntl.ioctl(hci_fd, bt.HCIGETCONNINFO, request, 1)
            handle = struct.unpack("8xH14x", request.tostring())[0]

            # Get RSSI
            cmd_pkt=struct.pack('H', handle)
            rssi = bt.hci_send_req(hci_sock, bt.OGF_STATUS_PARAM, bt.OCF_READ_RSSI, bt.EVT_CMD_COMPLETE, 4, cmd_pkt)
            rssi = struct.unpack('b', rssi[3])[0]

            # Close sockets
            bt_sock.close()
            hci_sock.close()

            return rssi

        except:
            return None

        
    def open_door(self):
        global door_status
        
        if door_status != 'open':
            # Open door
            print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ': Open door'
            door_status = 'open'
            GPIO.output(12, GPIO.HIGH)
            os.system("sudo su -l root -c 'echo '1' >/sys/class/leds/led0/brightness'")

            # Time to pass through door
            time.sleep(5)

            # Close door
            print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ': Close door'
            door_status = 'closed'
            GPIO.output(12, GPIO.LOW)
            os.system("sudo su -l root -c 'echo '0' >/sys/class/leds/led0/brightness'")

            # Time to leave door area
            time.sleep(5)
        else:
            print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ': Door already open'
        
        
    def run(self):
        print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ': Scan for ' + self.name + ' started'  
        while True:
            rssi = self.bluetooth_rssi()

            if rssi >= self.threshold:
                if self.status != 'home':
                    print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ': ' + self.name  +' is home'
                    self.status = 'home'
                    self.sleep_time = 2
                self.open_door()
            elif rssi is None:
                if self.status != 'away':
                    print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ': ' + self.name + ' is away'
                    self.status = 'away'
                    self.sleep_time = 2
            else:
                if self.status != 'not_close_enough':
                    print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ': ' + self.name + ' is not close enough'
                    self.status = 'not_close_enough'
                    self.sleep_time = 2
                    
            # If person is not in reach, interval between checks can be extended
            time.sleep(self.sleep_time)


            
bluetooth_addresses = {'Chris iPhone': '5C:AD:CF:20:86:59', 'Huas Android': '50:32:75:FC:B8:36'}

threads_running = []
for device_name, device_addr in bluetooth_addresses.iteritems():
    threads_running.append(bluetooth_scan(device_name, device_addr))
    threads_running[-1].daemon = True

for thr in threads_running:
    thr.start()

# to use Raspberry Pi board pin numbers
GPIO.setmode(GPIO.BOARD)

# set up the GPIO channels, 14 is Ground
# number 6 and 7 on the right side
GPIO.setup(12, GPIO.OUT)
GPIO.setup(11, GPIO.IN)

# set start value
GPIO.output(12, GPIO.LOW)
os.system("sudo su -l root -c 'echo none >/sys/class/leds/led0/trigger'")
os.system("sudo su -l root -c 'echo '0' >/sys/class/leds/led0/brightness'")

# Global door status variable
door_status = 'closed'

# While loop to be able to close python script with Control+C
while True:
    try:
        
        if GPIO.input(11):
            print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ': Doorbell ring'
            conn = httplib.HTTPSConnection("api.pushover.net:443")
            conn.request("POST", "/1/messages.json",
                         urllib.urlencode({"token": "a72ixa4uudncku5wygvnc9vio4342n", "user": "unpgpsea1vvxnk2522otkng3ffoef5", "priority": 0, "sound": "bike", "timestamp": int(time.time()), "title": "Open Door!", "message": "Doorbell ringed.",}), { "Content-type": "application/x-www-form-urlencoded" })
            # "priority": 2, "retry": 60, "expire": 120,
            push_response = conn.getresponse()
            response = json.load(push_response)
            if response['status'] == 1:
                print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ': Push successfully send'
                # On acknowledgment open the door
            else:
                print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ': Could not send Push notification'
            # Do not ring too often
            time.sleep(2)
        
        time.sleep(0.5)
    except KeyboardInterrupt:
        GPIO.cleanup()
        exit()
        
