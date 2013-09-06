# -*- coding: utf-8 -*-

import ssl
import socket
import errno

__title__ = "pynsd"
__version__ = "0.0.1"
__author__ = "novutec Inc."
__license__ = "Apache2"


class ControlClient(object):
    """Client class to connect to nsd control port and send calls"""

    NSD_CONTROL_VERSION = 1
    BUFSIZE = 8192

    def __init__(self, clientCert, clientKey, host='127.0.0.1',
                 port=8952, bufsize=None, strip=False):
        self.clientCert = clientCert
        self.clientKey = clientKey
        self._bufsize = bufsize or self.__class__.BUFSIZE
        self.host = host
        self.port = port
        self.sock = None
        self.strip = strip

    def __del__(self):
        self.close()

    def setClientCert(self, clientCert, clientKey):
        self.clientCert = clientCert
        self.clientKey = clientKey

    def close(self):
        if self.sock is not None:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
            self.sock = None

    def connect(self, host, port=8952):
        if self.sock is not None:
            raise Exception('Socket already defined.')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock = ssl.wrap_socket(s,
                                    certfile=self.clientCert,
                                    keyfile=self.clientKey)
        self.sock.connect((host, port))

    def __getattr__(self, name):
        def fn(*args):
            return self.call(name, args)
        return fn

    def call(self, cmd, args=()):
        if self.sock is None:
            self.connect(self.host, self.port)
        # send header
        self.sock.sendall("NSDCT%d " % (self.NSD_CONTROL_VERSION))
        # send command name
        self.sock.sendall(' ' + cmd)
        # send command parameters
        for arg in args:
            self.sock.sendall(' ' + arg)
        # send break line to commit command as completed
        self.sock.sendall("\n")
        # fetch response
        return self.fetch()

    def fetch(self):
        buf = ''
        buf_len = 0

        while True:
            try:
                part = self.sock.read(self._bufsize - buf_len)
            except socket.sslerror, err:
                if (err[0] == socket.SSL_ERROR_WANT_READ or
                    err[0] == socket.SSL_ERROR_WANT_WRITE):
                    continue
                if (err[0] == socket.SSL_ERROR_ZERO_RETURN or
                    err[0] == socket.SSL_ERROR_EOF):
                    break
                raise
            except socket.error, err:
                if err[0] == errno.EINTR:
                    continue
                if err[0] == errno.EBADF:
                    # XXX socket was closed?
                    break
                raise
            if len(part) == 0:
                break
            buf += part
            buf_len += len(part)

        self.close()
        if self.strip:
            return buf.strip()
        return buf
