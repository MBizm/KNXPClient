import re


def printIndividual(addr) -> str:
    return "{0}.{1}.{2}".format((addr >> 12) & 0x0f,
                                (addr >> 8) & 0x0f,
                                addr & 0xff)


def printGroup(addr) -> str:
    return "{0}.{1}.{2}".format((addr >> 11) & 0x1f,
                                (addr >> 8) & 0x07,
                                addr & 0xff)


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


def die(msg):
    print(msg)
    exit(1)
