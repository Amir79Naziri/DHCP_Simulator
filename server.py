import socket
import threading
import dhcp_protocol
from ip_pool import Pool


def start_server():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as serverSocket:
            serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            address = (socket.gethostbyname(socket.gethostname()), 8080)
            serverSocket.bind(address)

            pool = Pool()
            print('Server started...')

            while True:
                data, addr = serverSocket.recvfrom(1024)
                print(data)
                print(addr)
                serverSocket.sendto(b'OK', ('<broadcast>', 9090))

    except ConnectionError as msg:
        print(msg)
    except IOError as msg:
        print(msg)


if __name__ == '__main__':
    start_server()
