import webrepl
import network
import json
import socket
import os
from machine import Pin

# Load config file from disk
with open('config.json', 'r') as file:
    config = json.load(file)

# Connect to wifi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(config["wifi"]["ssid"], config["wifi"]["password"])

# Start webrepl to allow connecting and uploading scripts over network
# Do not put code before this, if it hangs will not be able to connect
webrepl.start()

relay = Pin(12, Pin.OUT)
switch = Pin(4, Pin.IN)

# Get filesize/modification time (to detect upload in future)
old = os.stat("boot.py")

print("\nCompleted startup\n")

# Interrupt function - lets lightswitch override relay state
def switch_interrupt(pin):
    if switch.value():
        relay.value(0)
    elif not switch.value():
        relay.value(1)

# Call interrupt function when switch changes in either direction
switch.irq(trigger=Pin.IRQ_RISING, handler=switch_interrupt)
switch.irq(trigger=Pin.IRQ_FALLING, handler=switch_interrupt)

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
        if switch.value(): # Only allow turning off if switch is off (switch = manual override)
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
