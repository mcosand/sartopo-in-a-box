# Monitor Garmin Alpha/Astro tracking collars

## Disable the garmin_gps kernel module
See files/etc/modprobe.d/blacklist-garmin.conf

## Install Python3 modules
```sh
sudo pip3 install libusb1
```
See https://github.com/vpelletier/python-libusb1

## Start the tracking script
```
sudo python3 trackers.py
```
Will try to forward position updates to CalTopo Desktop at http://localhost:8080. Will use `FLEET:COLLAR-{collar name}` as the device id.

The script starts a web server on port 80. Currently only has a `/api/state` endpoint to report the state of the collars heard by the script.