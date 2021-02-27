#!/usr/bin/env python3

import struct

TFTP_OPCODES = {
    'unknown': 0,
    'read': 1,
    'write': 2,
    'data': 3,
    'ack': 4,
    'error': 5,
    'oack': 6}


class TFTPPacket():
    def __init__(self, data):
        self.tt = int.from_bytes(data[:2], "big")
        if self.tt == 1 or self.tt == 2:
            blocks = data[2:].split(b'\0')
            self.blksize = None
            self.windowsize = None
            self.filename = blocks[0].decode('utf-8')
            for i in range(2, len(blocks), 2):
                if blocks[i] == b'blksize' and int(blocks[i + 1]) != 512:
                    self.blksize = int(blocks[i + 1])
                if blocks[i] == b'windowsize' and int(blocks[i + 1]) != 1:
                    self.windowsize = int(blocks[i + 1])
        if self.tt == 3:
            self.num = int.from_bytes(data[2:4], "big")
            self.data = data[4:]
        if self.tt == 4:
            self.num = int.from_bytes(data[2:4], "big")
        if self.tt == 6:
            blocks = data[2:].split(b'\0')
            self.blksize = 512
            self.windowsize = 1
            for i in range(0, len(blocks), 2):
                if blocks[i] == b'blksize':
                    self.blksize = int(blocks[i + 1])
                if blocks[i] == b'windowsize':
                    self.windowsize = int(blocks[i + 1])
            print(self.blksize)


def rrqpacket(filename, mode, blksize=512, windowsize=1):
    request = struct.pack('>h', 1)
    request += bytes(filename, 'utf-8')
    request += b'\00'
    request += bytes(mode, 'utf-8')
    request += b'\00'

    if blksize != 512:
        request += b'blksize'
        request += b'\00'
        request += bytes(str(blksize), "utf-8")
        request += b'\00'

    if windowsize != 1:
        request += b'windowsize'
        request += b'\00'
        request += bytes(str(windowsize), "utf-8")
        request += b'\00'
    return request

def ackpacket(block_number):
    request = struct.pack('>hh', 4, block_number)
    return request

def oackpacket(blksize, windowsize):
    request = struct.pack('>h', 6)
    if blksize is not None:
        request += b'blksize'
        request += b'\00'
        request += bytes(str(blksize), "utf-8")
        request += b'\00'

    if windowsize is not None:
        request += b'windowsize'
        request += b'\00'
        request += bytes(str(windowsize), "utf-8")
        request += b'\00'
    return request

def datapacket(num, data):
    packet = struct.pack('>hh', 3, num)
    packet += data
    return packet



