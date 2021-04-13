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
        printGroup(readgaddr(addrSrc))
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


if __name__ == '__main__':
    val = EIBClient().GroupCache_Read("1/0/3")
    print(str(val))
