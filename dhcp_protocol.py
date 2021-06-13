from uuid import getnode as get_mac
import random
import struct
import socket


class HARDCODES:
    REQUEST = b'\x01'
    REPLY = b'\x02'
    ETHERNET = b'\x01'
    HARDWARE_ADDR_LEN = b'\x06'
    HOPS = b'\x00'
    SEC_ELAPSED = b'\x00\x00'
    BOOTP_FLAGS = b'\x00\x00'
    MAC_ADDR_PADDING = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SNAME = b'\x00' * 64
    FILE = b'\x00' * 128
    DEFAULT_IP = b'\x00\x00\x00\x00'
    END_OPTION = b'\xff'


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


def ip_addr_to_byte(ip_addr):
    IP_Byte = b''
    for i in ip_addr.split('.'):
        IP_Byte += struct.pack('!B', int(i))
    return IP_Byte


def DHCP_discover_encode(ID):
    query = HARDCODES.REQUEST
    query += HARDCODES.ETHERNET
    query += HARDCODES.HARDWARE_ADDR_LEN
    query += HARDCODES.HOPS
    query += ID
    query += HARDCODES.SEC_ELAPSED
    query += HARDCODES.BOOTP_FLAGS
    query += HARDCODES.DEFAULT_IP
    query += HARDCODES.DEFAULT_IP
    query += HARDCODES.DEFAULT_IP
    query += HARDCODES.DEFAULT_IP
    MAC = system_mac_addr()
    query += MAC
    query += HARDCODES.MAC_ADDR_PADDING
    query += HARDCODES.SNAME
    query += HARDCODES.FILE

    # OPTIONS

    query += b'\x35\x01\x01'  # Option: (t=53,l=1) DHCP Message Type = DHCP Discover
    query += b'\x33\x06' + MAC  # Option: (t=51, l=6) Client identifier
    query += b'\x37\x03\x03\x01\x06'  # Option: (t=55,l=3) Parameter Request List
    query += HARDCODES.END_OPTION

    return query


def DHCP_offer_encode(ID, suggested_ip):
    query = HARDCODES.REPLY
    query += HARDCODES.ETHERNET
    query += HARDCODES.HARDWARE_ADDR_LEN
    query += HARDCODES.HOPS
    query += ID
    query += HARDCODES.SEC_ELAPSED
    query += HARDCODES.BOOTP_FLAGS
    query += HARDCODES.DEFAULT_IP
    query += ip_addr_to_byte(suggested_ip)
    query += ip_addr_to_byte(socket.gethostbyname(socket.gethostname()))
    query += HARDCODES.DEFAULT_IP
    MAC = system_mac_addr()
    query += MAC
    query += HARDCODES.MAC_ADDR_PADDING
    query += HARDCODES.SNAME
    query += HARDCODES.FILE

    # OPTIONS

    query += b'\x35\x01\x02'  # Option: (t=53,l=1) DHCP Message Type = DHCP Offer
    query += b'\x33\x02\x0E\x10'  # Option: (t=51,l=2)  lease time
    query += b'\x36\x04' + ip_addr_to_byte(socket.gethostbyname(socket.gethostname()))  # Option: (t=54,l=4)
    query += HARDCODES.END_OPTION

    return query


def DHCP_request_encode(ID, requested_ip, server_ip):
    query = HARDCODES.REQUEST
    query += HARDCODES.ETHERNET
    query += HARDCODES.HARDWARE_ADDR_LEN
    query += HARDCODES.HOPS
    query += ID
    query += HARDCODES.SEC_ELAPSED
    query += HARDCODES.BOOTP_FLAGS
    query += ip_addr_to_byte(requested_ip)
    query += HARDCODES.DEFAULT_IP
    query += ip_addr_to_byte(server_ip)
    query += HARDCODES.DEFAULT_IP
    MAC = system_mac_addr()
    query += MAC
    query += HARDCODES.MAC_ADDR_PADDING
    query += HARDCODES.SNAME
    query += HARDCODES.FILE

    # OPTIONS

    query += b'\x35\x01\x03'  # Option: (t=53,l=1) DHCP Message Type = DHCP Request
    query += b'\x32\x04' + ip_addr_to_byte(requested_ip)   # Option: (t=50,l=4) requested IP
    query += b'\x36\x04' + ip_addr_to_byte(server_ip)  # Option: (t=54,l=4) server IP
    query += HARDCODES.END_OPTION

    return query


def DHCP_ack_encode(ID, allocated_ip, lease_time_bytes):
    query = HARDCODES.REPLY
    query += HARDCODES.ETHERNET
    query += HARDCODES.HARDWARE_ADDR_LEN
    query += HARDCODES.HOPS
    query += ID
    query += HARDCODES.SEC_ELAPSED
    query += HARDCODES.BOOTP_FLAGS
    query += HARDCODES.DEFAULT_IP
    query += ip_addr_to_byte(allocated_ip)
    query += ip_addr_to_byte(socket.gethostbyname(socket.gethostname()))
    query += HARDCODES.DEFAULT_IP
    MAC = system_mac_addr()
    query += MAC
    query += HARDCODES.MAC_ADDR_PADDING
    query += HARDCODES.SNAME
    query += HARDCODES.FILE

    # OPTIONS

    query += b'\x35\x01\x05'  # Option: (t=53,l=1) DHCP Message Type = DHCP ack
    query += b'\x33\x02' + lease_time_bytes  # Option: (t=51,l=2)  lease time
    query += ip_addr_to_byte(socket.gethostbyname(socket.gethostname()))
    query += HARDCODES.END_OPTION

    return query


def DHCP_offer_decode(data, ID):
    if data[4:8] == ID:
        offerIP = '.'.join(map(lambda x: str(x), data[16:20]))
        nextServerIP = '.'.join(map(lambda x: str(x), data[20:24]))
        DHCPServerIdentifier = '.'.join(map(lambda x: str(x), data[245:249]))
        leaseTime = str(struct.unpack('!L', data[251:255])[0])


if __name__ == '__main__':
    print(socket.gethostbyname(socket.gethostname()))
    print(ip_addr_to_byte(socket.gethostbyname(socket.gethostname())))
