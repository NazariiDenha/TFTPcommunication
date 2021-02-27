#!/usr/bin/env python3

import socket
import argparse
from tftp import *

HOST = 'localhost'
PORT = 6969
parser = argparse.ArgumentParser()
parser.add_argument('--host', default=HOST)
parser.add_argument('--port', type=int, default=PORT)
parser.add_argument('--blksize', type=int, default=512)
parser.add_argument('--windowsize', type=int, default=1)
parser.add_argument('--filename')
args = parser.parse_args()

TFTP_OPCODES = {
    'unknown': 0,
    'read': 1,
    'write': 2,
    'data': 3,
    'ack': 4,
    'error': 5,
    'oack': 6}


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server = (args.host, args.port)

file = open(args.filename, 'wb')
sock.sendto(rrqpacket(args.filename, 'netascii', blksize=args.blksize, windowsize=args.windowsize), server)
blksize = 512
windowsize = 1
last_good = 0
last_window = 0
bad_ack_sent = False
while True:
    data, addr = sock.recvfrom(blksize + 4)
    packet = TFTPPacket(data)
    if packet.tt == 3:
        if packet.num != last_good + 1:
            if not bad_ack_sent:
                bad_ack_sent = True
                sock.sendto(ackpacket(last_good), addr)
            continue
        bad_ack_sent = False
        file.write(packet.data)
        last_good += 1
        if packet.num == last_window + windowsize or len(packet.data) < blksize:
            sock.sendto(ackpacket(packet.num), addr)
            last_window = packet.num
        if len(packet.data) < blksize:
            break
    if packet.tt == 6:
        blksize = packet.blksize
        windowsize = packet.windowsize
        sock.sendto(ackpacket(0), addr)
