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

s = socket.socket()
s.bind((wlan.ifconfig()[0], 4200))
s.listen(1)

while True:
    conn, addr = s.accept()
    msg = conn.recv(1024).decode()
    if not msg:
        break
    if msg == "on":
        relay.value(1)
    elif msg == "off":
        relay.value(0)
    conn.close()
