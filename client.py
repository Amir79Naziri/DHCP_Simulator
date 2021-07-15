import socket
from dhcp_protocol import create_id, DHCP_discover_encode, DHCP_request_encode, DHCP_decode
from typing import Final
import time
import random


INITIAL_INTERVAL: Final = 120
BACK_OFF_CUTOFF = 10
MAC_ADDR = None
DEVICE_NAME = None


def discover(clientSocket, ID):
    global BACK_OFF_CUTOFF, INITIAL_INTERVAL

    s_query = DHCP_discover_encode(ID, MAC_ADDR, DEVICE_NAME)
    clientSocket.settimeout(BACK_OFF_CUTOFF)
    clientSocket.sendto(s_query, ('<broadcast>', 8080))

    try:
        while True:
            r_query, _ = clientSocket.recvfrom(1024)
            data = DHCP_decode(r_query)
            if data['XID'] == ID and data['CH_ADDR'] == MAC_ADDR and data['OP'] == 2 and \
                    data['M_TYPE'] == 'OFFER':
                return data
    except socket.timeout:
        BACK_OFF_CUTOFF = min(BACK_OFF_CUTOFF * 2 * random.uniform(0.5, 1), INITIAL_INTERVAL)
        return None


def request(clientSocket, ID, yi_addr, si_addr, init_time):
    s_query = DHCP_request_encode(ID, yi_addr, si_addr, MAC_ADDR, DEVICE_NAME)
    clientSocket.settimeout(init_time)
    clientSocket.sendto(s_query, ('<broadcast>', 8080))

    try:
        while True:
            r_query, _ = clientSocket.recvfrom(1024)
            data = DHCP_decode(r_query)
            if data['XID'] == ID and data['CH_ADDR'] == MAC_ADDR and data['OP'] == 2 and \
                    data['M_TYPE'] == 'ACK':

                return data
    except socket.timeout:
        return None


def start_client():
    ID = create_id()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as clientSocket:
            clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            clientSocket.bind(('0.0.0.0', 9090))

            while True:
                print('discovering...[timeout:{:.2f} s]'.format(BACK_OFF_CUTOFF))
                data = discover(clientSocket, ID)
                if data is None:
                    continue

                print('requesting...[timeout:{:.2f} s]'.format(10))
                data = request(clientSocket, ID, data['YI_ADDR'], data['SI_ADDR'], 10)
                if data is None:
                    continue

                while True:
                    lease_time = data['lease_time']
                    renewal_time = lease_time / 2
                    rebind_time = (3 / 4) * lease_time
                    print('ip allocated : ', data['YI_ADDR'])
                    time.sleep(renewal_time)

                    print('requesting, again...[timeout:{:.2f} s]'.format(10))
                    data = request(clientSocket, ID, data['YI_ADDR'], data['SI_ADDR'], rebind_time - renewal_time)
                    if data is None:
                        print('ip deactivated')
                        break

    except ConnectionError as msg:
        print(msg)
    except IOError as msg:
        print(msg)


if __name__ == '__main__':
    MAC_ADDR = input('mac_addr: ')
    DEVICE_NAME = input('device name: ')
    start_client()
