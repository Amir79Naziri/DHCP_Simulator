from uuid import getnode as get_mac
import random
import struct


def create_id():
    ID = b''
    for i in range(4):
        ID += struct.pack('!B', random.randint(0, 255))

    return ID


def system_mac_addr():
    str_mac = hex(get_mac())[2:]
    while len(str_mac) < 12:
        str_mac = '0' + str_mac
    MAC = b''
    for _ in range(0, 12, 2):
        MAC += bytes.fromhex(str_mac[_:_ + 2])
    return MAC


def DHCP_discover_encode(ID):
    query = b'\x01'  # Message type: Boot Request (1)
    query += b'\x01'  # Hardware type: Ethernet
    query += b'\x06'  # Hardware address length: 6
    query += b'\x00'  # Hops: 0
    query += ID
    query += b'\x00\x00'  # Seconds elapsed: 0
    query += b'\x80\x00'  # Bootp flags: 0x8000 (Broadcast) + reserved flags
    query += b'\x00\x00\x00\x00'  # Client IP address: 0.0.0.0
    query += b'\x00\x00\x00\x00'  # Your (client) IP address: 0.0.0.0
    query += b'\x00\x00\x00\x00'  # Next server IP address: 0.0.0.0
    query += b'\x00\x00\x00\x00'  # Relay agent IP address: 0.0.0.0
    MAC = system_mac_addr()
    query += MAC  # Client MAC address
    query += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # Client hardware address padding: 00000000000000000000
    query += b'\x00' * 64  # Server host name not given
    query += b'\x00' * 128  # Boot file name not given
    # query += b'\x63\x82\x53\x63'  # Magic cookie: DHCP
    # query += b'\x35\x01\x01'  # Option: (t=53,l=1) DHCP Message Type = DHCP Discover
    # query += b'\x3d\x06' + MAC  # Option: (t=61,l=6) Client identifier
    # query += b'\x37\x03\x03\x01\x06'  # Option: (t=55,l=3) Parameter Request List
    query += b'\xff'  # End Option

    return query


def DHCP_discover_decode(data):
    pivot = 0
    OP = data[pivot:pivot + 1]
    pivot += 1
    H_TYPE = data[pivot:pivot + 1]
    pivot += 1
    H_LEN = data[pivot:pivot + 1]
    pivot += 1
    HOPS = data[pivot:pivot + 1]
    pivot += 1
    XID = data[pivot:pivot + 4]
    pivot += 4
    SECS = data[pivot:pivot + 2]
    pivot += 2
    FLAGS = data[pivot:pivot + 2]
    pivot += 2
    CI_ADDR = data[pivot:pivot + 4]
    pivot += 4
    YI_ADDR = data[pivot:pivot + 4]
    pivot += 4
    SI_ADDR = data[pivot:pivot + 4]
    pivot += 4
    GI_ADDR = data[pivot:pivot + 4]
    pivot += 4
    CH_ADDR = data[pivot:pivot + 16]
    pivot += 16
    S_NAME = data[pivot:pivot + 64]
    pivot += 64
    FILE = data[pivot:pivot + 128]
    pivot += 128
    # M_COOKIE = data[pivot:pivot + 4]
    # pivot += 4
    # DHCP_MESSAGE_TYPE = data[pivot:pivot + 3]
    # pivot += 3
    # CLIENT_ID = data[pivot:pivot + 18]
    # pivot += 18
    # R_LIST = data[pivot:pivot + 5]
    # pivot += 5
    # END = data[pivot:pivot + 1]
    pivot += 1


def DHCP_offer_decode(data, ID):
    if data[4:8] == ID:
        offerIP = '.'.join(map(lambda x: str(x), data[16:20]))
        nextServerIP = '.'.join(map(lambda x: str(x), data[20:24]))
        DHCPServerIdentifier = '.'.join(map(lambda x: str(x), data[245:249]))
        leaseTime = str(struct.unpack('!L', data[251:255])[0])
        router = '.'.join(map(lambda x: str(x), data[257:261]))
        subnetMask = '.'.join(map(lambda x: str(x), data[263:267]))
        dnsNB = int(data[268] / 4)
        DNS = []
        for i in range(0, 4 * dnsNB, 4):
            DNS.append('.'.join(map(lambda x: str(x), data[269 + i:269 + i + 4])))



