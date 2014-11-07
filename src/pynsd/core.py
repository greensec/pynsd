# coding: utf-8
"""
Copyright (c) 2007 - 2013 Novutec Inc. (http://www.novutec.com)
Copyright (c) 2014 greenSec Solutions (http://www.greensec.de)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

@category Novutec
@package pynsd
@copyright Copyright (c) 2007 - 2013 Novutec Inc. (http://www.novutec.com)
@copyright Copyright (c) 2014 greenSec Solutions (http://www.greensec.de)
@license http://www.apache.org/licenses/LICENSE-2.0
"""
import ssl
import socket
import errno
from .parser import *

""" client class to connect to nsd control port and send calls
"""
class ControlClient(object):

    NSD_CONTROL_VERSION = 1
    BUFSIZE = 8192

    def __init__(self, clientCert, clientKey, host='127.0.0.1',
                 port=8952, bufsize=None, strip=False, parse=True):
        self.clientCert = clientCert
        self.clientKey = clientKey
        self._bufsize = bufsize or self.__class__.BUFSIZE
        self.host = host
        self.port = port
        self.sock = None
        self.strip = strip
        self.parse = parse

    """ deconstructor - auto close connection
    """
    def __del__(self):
        self.close()

    """ Set client certificate
    """
    def setClientCert(self, clientCert, clientKey):
        self.clientCert = clientCert
        self.clientKey = clientKey

    """ close connection if still open
    """
    def close(self):
        if self.sock is not None:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
            self.sock = None

    """ connect to "remote" host
    """
    def connect(self, host, port=8952):
        if self.sock is not None:
            self.close()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock = ssl.wrap_socket(s,
                                    certfile=self.clientCert,
                                    keyfile=self.clientKey)
        self.sock.connect((host, port))

    """ wrapper to make commands generic callable
    """
    def __getattr__(self, name):
        def fn(*args):
            return self.call(name, args)
        return fn

    """ send call to api
    """
    def __send(self, data):
        try:
            self.sock.sendall(data)
        except socket.timeout:
            self.close()
            raise

        except socket.sslerror:
            self.close()
            raise

        except socket.error:
            self.close()
            raise

    """ fetch result of previous call
    """
    def __fetch(self):
        buf = ''
        buf_len = 0

        while True:
            try:
                part = self.sock.read(self._bufsize - buf_len)
            except socket.timeout:
                self.close()
                raise

            except socket.sslerror, err:
                if (err[0] == socket.SSL_ERROR_WANT_READ or
                    err[0] == socket.SSL_ERROR_WANT_WRITE):
                    continue
                if (err[0] == socket.SSL_ERROR_ZERO_RETURN or
                    err[0] == socket.SSL_ERROR_EOF):
                    break
                self.close()
                raise

            except socket.error, err:
                if err[0] == errno.EINTR:
                    continue
                if err[0] == errno.EBADF:
                    """XXX socket was closed?
                    """
                    break
                self.close()
                raise

            if len(part) == 0:
                break
            buf += part
            buf_len += len(part)

        self.close()
        if self.strip:
            return buf.strip()
        return buf

    """ run a command and return result
    """
    def call(self, cmd, args=()):
        if self.sock is None:
            self.connect(self.host, self.port)

        """send header
        """
        self.__send("NSDCT%d " % (self.NSD_CONTROL_VERSION))

        """send command name
        """
        self.__send(' ' + cmd)

        """send command parameters
        """
        for arg in args:
            self.__send(' ' + arg)

        """send break line to commit command as completed
        """
        self.__send("\n")

        """fetch response
        """
        if self.parse:
            return ControlResultParser.parse(cmd, self.__fetch())

        return self.__fetch()
