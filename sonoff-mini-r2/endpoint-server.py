import webrepl
import network
import socket
from machine import Pin

# Connect to wifi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('jamnet', 'cjZY8PTa4ZQ6S83A')

# Start webrepl to allow connecting and uploading scripts over network
# Do not put code before this, if it hangs will not be able to connect
webrepl.start()

print("\nCompleted startup\n")

relay = Pin(12, Pin.OUT)

on = socket.socket()
on.bind((wlan.ifconfig()[0], 6969))
on.listen(1)

off = socket.socket()
off.bind((wlan.ifconfig()[0], 9696))
off.listen(1)

while True:
    clientsocket, address = on.accept()
    if address:
        print("Turning ON")
        relay.value(1)
    clientsocket, address = off.accept()
    if address:
        print("Turning OFF")
        relay.value(0)
    gc.collect()
