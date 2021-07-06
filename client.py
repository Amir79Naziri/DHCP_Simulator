import socket
from dhcp_protocol import create_id, DHCP_discover_encode, DHCP_request_encode, DHCP_decode
from typing import Final
import time
import random
from threading import Thread

INITIAL_INTERVAL: Final = 120
BACK_OFF_CUTOFF = 10
MAC_ADDR = None
DEVICE_NAME = None


class Timer(Thread):

    def __init__(self, init_time):
        super().__init__()
        self.exception = None
        self.init_time = init_time

    def run(self) -> None:
        try:
            while True:
                time.sleep(1)
                self.init_time -= 1
                if self.init_time <= 0:
                    raise TimeoutError('time out')
        except TimeoutError as e:
            self.exception = e

    def wait(self):
        Thread.join(self)

        if self.exception:
            raise self.exception


def discover(clientSocket, ID):
    global BACK_OFF_CUTOFF, INITIAL_INTERVAL

    s_query = DHCP_discover_encode(ID, MAC_ADDR, DEVICE_NAME)
    clientSocket.sendto(s_query, ('<broadcast>', 8080))
    th_timer = Timer(BACK_OFF_CUTOFF)
    th_timer.start()
    try:
        th_timer.wait()
        while True:
            r_query = clientSocket.recvfrom(1024)
            data = DHCP_decode(r_query)
            if data['XID'] == ID and data['CH_ADDR'] == MAC_ADDR and data['OP'] == 2 and \
                    data['M_TYPE'] == 'OFFER':
                return data
    except TimeoutError:
        BACK_OFF_CUTOFF = BACK_OFF_CUTOFF * 2 * random.uniform(0.5, 1)
        print('here')
        return None


def request(clientSocket, ID, yi_addr, si_addr, init_time):
    s_query = DHCP_request_encode(ID, yi_addr, si_addr, MAC_ADDR, DEVICE_NAME)
    clientSocket.sendto(s_query, ('<broadcast>', 8080))

    th_timer = Timer(init_time)
    th_timer.start()
    try:
        th_timer.wait()
        while True:
            r_query = clientSocket.recvfrom(1024)
            data = DHCP_decode(r_query)
            if data['XID'] == ID and data['CH_ADDR'] == MAC_ADDR and data['OP'] == 2 and \
                    data['M_TYPE'] == 'ACK':
                return data
    except TimeoutError:
        return None


def start_client():
    ID = create_id()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as clientSocket:
            clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            clientSocket.bind(('0.0.0.0', 9090))

            while True:
                data = discover(clientSocket, ID)
                if data is None:
                    continue

                data = request(clientSocket, ID, data['YI_ADDR'], data['SI_ADDR'], 10)
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
