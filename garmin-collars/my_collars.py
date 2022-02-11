import copy
import sys
import signal
import struct
import time
import array
import math
import usb1
import threading
import urllib.request

class CollarsThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.usb_device = None
        self.handle = None
        self.should_run = True
        self.connected = False
        self.start_counter = 0
        self.state = {
            "collars": {},
            "connected": False,
        }

    def status(self):
        s = copy.deepcopy(self.state)
        s["connected"] = self.connected
        return s

    def run(self):
        with usb1.USBContext() as context:
            while self.should_run:
                try:
                    print("Looking for device...")
                    self.handle = getDeviceHandle(context, 0x091e, 0x0003, self.usb_device)
                    if self.handle is None:
                        print("No device")
                        time.sleep(1)
                        continue

                    self.handle.claimInterface(0)
                
                    startSession(self.handle)
                    self.run2()
                except usb1.USBErrorIO:
                    print("USB Error")
                self.connected = False
                time.sleep(1)

            self.handle.releaseInterface(0)
            


    def run2(self):
        while self.should_run:
            try:
                pkt = readBulk(self.handle, 1000)
                #print("{:3d} {}".format(len(pkt), ' '.join(format(x, '02x') for x in pkt)))
                if struct.unpack("<H", pkt[0:2])[0] == 20 and struct.unpack("<H", pkt[4:6])[0] == 3078:
                    self.processBaseStationPacket(pkt[12:]) 
                elif struct.unpack("<H", pkt[0:2])[0] == 20 and struct.unpack("<H", pkt[4:6])[0] == 0xFD:
                    self.connected = True
                    print("Connected")

            except usb1.USBErrorTimeout:
                # print(".")
                print("", end='')
                self.start_counter += 1
                if self.start_counter > 3 and self.connected == False:
                    print("retrying ...")
                    self.start_counter = 0
                    startSession(self.handle)

    def shutdown(self):
        print("USB shutdown requested...")
        self.should_run = False

    def processBaseStationPacket(self, pkt):
        lat = struct.unpack("<i", pkt[0:4])[0] * (180.0 / 2147483647)
        lng = struct.unpack("<i", pkt[4:8])[0] * (180.0 / 2147483647)
        alt = struct.unpack("<f", pkt[8:12])[0]
        gps_time = struct.unpack("<i", pkt[12:16])[0] # seconds since 12/31/89 UTC
        asset_into = struct.unpack("<i", pkt[16:20])[0]
        batt = struct.unpack("<B", pkt[25:26])[0]
        gps = struct.unpack("<B", pkt[26:27])[0]
        comm = struct.unpack("<B", pkt[27:28])[0]
        ident = pkt[31:pkt.find(0,31)].decode("utf-8")
        print("  {:8s} {:2.5f},{:3.5f} batt:{} gps:{} comm:{} {:4.1f}m".format(ident, lat, lng, batt, gps, comm, alt))
        msg = "batt:{} gps:{} comm:{}".format(batt, gps, comm)

        self.state["collars"][ident] = {
            "lat": lat,
            "lng": lng,
            "alt": alt,
            "gps": gps,
            "comm": comm,
            "batt": batt,
            "updated": time.time() * 1000
        }

        SubmitThread("http://localhost:8080/rest/location/update/position?id=COLLAR-{}&lat={}&lng={}&alt={}&msg={}".format(urllib.parse.quote_plus(ident), lat, lng, alt, urllib.parse.quote_plus(msg))).start()

class SubmitThread (threading.Thread):
    def __init__(self, url):
        threading.Thread.__init__(self)
        self.url = url

    def run(self):
        f = urllib.request.urlopen(self.url)
        print(f.read().decode('utf-8'))


def getDeviceHandle(context, vendor_id, device_id, usb_device=None):
    if usb_device is None:
        return context.openByVendorIDAndProductID(vendor_id, device_id)
    bus_number, device_address = usb_device
    for device in context.getDeviceList():
        if (bus_number != device.getBusNumber() \
                or device_address != device.getDeviceAddress()):
            continue
        if (device.getVendorID() == vendor_id and
            device.getProductID() == device_id):
            return device.open()
        raise ValueError(
            'Device at %03i.%03i is not of expected type' % usb_device + (vendor_id, device_id),
        )

def readBulk(handle, timeout):
    while True:
        pkt = handle.interruptRead(0x82, 60, timeout)
        if pkt[4] == 2:
            break

    pkt = []
    while len(pkt) < 12:
        pkt.extend(handle.bulkRead(0x83, 6000, timeout))

    data_len = struct.unpack("<I", bytes(pkt[8:12]))[0]
    while len(pkt) < 12 + data_len:
        pkt.extend(handle.bulkRead(0x83, 6000, timeout))

    pkt = bytes(pkt)
    return pkt

def startSession(handle):
    handle.bulkWrite(1, [0,0,0,0,5,0,0,0,0,0,0,0,0])
    while True:
        pkt = handle.interruptRead(0x82, 60, 5000)
        if pkt[4] == 6:
            deviceId = struct.unpack("<I", pkt[12:])[0]
            print("Found Device ID {}".format(deviceId))
            break

    handle.bulkWrite(1, [20,0,0,0,254,0,0,0,0,0,0,0])
    pkt = readBulk(handle, 15000)

    product_id = struct.unpack("<H", pkt[12:14])[0]
    software_ver = struct.unpack("<h", pkt[14:16])[0] / 100
    product_desc = pkt[16:pkt.find(0, 16)].decode("utf-8")
    print("{}".format(product_desc))
