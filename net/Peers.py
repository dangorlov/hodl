import json
import time
import traceback
from socket import socket
import random
import cryptogr as cg
import logging as log
from .proto import recv, send

meta = """HODL_NetP v1"""


def ats(addr):
    return addr[0] + ':' + str(addr[1])


def afs(addr):
    return addr.split(':')[0], int(addr.split(':')[1])


class Peer:
    """
    Class for one peer.
    """

    def __init__(self, addr, netaddrs):
        """
        :param addr: Peer's HODL wallet
        :param netaddrs: Peer's IPs (dict: {IP1: whiteness of IP1, IP2: whiteness of IP2})
        """
        self.addr = addr
        self.netaddrs = [ats(addr) for addr in netaddrs]

    def connect(self, peers):
        """Generate sockets to all IP addresses for this peer"""
        log.debug('Peer.connect: Connecting to peer. self.netaddrs: ' + str(self.netaddrs) + '\n self.addr' + str(
                self.addr))
        sockets = []
        for addr in self.netaddrs:
            log.debug(str(time.time()) + ':Peer.connect: connecting to ' + str(addr))
            try:
                sock = socket()
                sock.connect(afs(addr))
                sockets.append(sock)
                log.debug('Peer.connect: new socket to white address ' + str(addr) + ': ' + str(sock))
            except Exception as e:
                log.debug('Peer.connect: exception while connecting: ' + traceback.format_exc())
        sockets += peers.white_conn_to(self.addr)
        return sockets

    def connect_white(self):
        sockets = []
        for addr in self.netaddrs:
            try:
                sock = socket()
                sock.settimeout(2)
                sock.connect(afs(addr))
                sockets.append(sock)
            except:
                pass
        return sockets

    def __str__(self):
        return json.dumps([self.addr, self.netaddrs])

    @classmethod
    def from_json(cls, s):
        """
        Restore peer from json string generated by str(peer)
        :type s: str
        :return: Peer
        """
        s = json.loads(s)
        self = cls(s[0], s[1])
        return self


class Peers(set):
    """
    Class for storing peers.
    It is a set of peers(class Peer)
    """

    def save(self, file):
        """
        Save peers to file
        :type file: str
        :return:
        """
        with open(file, 'w') as f:
            f.write(str(self))

    def __str(self):
        return json.dumps([json.dumps(peer) for peer in list(self)])

    @classmethod
    def from_json(cls, s):
        self = cls()
        for peer in json.loads(s):
            self.add(Peer.from_json(peer))
        return self

    @classmethod
    def open(cls, file):
        """
        Restore peers from file
        :type file: str
        :return:
        """
        with open(file, 'r') as f:
            self = cls.from_json(f.read())
        return self

    def srchbyaddr(self, addr):
        """
        Search peer in self.
        addr is peer's public key.
        :type addr: str
        :return:
        """
        for p in self:
            if p.addr == addr:
                return True, p
        return False, None

    def white_conn_to(self, to):
        for peer in self:
            socks = peer.connect_white()
            if socks:
                send(socks[0], json.dumps([meta, to]))
                return socks[0]
