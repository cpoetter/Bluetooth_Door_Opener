#! /usr/bin/env python

import fcntl
import struct
import array
import bluetooth
import bluetooth._bluetooth as bt

import time
import os
import datetime

def bluetooth_rssi(addr):
    # Open hci socket
    hci_sock = bt.hci_open_dev()
    hci_fd = hci_sock.fileno()

    # Connect to device (to whatever you like)
    bt_sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
    bt_sock.settimeout(10)
    result = bt_sock.connect_ex((addr, 1))      # PSM 1 - Service Discovery

    try:
        # Get ConnInfo
        reqstr = struct.pack("6sB17s", bt.str2ba(addr), bt.ACL_LINK, "\0" * 17)
        request = array.array("c", reqstr )
        handle = fcntl.ioctl(hci_fd, bt.HCIGETCONNINFO, request, 1)
        handle = struct.unpack("8xH14x", request.tostring())[0]

        # Get RSSI
        cmd_pkt=struct.pack('H', handle)
        rssi = bt.hci_send_req(hci_sock, bt.OGF_STATUS_PARAM,
                     bt.OCF_READ_RSSI, bt.EVT_CMD_COMPLETE, 4, cmd_pkt)
        rssi = struct.unpack('b', rssi[3])[0]

        # Close sockets
        bt_sock.close()
        hci_sock.close()

        return rssi

    except:
        return None


bluetooth_addresses = ['5C:AD:CF:20:86:59', '50:32:75:FC:B8:36']

status = 'closed'

while True:

    for device_addr in bluetooth_addresses:
        rssi = bluetooth_rssi(device_addr)

        if rssi >= 3:
            if status != 'open':
                print datetime.datetime.now(), 'User is home, open door'
                status = 'open'
        else:
            if status != 'closed':
                print datetime.datetime.now(), 'User left, close door'
                status = 'closed'
    time.sleep(2)
