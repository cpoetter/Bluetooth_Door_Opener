import time
import os

#### To add new devices ####
# Just do this once
# sudo bluetoothctl
# pair MAC_ADDRESS
#### ####

#### To install bluetooth in Raspberry Pi 3 ####
# sudo apt-get install python-bluez
#### ####

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

# Wait until bluetooth module is powered on after reboot
print 'Wait 10 seconds for bluetooth devices to power on'
time.sleep(10)
            
bluetooth_addresses = {'Chris': ['9C:F4:8E:26:F0:22', -1, -22], 'Gerd': ['B8:53:AC:61:73:AA', -1, -22], 'Regina': ['98:FE:94:37:67:86', -1, -22]}

device_number = 0
for device_name, device_data in bluetooth_addresses.iteritems():
    device_addr = device_data[0]
    device_border_1 = device_data[1]
    device_border_2 = device_data[2]
    os.system("sudo su -l pi -c 'screen -d -m -S \"Observer " + device_name + " \" /home/pi/Bluetooth_Door_Opener/bluetooth " + device_addr + " \"" + device_name + "\" " + str(device_number) + " " + str(device_border_1) + " " + str(device_border_2) + " &'")
    print "Scan started for " + device_name
    device_number += 1
