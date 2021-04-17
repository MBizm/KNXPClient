"""
    EIB/KNX client implementation for Python based on the great work by:
    - Martin Koegler <mkoegler@auto.tuwien.ac.at>
    - Mathias Urlichs <http://matthias.urlichs.de/>

    Copyright (C) 2021 Michael Bernhardt [https://github.com/MBizm]

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""

from __future__ import print_function

import os
import threading

from common import *
from EIBConnection import EIBConnection, EIBAddr, EIBBuffer


class EIBClientListener(object):
    __gaddrInt = 0

    """
    Abstract Listener implementation
    Derive your own implementation if you want to permanently monitor for new values sent on the bus
    and register via the EIBClientFactory
    """

    def __init__(self, gaddr):
        """
        initialize a new listener class, events will be reported via updateOccured method
        :param gaddr: KNX string representation of group address to be listened to ("1/0/3")
        """
        self.__gaddrInt = readgaddr(gaddr)

    @property
    def gaddrInt(self) -> int:
        return self.__gaddrInt

    def getGoupAddressText(self) -> str:
        return printGroup(self.__gaddrInt)

    def updateOccurred(self, srcAddr, val):
        raise NotImplementedError


class EIBClient(object):
    __EIBConnection = None

    def flush(self):
        """
        closes socket connection and reset all instance variables
        """
        # close socket connection
        if self.__EIBConnection and self.__EIBConnection.fd:
            self.__EIBConnection.fd.close()

    def getEIBConnection(self):
        return self.__EIBConnection

    def setEIBConnection(self, port):
        """
        Establishes the socket connection
        """
        c = EIBConnection()
        if port[0] == '/':
            c.EIBSocketLocal(port)
        else:
            parts = port.split(':')
            if len(parts) == 1:
                parts.append(6720)
            c.EIBSocketRemote(parts[0], int(parts[1]))

        self.__EIBConnection = c

    def GroupCache_Read(self, addrSrc):
        """
        reads value from local cache
        :param addrSrc: KNX address with "/" separator
        :return: current value in cache
        """
        raise NotImplementedError

    def Group_Write_DPTVal(self, addrDest, val):
        raise NotImplementedError


class _EIBClient(EIBClient):
    """
    Implementation of an EIB/KNX client
    This class mimics the behavior of knxdtool implementation
    """

    def GroupCache_Read(self, addrSrc):
        """
        reads value from local cache
        :param      addrSrc: KNX address with "/" separator
        :return:    string representation of hexified value in cache
        :raises:    ValueError
        """
        buf = EIBBuffer()
        src = EIBAddr()

        # call group cache
        rlen = self.__EIBConnection.EIB_Cache_Read(readgaddr(addrSrc),
                                                   src,
                                                   buf)

        if rlen == -1:
            raise ValueError("Read failed - " + os.strerror(self.__EIBConnection.errno))
        elif len(buf.buffer) < 2:
            raise ValueError("Buffer size too small - {0}: {1}".format(addrSrc,
                                                                       buf.buffer))

        return printValue(buf.buffer, rlen)

    def Group_Write_DPTVal(self, addrDest, val):
        vals = re.compile(r"[ \t]").split(val)

        lbuf = [0x0] * (len(vals) + 2)
        # init buffer lbuf[0] = 0x0, lbuf[1] = 0x80
        lbuf[1] = 0x80

        lbuf, length = readBlock(lbuf, vals)
        if length < 0:
            raise ValueError("Invalid hex bytes")

        if self.__EIBConnection.EIBOpenT_Group(readgaddr(addrDest), 1) == -1:
            raise ConnectionError("Connect failed")

        length = self.__EIBConnection.EIBSendAPDU(lbuf)
        if length == -1:
            raise ConnectionError("Send request failed")

        # report success
        return 1


class EIBClientFactory(object):
    """
    Factory for EIB/KNX client creation
    Depending on whether a one-time request or a permanent monitoring, factory will instanicate corresponding object
    """
    __factoryInstance = None
    __clientInstance = None
    __clientMonitorInstance = None

    def __new__(cls, *args, **kwargs):
        """
        setup of EIBClient singleton instance
        :return:
        """
        if EIBClientFactory.__factoryInstance is None:
            EIBClientFactory.__factoryInstance = object.__new__(cls)
        return EIBClientFactory.__factoryInstance

    @staticmethod
    def getClient() -> EIBClient:
        if EIBClientFactory.__clientInstance is None:
            EIBClientFactory.__clientInstance = EIBClientFactory.__initializeNewClient()
        return EIBClientFactory.__clientInstance

    @staticmethod
    def getMonitorClient() -> EIBClient:
        if EIBClientFactory.__clientMonitorInstance is None:
            EIBClientFactory.__clientMonitorInstance = EIBClientFactory.__initializeNewClient()
        return EIBClientFactory.__clientMonitorInstance

    @staticmethod
    def __initializeNewClient():
        client = _EIBClient()
        # find KNX/EIB daemon - for now only local instances
        if os.path.exists('/run/knx'):
            port = '/run/knx'
        elif os.path.exists('/tmp/eib'):
            port = '/tmp/eib'
        else:
            port = 'localhost'
        client.setEIBConnection(port)
        return client

    @staticmethod
    def registerListener(listener: EIBClientListener):
        """
        registers listener that will be informed of updates for the defined group address
        :param listener:    listener instance
        :type listener:     EIBClientListener
        """
        if not listener:
            return

        _EIBClientMonitor.register(listener)

    @staticmethod
    def unregisterListener(listener: EIBClientListener):
        _EIBClientMonitor.unregister(listener)


class _EIBClientMonitor(threading.Thread):
    """
    Signleton monitor permanently watching the queue and calls callback function
    if listener is registered for a dedicated group address being updated.
    """
    __instance = None
    __listenerList = []

    def __new__(cls, *args, **kwargs):
        """
        starts separate thread for monitoring the bus
        """
        if _EIBClientMonitor.__instance is None:
            _EIBClientMonitor.__instance = object.__new__(cls)
        return _EIBClientMonitor.__instance

    def run(self):
        con = EIBClientFactory.getMonitorClient().getEIBConnection()
        # register broadcast monitor
        con.EIBOpen_GroupSocket(0)
        buf = EIBBuffer()
        src = EIBAddr()
        dest = EIBAddr()
        while con.EIBGetGroup_Src(buf, src, dest):
            listener = self.findListener(gaddrInt=dest.data)
            # only for debug
            # print("%s(%s) > %s(%s): %s" % (printGroup(src.data), src.data,
            #                                printGroup(dest.data), dest.data,
            #                                repr(buf.buffer)))
            # continue in case no listener registered for destination
            if listener is None:
                continue
            # check whether multiple listeners for destination exists
            if listener and isinstance(listener, list):
                for rl in listener:
                    self.__informListener(rl, buf, dest, src)
            else:
                self.__informListener(listener, buf, dest, src)

    @staticmethod
    def __informListener(listener, buf, dest, src):
        listener.updateOccurred(src.data, buf.buffer)

    @staticmethod
    def register(listener):
        m = _EIBClientMonitor()

        # start thread once, temporary solution - see remarks below
        if len(m.__listenerList) == 0:
            m.start()

        if not m.findListener(listener):
            m.__listenerList.append(listener)

            # TODO for now is_alive() is not accurate enough and starts thread multiple times
            #       see https://stackoverflow.com/questions/67099275/threadings-is-alive-method-not-returning-accurate-state
            #       let's use listenerList size for now as the criteria to start the thread
            # initialize monitor in separate thread if not yet running
            # if not m.is_alive():
            #    m.start()

    @staticmethod
    def unregister(listener):
        _EIBClientMonitor.__listenerList.remove(listener)

        # stop monitoring if last listener removed
        if len(_EIBClientMonitor.__listenerList) == 0:
            _EIBClientMonitor().stop()

    @staticmethod
    def findListener(listener=None, gaddrInt=0):
        """
        Checks list of listeners for existance of corresponding listener identified by instance OR group address
        :type listener:     EIBClientListener
        :param gaddrInt:    group address under which listener instance is registered
        :type gaddrInt:     int
        :return:            list of one or multiple listeners registered for the same group address, None if not registered for address
        """
        ret = None
        if listener and listener in _EIBClientMonitor.__listenerList:
            ret = [listener, ]
        if gaddrInt >= 0:
            for rl in _EIBClientMonitor.__listenerList:
                if rl.gaddrInt == gaddrInt:
                    # append matching listener instances
                    if not ret:
                        ret = []
                    ret += [rl, ]
        return ret


if __name__ == '__main__':
    cf = EIBClientFactory()
    c = cf.getClient()

    # read sample value
    # val = c.GroupCache_Read("1/0/3")
    # print("Read group cache value: \t" + str(val))

    # write sample value
    val = c.Group_Write_DPTVal('1/0/3', '44 B1 00 01')
    if val:
        print("Write group value: \tValue successful transmitted")
    else:
        print("Write group value: \tFailed to transmit value!")

    # monitor sample value
    class MyEIBClientListener(EIBClientListener):
        def updateOccurred(self, srcAddr, val):
            print("### This is the value you were waiting for - FROM: {0} VALUE: {1}".format(printGroup(srcAddr), val))
    cf.registerListener(MyEIBClientListener('1/0/3'))


    # monitor same sample value twice
    class MyEIBClientListener2(EIBClientListener):
        def updateOccurred(self, srcAddr, val):
            print("### This is also the value you were waiting for - FROM: {0} VALUE: {1}".format(printGroup(srcAddr),
                                                                                                  val))
    cf.registerListener(MyEIBClientListener2('1/0/3'))
