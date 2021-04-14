#!/usr/bin/python

#
#   EIBD client library
#   Copyright (C) 2005-2011 Martin Koegler <mkoegler@auto.tuwien.ac.at>
#
#   Adapted to EIB/KNX client implementation for Python by:
#   Copyright (C) 2021 Michael Bernhardt [https://github.com/MBizm]
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   In addition to the permissions in the GNU General Public License,
#   you may link the compiled version of this file into combinations
#   with other programs, and distribute those combinations without any
#   restriction coming from the use of this file. (The General Public
#   License restrictions do apply in other respects; for example, they
#   cover modification of the file, and distribution when not linked into
#   a combine executable.)
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#


from __future__ import print_function

from common import *
from EIBConnection import EIBConnection, EIBAddr, EIBBuffer


def run(port, adr):
    c = EIBConnection()
    if port[0] == '/':
        c.EIBSocketLocal(port)
    else:
        parts = port.split(':')
        if len(parts) == 1:
            parts.append(6720)
        c.EIBSocketRemote(parts[0], int(parts[1]))
    c.EIBOpen_GroupSocket(adr)
    buf = EIBBuffer()
    src = EIBAddr()
    dest = EIBAddr()
    while c.EIBGetGroup_Src(buf, src, dest):
        print("%s(%s) > %s(%s): %s" % (printGroup(src.data), src.data,
                                       printGroup(dest.data), dest.data,
                                       repr(buf.buffer)))


if __name__ == "__main__":
    import sys

    args = list(sys.argv[1:])
    if args:
        try:
            adr = int(args[-1])
        except ValueError:
            adr = 0
        else:
            args.pop()
    else:
        adr = 0
    if args:
        port = args[0]
    else:
        import os

        if os.path.exists('/run/knx'):
            port = '/run/knx'
        elif os.path.exists('/tmp/eib'):
            port = '/tmp/eib'
        else:
            port = 'localhost'
    run(port, adr)
