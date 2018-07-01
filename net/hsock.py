from socket import socket
from threading import Thread
import time
import traceback
from net.Peers import Peers
import logging as log
from .proto import recv, send, sock_to
from .protocol import generate, handle

hsocks = []


class HSock:
    """
    HODL Socket:11
    Helps to connect any device connected to HODL network (including devices behind NAT)
    """

    def __init__(self, sock=None, conn=None, addr='', myaddrs=tuple(), peers=Peers(), n=3):
        if not (sock and conn):
            self.peer = peers.srchbyaddr(addr)[1]
            self.socks = self.peer.connect(peers, n=n)
            self.conns = []
            log.debug('HSock.__init__ by address: self.socks, self.conns created. self.socks:'
                      + str([str(sock) for sock in self.socks]))
        else:
            self.socks = [sock]
            self.conns = [conn]
        self.peers = peers
        self.in_msgs = []
        self.myaddrs = myaddrs
        self.listen()
        self.addr = addr
        self.amh = []
        if not (sock and conn):
            time.sleep(0.3)
            self.send(generate('', peers, [], myaddrs, [], 'text', True, self.addr))

    @classmethod
    def input(cls, sock, conn, myaddrs=tuple()):
        # todo: get sender's address
        return cls(sock=sock, conn=conn, myaddrs=myaddrs)

    def send(self, data='', requests=tuple(), ans=tuple(), full=False, peers='from_HSock'):
        """

        Send data with all sockets in this HSock
        :param data: str
        :param peers: Peers
        :param full: bool
        """
        if peers == 'from_HSock':
            try:
                peers = self.peers
            except AttributeError:
                peers = Peers()
        # todo: encode data using RSA
        # todo: generate message by protocol.generate
        log.debug('send')
        for sock in self.socks:
            if sock:
                send(sock, generate(message=data, peers=peers, ans=ans, pubkeys=[addr[1] for addr in self.myaddrs],
                                    requests=requests, encoding="text", full=full, endaddr=self.addr))

    def listen(self):
        """
        Listen for new messages and write it to self.in_msgs
        :return:
        """
        # todo: decode msg using RSA
        if self.conns:
            for conn in self.conns:
                if conn:
                    Thread(target=self.recv_by_sock, args=(conn,), name="recv_by_sock " + str(conn)
                                                                        + str(hash(self))).start()
        else:
            for sock in self.socks:
                if sock:
                    Thread(target=self.recv_by_sock, args=(sock,)).start()

    def close(self):
        """
        Close socket.
        :return:
        """
        for conn in self.conns:
            conn.close()

    def recv_by_sock(self, sock):
        while True:
            try:
                recvmess = recv(sock)
                if recvmess == None:
                    time.sleep(0.05)
                    continue
                self.in_msgs.append(recvmess)
                hand = handle(self.in_msgs[-1], self.addr, self.peers, alternative_message_handlers=self.amh,
                              first=len(self.in_msgs) == 0)
                if hand[0]:
                    self.send(*(hand[1] + [self.peers]))
            except Exception as e:
                if str(e) != 'timed out':
                    log.debug(str(time.time()) + ':HSock.recv_by_sock:exception: ' + traceback.format_exc())

    def listen_msg(self, delt=0.05):
        """
        Listen for one msg
        :param delt: float
        :return: msg: str
        """
        len_msgs = len(self.in_msgs)
        while True:
            time.sleep(delt)
            if len(self.in_msgs) > len_msgs:
                return self.in_msgs[-1]

    def extend(self, peer, peers=Peers()):
        """
        If new IPs for this peer are received, make connections with this IPs
        :param peer: Peer
        :param peers: Peers
        """
        current_ips = set(self.peer.netaddrs)
        peer.connect(peers, current_ips)

    def __hash__(self):
        return hash(','.join([str(hash(self.__dict__.get('peer', 'none')))] + [str(conn) for conn in self.conns]
                             + [str(sock) for sock in self.socks]))

    def __repr__(self):
        return '<HSock socks=' + str(self.socks) + ' peer=' + repr(
            self.__dict__.get('peer')) + '>'


def listen(port=9276):
    """
    Listen for one connection
    :return: sock: HSock
    """
    global sock
    if not 'sock' in globals():
        sock = socket()
        sock.bind(('', port))
        sock.listen()
    conn, addr = sock.accept()
    hsock = HSock.input(sock, conn)
    hsocks.append(hsock)
    return hsock


def connect_to(addr, myaddrs=tuple(), peers=Peers()):
    """
    Create new HSock by address if not exists
    :param addr: str, HODL wallet to connect to
    :param myaddrs: list, my addresses
    :param peers: Peers
    :return: HSock
    """
    for hsock in hsocks:
        if hsock.addr == addr:
            return hsock
    else:
        hsock = HSock(addr=addr, myaddrs=myaddrs, peers=peers)
        hsocks.append(hsock)
        return hsock


def listen_loop(port=9276):
    while True:
        listen(port)


def listen_thread(port=9276):
    """
    Start new thread for listening
    :param port: int
    """
    Thread(target=listen_loop, args=(port,)).start()


def connect_to_all(peers, myaddrs=tuple()):
    connected = [hsock.peer.addr if 'peer' in hsock.__dict__.keys() else None for hsock in hsocks]
    for peer in list(peers):
        if peer.addr in connected:
            hsock = hsocks[connected.index(peer.addr)]
            hsock.extend(peer, peers)
        else:
            hsocks.append(HSock(addr=peer.addr, myaddrs=myaddrs, peers=peers))
