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

from common import *
from EIBConnection import EIBConnection, EIBAddr, EIBBuffer


class EIBClient(object):
    """ central instance (singleton) handling all requests to KNXDDaemon """
    __instance = None
    __EIBConnection = None

    @staticmethod
    def __getEIBConnection(port) -> EIBConnection:
        """
        Establishs the socket connection
        :return: EIBConnection object, local or remote
        """
        c = EIBConnection()
        if port[0] == '/':
            c.EIBSocketLocal(port)
        else:
            parts = port.split(':')
            if len(parts) == 1:
                parts.append(6720)
            c.EIBSocketRemote(parts[0], int(parts[1]))
        return c

    def __new__(cls, *args, **kwargs):
        """
        setup of EIBClient singleton instance
        :return:
        """
        if EIBClient.__instance is None:
            EIBClient.__instance = object.__new__(cls)
            # find KNX/EIB daemon - for now only local instances
            if os.path.exists('/run/knx'):
                port = '/run/knx'
            elif os.path.exists('/tmp/eib'):
                port = '/tmp/eib'
            else:
                port = 'localhost'
            EIBClient.__EIBConnection = EIBClient.__getEIBConnection(port)
        return EIBClient.__instance

    @staticmethod
    def flush():
        """
        closes socket connection and reset all instance variables
        """
        # close socket connection
        EIBClient.__EIBConnection.fd.close()
        # release signleton handle
        EIBClient.__instance = None

    def GroupCache_Read(self, addrSrc):
        """
        reads value from local cache
        :param addrSrc: KNX address with "/" separator
        :return: current value in cache
        """
        ret = None
        buf = EIBBuffer()
        src = EIBAddr()

        # call group cache
        rlen = self.__EIBConnection.EIB_Cache_Read(readgaddr(addrSrc),
                                                   src,
                                                   buf)

        if rlen == -1:
            die("Read failed - " + os.strerror(self.__EIBConnection.errno))

        if buf.buffer[1] & 0xC0:
            if rlen == 2:
                ret = "%02X" % (buf.buffer[1] & 0x3F)
            else:
                ret = printHex(rlen - 2, buf.buffer[2:])
        # remove trailing blanks
        ret = ret.strip()

        return ret

    def Group_Write_DPTVal(self, addrDest, val):
        vals = re.compile(r"[ \t]").split(val)

        lbuf = [0x0] * (len(vals) + 2)
        # init buffer lbuf[0] = 0x0, lbuf[1] = 0x80
        lbuf[1] = 0x80

        lbuf, length = readBlock(lbuf, vals)
        if length < 0:
            die("Invalid hex bytes")

        if self.__EIBConnection.EIBOpenT_Group(readgaddr(addrDest), 1) == -1:
            die("Connect failed")

        length = self.__EIBConnection.EIBSendAPDU(lbuf)
        if length == -1:
            die("Request failed")

        # report success
        return 1


if __name__ == '__main__':
    c = EIBClient()

    # val = c.GroupCache_Read("1/0/3")
    # print("Read group cache value: \t" + str(val))

    val = c.Group_Write_DPTVal('1/0/3', '44 B1 00 01')
    if val:
        print("Write group value: \tValue successful transmitted")
    else:
        print("Write group value: \tFailed to transmit value!")
