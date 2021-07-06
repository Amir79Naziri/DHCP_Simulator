from uuid import getnode as get_mac
import random
import struct


class HARDCODES:
    REQUEST = b'\x01'
    REPLY = b'\x02'
    ETHERNET = b'\x01'
    HARDWARE_ADDR_LEN = b'\x06'
    HOPS = b'\x00'
    SEC_ELAPSED = b'\x00\x00'
    BOOTP_FLAGS = b'\x00\x00'
    MAC_ADDR_PADDING = b'\x00' * 10
    SNAME = b'\x00' * 64
    FILE = b'\x00' * 128
    DEFAULT_IP = b'\x00\x00\x00\x00'
    END_OPTION = b'\xff'


def create_id():
    ID = b''
    for i in range(4):
        ID += struct.pack('!B', random.randint(0, 255))

    return ID


def mac_addr_to_byte(mac=None):
    if mac is None:
        mac = hex(get_mac())[2:]
    else:
        mac = mac.replace('.', '')
    while len(mac) < 12:
        mac = '0' + mac
    MAC_bytes = b''
    for _ in range(0, 12, 2):
        MAC_bytes += bytes.fromhex(mac[_:_ + 2])
    return MAC_bytes


def ip_addr_to_byte(ip_addr):
    IP_Byte = b''
    for i in ip_addr.split('.'):
        IP_Byte += struct.pack('!B', int(i))
    return IP_Byte


def byte_to_ip_addr(byte_array):
    return '.'.join(map(lambda x: str(x), byte_array))


def byte_to_mac_addr(byte_array):
    MAC = byte_array.hex()
    return '.'.join(MAC[i:i + 2] for i in range(0, 12, 2))


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
    MAC = mac_addr_to_byte()
    query += MAC
    query += HARDCODES.MAC_ADDR_PADDING
    query += HARDCODES.SNAME
    query += HARDCODES.FILE

    # OPTIONS

    query += b'\x35\x01\x01'  # Option: (t=53,l=1) DHCP Message Type = DHCP Discover
    query += HARDCODES.END_OPTION

    return query


def DHCP_offer_encode(ID, suggested_ip, server_ip, lease_time):
    query = HARDCODES.REPLY
    query += HARDCODES.ETHERNET
    query += HARDCODES.HARDWARE_ADDR_LEN
    query += HARDCODES.HOPS
    query += ID
    query += HARDCODES.SEC_ELAPSED
    query += HARDCODES.BOOTP_FLAGS
    query += HARDCODES.DEFAULT_IP
    query += ip_addr_to_byte(suggested_ip)
    query += ip_addr_to_byte(server_ip)
    query += HARDCODES.DEFAULT_IP
    MAC = mac_addr_to_byte()
    query += MAC
    query += HARDCODES.MAC_ADDR_PADDING
    query += HARDCODES.SNAME
    query += HARDCODES.FILE

    # OPTIONS

    query += b'\x35\x01\x02'  # Option: (t=53,l=1) DHCP Message Type = DHCP Offer
    query += b'\x33\x04' + struct.pack('!L', lease_time)  # Option: (t=51,l=2)  lease time
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
    MAC = mac_addr_to_byte()
    query += MAC
    query += HARDCODES.MAC_ADDR_PADDING
    query += HARDCODES.SNAME
    query += HARDCODES.FILE

    # OPTIONS

    query += b'\x35\x01\x03'  # Option: (t=53,l=1) DHCP Message Type = DHCP Request
    query += HARDCODES.END_OPTION

    return query


def DHCP_ack_encode(ID, allocated_ip, server_ip, lease_time):
    query = HARDCODES.REPLY
    query += HARDCODES.ETHERNET
    query += HARDCODES.HARDWARE_ADDR_LEN
    query += HARDCODES.HOPS
    query += ID
    query += HARDCODES.SEC_ELAPSED
    query += HARDCODES.BOOTP_FLAGS
    query += HARDCODES.DEFAULT_IP
    query += ip_addr_to_byte(allocated_ip)
    query += ip_addr_to_byte(server_ip)
    query += HARDCODES.DEFAULT_IP
    MAC = mac_addr_to_byte()
    query += MAC
    query += HARDCODES.MAC_ADDR_PADDING
    query += HARDCODES.SNAME
    query += HARDCODES.FILE

    # OPTIONS

    query += b'\x35\x01\x05'  # Option: (t=53,l=1) DHCP Message Type = DHCP ack
    query += b'\x33\x04' + struct.pack('!L', lease_time)  # Option: (t=51,l=2)  lease time
    query += HARDCODES.END_OPTION

    return query


def DHCP_decode(data):
    decoded_data = dict()

    pivot = 0
    decoded_data['OP'] = data[pivot:pivot + 1]
    pivot += 1
    decoded_data['HW_TYPE'] = data[pivot:pivot + 1]
    pivot += 1
    decoded_data['HW_LEN'] = data[pivot:pivot + 1]
    pivot += 1
    decoded_data['HOPS'] = data[pivot:pivot + 1]
    pivot += 1
    decoded_data['XID'] = data[pivot:pivot + 4]
    pivot += 4
    decoded_data['SECS'] = data[pivot:pivot + 2]
    pivot += 2
    decoded_data['FLAGS'] = data[pivot:pivot + 2]
    pivot += 2
    decoded_data['CI_ADDR'] = byte_to_ip_addr(data[pivot:pivot + 4])
    pivot += 4
    decoded_data['YI_ADDR'] = byte_to_ip_addr(data[pivot:pivot + 4])
    pivot += 4
    decoded_data['SI_ADDR'] = byte_to_ip_addr(data[pivot:pivot + 4])
    pivot += 4
    decoded_data['GI_ADDR'] = byte_to_ip_addr(data[pivot:pivot + 4])
    pivot += 4
    decoded_data['CH_ADDR'] = byte_to_mac_addr(data[pivot:pivot + 16])
    pivot += 16
    decoded_data['S_NAME'] = data[pivot:pivot + 64]
    pivot += 64
    decoded_data['FILE'] = data[pivot:pivot + 128]
    pivot += 128

    # OPTIONS

    pivot_copy = pivot

    while True:
        T = data[pivot_copy]
        pivot_copy += 1
        L = data[pivot_copy]
        pivot_copy += 1
        if T == 53:
            code = data[pivot_copy]
            if code == 1:
                M_TYPE = 'DISCOVER'
            elif code == 2:
                M_TYPE = 'OFFER'
            elif code == 3:
                M_TYPE = 'REQUEST'
            elif code == 5:
                M_TYPE = 'ACK'
            else:
                M_TYPE = 'UNKNOWN'
            break

        elif T == 255:
            M_TYPE = 'UNKNOWN'
            break
        else:
            pivot_copy += L

    if M_TYPE == 'UNKNOWN':
        return dict()

    decoded_data['M_TYPE'] = M_TYPE

    if M_TYPE == 'OFFER' or M_TYPE == 'ACK':
        pivot_copy = pivot

        while True:
            T = data[pivot_copy]
            pivot_copy += 1
            L = data[pivot_copy]
            pivot_copy += 1
            if T == 51:
                decoded_data['lease_time'] = int(struct.unpack('!L', data[pivot_copy:pivot_copy + L])[0])
                break
            elif T == 255:
                decoded_data['lease_time'] = -1
                break
            else:
                pivot_copy += L
    else:
        decoded_data['lease_time'] = -1

    return decoded_data


if __name__ == '__main__':
    print(DHCP_decode(DHCP_offer_encode(create_id(), '127.0.0.1', '10.10.01.1', 3600)))