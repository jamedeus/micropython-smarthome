import webrepl
import network
import socket
import os
from machine import Pin

# Connect to wifi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('jamnet', 'cjZY8PTa4ZQ6S83A')

# Start webrepl to allow connecting and uploading scripts over network
# Do not put code before this, if it hangs will not be able to connect
webrepl.start()

relay = Pin(12, Pin.OUT)

# Get filesize/modification time (to detect upload in future)
old = os.stat("boot.py")

print("\nCompleted startup\n")

# Create socket listening on port 4200
s = socket.socket()
s.bind((wlan.ifconfig()[0], 4200))
s.listen(1)

# Handle connections
while True:
    # Accept connection, decode message
    conn, addr = s.accept()
    msg = conn.recv(1024).decode()

    if msg == "on":
        relay.value(1)
    elif msg == "off":
        relay.value(0)

    # Close connection, restart loop and wait for next connection
    conn.close()

    # Check if boot.py changeed on disk (upload received through webrepl), reboot if it did
    if not os.stat("boot.py") == old:
        import machine
        machine.reset()



## Client-side code ##
#import socket

#def on():
    #s = socket.socket()
    #s.connect(('192.168.1.227', 4200))
    #s.send("on".encode())
    #s.close()

#def off():
    #s = socket.socket()
    #s.connect(('192.168.1.227', 4200))
    #s.send("off".encode())
    #s.close()
