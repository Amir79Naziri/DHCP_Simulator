import socket
import threading


def client_handler(connection, message, address, ID):
    message = "Message from Client-{}: ".format(ID) + bytes.decode(message)
    adr_msg = "Client-{} Address: ".format(ID) + str(address)

    print(message)
    print(adr_msg)

    try:
        connection.sendto(str.encode('done'), address)
    except ConnectionError as msg_:
        print(msg_)
        return
    except IOError as msg_:
        print(msg_)
        return


def start_server(address=('127.0.0.1', 8080)):
    counter = 1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as serverSocket:

            serverSocket.bind(address)
            print('Server started')

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
