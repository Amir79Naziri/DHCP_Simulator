import socket
from dhcp_protocol import DHCP_offer_encode, DHCP_ack_encode, DHCP_decode
from ip_pool import Pool
import time
from threading import Thread

pool = Pool()
PENDING_MACS = dict()


def timer():
    while True:
        time.sleep(1)
        for mac in PENDING_MACS.copy():
            new_time = PENDING_MACS[mac][0] - 1
            service = PENDING_MACS[mac][1]
            if new_time <= 0:
                if service == 'offered':
                    pool.reject_ip(mac)
                else:
                    pool.deallocate_ip(mac)
                del PENDING_MACS[mac]
            else:
                PENDING_MACS[mac] = (new_time, service)


def show_list():
    while True:
        if input() == 'ls':
            ls = PENDING_MACS.copy()
            pool.print_status(ls)


def offer(serverSocket, ID, mac_addr, device_name):
    offered_ip = pool.offer_ip(mac_addr, device_name)
    s_query = DHCP_offer_encode(ID, offered_ip, socket.gethostbyname(socket.gethostname()), pool.lease_time(), mac_addr)
    serverSocket.sendto(s_query, ('<broadcast>', 9090))


def ack(serverSocket, ID, mac_addr, device_name):
    allocated_ip = pool.allocate_ip(mac_addr, device_name)
    s_query = DHCP_ack_encode(ID, allocated_ip, socket.gethostbyname(socket.gethostname()), pool.lease_time(), mac_addr)
    serverSocket.sendto(s_query, ('<broadcast>', 9090))


def start_server():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as serverSocket:
            serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            address = ('', 8080)
            serverSocket.bind(address)

            print('Server started...')

            while True:
                r_query, _ = serverSocket.recvfrom(1024)
                data = DHCP_decode(r_query)
                if data['OP'] == 1 and data['M_TYPE'] == 'DISCOVER':
                    PENDING_MACS[data['CH_ADDR']] = (10, 'offered')
                    offer(serverSocket, data['XID'], data['CH_ADDR'], data['device_name'])

                elif data['OP'] == 1 and data['M_TYPE'] == 'REQUEST':
                    if data['CH_ADDR'] in PENDING_MACS:
                        PENDING_MACS[data['CH_ADDR']] = (pool.lease_time(), 'allocated')
                        ack(serverSocket, data['XID'], data['CH_ADDR'], data['device_name'])


    except ConnectionError as msg:
        print(msg)
    except IOError as msg:
        print(msg)


if __name__ == '__main__':
    Thread(target=timer).start()
    Thread(target=show_list).start()
    start_server()
