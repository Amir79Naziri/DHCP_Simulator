import socket
import threading
import dhcp_protocol


def client_handler(connection, data, address, ID):
    received_data = dhcp_protocol.DHCP_decode(data)  # receive Offer

    adr_msg = "Client-{} Address: ".format(ID) + str(address)

    print(data)
    print(adr_msg)

    try:
        connection.sendto(str.encode('done'), address)
    except ConnectionError as msg_:
        print(msg_)
        return
    except IOError as msg_:
        print(msg_)
        return


def start_server():
    counter = 1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as serverSocket:
            address = (socket.gethostbyname(socket.gethostname()), 67)
            serverSocket.bind(address)
            print('Server started\nwaiting for client ...')

            while True:
                data = serverSocket.recvfrom(1024)
                print('Client-{} accepted'.format(counter))
                threading.Thread(target=client_handler,
                                 args=(serverSocket, data[0], data[1], counter)).start()
                counter += 1

    except ConnectionError as msg:
        print(msg)
    except IOError as msg:
        print(msg)


if __name__ == '__main__':
    start_server()
