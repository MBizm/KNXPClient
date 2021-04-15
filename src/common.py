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

import re


def printIndividual(addr) -> str:
    return "{0}.{1}.{2}".format((addr >> 12) & 0x0f,
                                (addr >> 8) & 0x0f,
                                addr & 0xff)


def printGroup(addr) -> str:
    return "{0}.{1}.{2}".format((addr >> 11) & 0x1f,
                                (addr >> 8) & 0x07,
                                addr & 0xff)


def printValue(buffer, rlen) -> str:
    """
    converts buffer to hex string representation
    """
    ret = None
    if buffer[1] & 0xC0:
        if rlen == 2:
            ret = "%02X" % (buffer[1] & 0x3F)
        else:
            ret = printHex(rlen - 2, buffer[2:])
    # remove trailing blanks
    return ret.strip()


def readHex(val) -> int:
    return int(val, 16)


def printHex(len, buf) -> str:
    ret = ""
    for i in range(0, len):
        ret += "%02X " % buf[i]
    return ret


def readaddr(addr) -> int:
    ret = None
    r = re.compile('[./]').split(addr)

    if len(r) == 3:
        ret = ((int(r[0]) & 0x0f) << 12) | ((int(r[1]) & 0x0f) << 8) | (int(r[2]) & 0xff)
    elif len(r) == 1:
        ret = int(r[0]) & 0xffff
    else:
        raise ValueError("invalid individual address %s" % addr)

    return ret


def readgaddr(addr) -> int:
    ret = None
    r = re.compile('[./]').split(addr)

    if len(r) == 3:
        ret = ((int(r[0]) & 0x01f) << 11) | ((int(r[1]) & 0x07) << 8) | (int(r[2]) & 0xff)
    elif len(r) == 2:
        ret = ((int(r[0]) & 0x01f) << 11) | (int(r[1]) & 0x07FF)
    elif len(r) == 1:
        ret = int(r[0]) & 0xffff
    else:
        raise ValueError("invalid group address format %s" % addr)

    return ret


def readBlock(buf, vals):
    """
    converts hex representation of values into buffer representing values as int
    :param buf:     buffer to be filled for transmission
    :param vals:    values as list to be converted
    :return:        1. value: buffer for transmission, 2. value: number of values in buffer
    """
    i = 0
    for i in range(2, len(buf)):
        buf[i] = readHex(vals[i - 2])
    return buf, i
