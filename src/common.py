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


def readHex(val) -> str:
    return int(val, 16)


def printHex(len, buf) -> str:
    ret = ""
    for i in range(0, len):
        ret += "%02X " % buf[i]
    return ret


def readaddr(addr):
    ret = None
    r = re.compile('[./]').split(addr)

    if len(r) == 3:
        ret = ((int(r[0]) & 0x0f) << 12) | ((int(r[1]) & 0x0f) << 8) | (int(r[2]) & 0xff)
    elif len(r) == 1:
        ret = int(r[0]) & 0xffff
    else:
        die("invalid individual address %s" % addr)

    return ret


def readgaddr(addr):
    ret = None
    r = re.compile('[./]').split(addr)

    if len(r) == 3:
        ret = ((int(r[0]) & 0x01f) << 11) | ((int(r[1]) & 0x07) << 8) | (int(r[2]) & 0xff)
    elif len(r) == 2:
        ret = ((int(r[0]) & 0x01f) << 11) | (int(r[1]) & 0x07FF)
    elif len(r) == 1:
        ret = int(r[0]) & 0xffff
    else:
        die("invalid group address format %s" % addr)

    return ret


def readBlock(buf, vals):
    i = 0
    for i in range(2, len(buf)):
        buf[i] = readHex(vals[i-2])
    return buf, i


def die(msg):
    print(msg)
    exit(1)
