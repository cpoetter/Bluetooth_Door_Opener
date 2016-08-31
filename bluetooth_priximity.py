#! /usr/bin/env python

import threading
import fcntl
import struct
import array
import bluetooth
import bluetooth._bluetooth as bt
import time
import os
import datetime


class bluetooth_scan(threading.Thread):
    def __init__(self, name, addr, threshold = 3):
        threading.Thread.__init__(self)
        self.addr = addr
        self.name = name
        self.threshold = threshold
        self.status = 'closed'     

    def bluetooth_rssi(self):
        # Open hci socket
        hci_sock = bt.hci_open_dev()
        hci_fd = hci_sock.fileno()

        # Connect to device (to whatever you like)
        bt_sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
        bt_sock.settimeout(10)
        result = bt_sock.connect_ex((self.addr, 1))      # PSM 1 - Service Discovery

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

    def run(self):
        print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ': Scan for ' + self.name + ' started'  
        while True:
            rssi = self.bluetooth_rssi()

            if rssi >= self.threshold:
                if self.status != 'open':
                    print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ': ' + self.name  +' is home, open door'
                    self.status = 'open'
                    time.sleep(3)
            else:
                if self.status != 'closed':
                    print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ': ' + self.name + ' left, close door'
                    self.status = 'closed'
            time.sleep(2)


bluetooth_addresses = {'Chris iPhone': '5C:AD:CF:20:86:59', 'Huas Android': '50:32:75:FC:B8:36'}

threads_running = []
for device_name, device_addr in bluetooth_addresses.iteritems():
    threads_running.append(bluetooth_scan(device_name, device_addr))
    threads_running[-1].daemon = True

for thr in threads_running:
    thr.start()

while True:
    time.sleep(1)
