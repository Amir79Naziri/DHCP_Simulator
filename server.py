import socket
from dhcp_protocol import DHCP_offer_encode, DHCP_ack_encode, DHCP_decode
from ip_pool import Pool

SERVER_IP = None
pool = None


def offer(serverSocket, ID, mac_addr, device_name):
    offered_ip = pool.offer_ip(mac_addr, device_name)
    print(offered_ip)
    s_query = DHCP_offer_encode(ID, offered_ip, SERVER_IP, pool.lease_time(), mac_addr)
    serverSocket.sendto(s_query, ('<broadcast>', 9090))


def ack(serverSocket, ID, mac_addr, device_name):
    allocated_ip = pool.allocate_ip(mac_addr, device_name)
    print(allocated_ip)
    s_query = DHCP_ack_encode(ID, allocated_ip, SERVER_IP, pool.lease_time(), mac_addr)
    serverSocket.sendto(s_query, ('<broadcast>', 9090))


def start_server():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as serverSocket:
            serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            address = (SERVER_IP, 8080)
            serverSocket.bind(address)

            print('Server started...')

            while True:
                r_query, _ = serverSocket.recvfrom(1024)
                data = DHCP_decode(r_query)
                if data['OP'] == 1 and data['M_TYPE'] == 'DISCOVER':
                    pass
                elif data['OP'] == 1 and data['M_TYPE'] == 'REQUEST':
                    pass


    except ConnectionError as msg:
        print(msg)
    except IOError as msg:
        print(msg)


if __name__ == '__main__':
    SERVER_IP = socket.gethostbyname(socket.gethostname())
    pool = Pool()
    start_server()
