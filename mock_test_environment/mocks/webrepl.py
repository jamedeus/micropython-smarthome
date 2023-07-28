import socket

listen_s = None


def start():
    global listen_s
    listen_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
