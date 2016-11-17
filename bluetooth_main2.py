import time
import os

# Wait until bluetooth module is powered on after reboot
print 'Wait 10 seconds for bluetooth devices to power on'
time.sleep(10)

bluetooth_addresses = {'Chris': '9C:F4:8E:26:F0:22', 'Gerd': 'B8:53:AC:61:73:AA', 'Regina': '98:FE:94:37:67:86'}

device_number = 0
for device_name, device_addr in bluetooth_addresses.iteritems():
    os.system("sudo su -l pi -c 'screen -d -m -S \"Observer " + device_name + " \" /home/pi/Bluetooth_Door_Opener/bluetooth2 " + device_addr + " \"" + device_name + "\" " + str(device_number) + " &'")
    print "Scan started for " + device_name
    device_number += 1
