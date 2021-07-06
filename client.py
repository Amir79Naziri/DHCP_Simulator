import socket
import dhcp_protocol
from typing import Final
import time
import random
from threading import Thread

INITIAL_INTERVAL: Final = 120
BACK_OFF_CUTOFF = 10
MAC_ADDR = None
DEVICE_NAME = None


def timer(init_time):
    while True:
        time.sleep(1)
        init_time -= 1
        if init_time <= 0:
            raise TimeoutError


def discover(clientSocket, ID):
    global BACK_OFF_CUTOFF, INITIAL_INTERVAL

    s_query = dhcp_protocol.DHCP_discover_encode(ID, MAC_ADDR)
    clientSocket.sendto(s_query, ('<broadcast>', 8080))

    try:
        Thread(target=timer, args=(BACK_OFF_CUTOFF,)).start()
        while True:
            r_query = clientSocket.recvfrom(1024)
            data = dhcp_protocol.DHCP_decode(r_query)
            if data['XID'] == ID and data['CH_ADDR'] == MAC_ADDR and data['OP'] == 2 and \
                    data['M_TYPE'] == 'OFFER':
                return data
    except TimeoutError:
        BACK_OFF_CUTOFF = BACK_OFF_CUTOFF * 2 * random.random()
        return None


def request(clientSocket, ID, yi_addr, si_addr, init_time):

    s_query = dhcp_protocol.DHCP_request_encode(ID, yi_addr, si_addr, MAC_ADDR)
    clientSocket.sendto(s_query, ('<broadcast>', 8080))

    try:
        Thread(target=timer, args=(init_time,)).start()
        while True:
            r_query = clientSocket.recvfrom(1024)
            data = dhcp_protocol.DHCP_decode(r_query)
            if data['XID'] == ID and data['CH_ADDR'] == MAC_ADDR and data['OP'] == 2 and \
                    data['M_TYPE'] == 'ACK':
                return data
    except TimeoutError:
        return None


def start_client():
    ID = dhcp_protocol.create_id()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as clientSocket:
            clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            clientSocket.bind(('0.0.0.0', 9090))

            while True:
                data = discover(clientSocket, ID)
                if data is None:
                    continue

                data = request(clientSocket, ID, data['YI_ADDR'], data['SI_ADDR'])
                if data is None:
                    continue

                while True:
                    lease_time = data['lease_time']
                    renewal_time = lease_time / 2
                    rebind_time = (3 / 4) * lease_time
                    print('ip allocated : ', data['YI_ADDR'])
                    time.sleep(renewal_time)

                    data = request(clientSocket, ID, data['YI_ADDR'], data['SI_ADDR'], rebind_time - renewal_time)
                    if data is None:
                        break

    except socket.timeout as msg:
        print(msg)
    except ConnectionError as msg:
        print(msg)
    except IOError as msg:
        print(msg)


if __name__ == '__main__':
    MAC_ADDR = input('mac_addr: ')
    DEVICE_NAME = input('device name: ')
    start_client()
