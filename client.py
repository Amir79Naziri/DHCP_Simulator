import socket
import dhcp


def start_client():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as clientSocket:
        try:
            ID = dhcp.create_id()
            clientSocket.bind(('', 68))
            clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)


            clientSocket.settimeout(5)
            clientSocket.sendto(dhcp.DHCP_discover_encode(ID), ('127.0.0.1', 8080))

            data = clientSocket.recvfrom(1024)
            offer = dhcp.DHCP_offer_decode(data, ID)


        except socket.timeout as msg:
            print(msg)
        except ConnectionError as msg:
            print(msg)
        except IOError as msg:
            print(msg)


if __name__ == '__main__':
    start_client()
