#!/usr/bin/env python3

import socket
import argparse
import select
from tftp import *

HOST = ''
PORT = 6969
parser = argparse.ArgumentParser()
parser.add_argument('--host', default=HOST)
parser.add_argument('--port', type=int, default=PORT)
args = parser.parse_args()

TFTP_OPCODES = {
    'unknown': 0,
    'read': 1,
    'write': 2,
    'data': 3,
    'ack': 4,
    'error': 5,
    'oack': 6}


class Client:
    def __init__(self, client_sock, client_addr, data):
        self.sock = client_sock
        self.addr = client_addr
        packet = TFTPPacket(data)
        self.blksize = 512 if packet.blksize is None else packet.blksize
        self.windowsize = 1 if packet.windowsize is None else packet.windowsize
        if packet.blksize is not None or packet.windowsize is not None:
            self.sock.sendto(oackpacket(packet.blksize, packet.windowsize), client_addr)


        self.file = open(packet.filename, "rb")
        self.blocks = dict()
        self.lastblock = -1
        if packet.blksize is None and packet.windowsize is None:
            for i in range(1, 1 + self.windowsize):
                if self.blocks.get(i) is None:
                    self.blocks[i] = self.file.read(self.blksize)
                data = self.blocks[i]
                self.sock.sendto(datapacket(i, data), client_addr)
                if len(data) < self.blksize:
                    self.lastblock = i
                    break

    def handle_message(self, data, client_addr):
        packet = TFTPPacket(data)
        if packet.tt == 0 or packet.tt == 1 or packet.tt == 2 or packet.tt == 3 or packet.tt == 5 or packet.tt == 6:
            return False
        if packet.tt == 4:
            last = packet.num
            if self.lastblock != -1 and last == self.lastblock:
                return True
            for i in range(last, 0, -1):
                if self.blocks.get(i) is not None:
                    self.blocks.pop(i)
                else:
                    break
            for i in range(last + 1, last + 1 + self.windowsize):
                if self.blocks.get(i) is None:
                    self.blocks[i] = self.file.read(self.blksize)
                data = self.blocks[i]
                self.sock.sendto(datapacket(i, data), client_addr)
                if len(data) < self.blksize:
                    self.lastblock = i
                    break
        return False

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_sock:
    server_sock.bind((args.host, args.port))
    epoll = select.epoll()
    epoll.register(server_sock.fileno(), select.EPOLLIN)
    clients = dict()
    while True:
        for fileno, event in epoll.poll(timeout=1):
            if fileno == server_sock.fileno() and event & select.EPOLLIN:
                data, client_addr = server_sock.recvfrom(1024)
                if TFTPPacket(data).tt != 1:
                    continue
                print('Add client', client_addr)
                client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                clients[client_sock.fileno()] = Client(client_sock, client_addr, data)
                epoll.register(client_sock.fileno(), select.EPOLLIN)
            elif fileno in clients and event & select.EPOLLIN:
                client = clients[fileno]
                data, client_addr = client.sock.recvfrom(1024)
                if client_addr != client.addr:
                    continue
                if client.handle_message(data, client_addr):
                    clients.pop(client.sock.fileno())
                    epoll.unregister(client.sock.fileno())
                    client.sock.close()
                    print('Remove client', client.addr)

