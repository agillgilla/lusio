import socket
import sys

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
server_address = ('localhost', 65432)

print('Connecting to {} port {}'.format(*server_address))
sock.connect(server_address)

print('Connected!')

try:

    while True:
        # Send data
        message = input() + "\n"
        print('Sending: "' + message + '"')
        sock.sendall(message.encode())


        '''
        # Look for echo response
        amount_received = 0
        amount_expected = len(message)

        while amount_received < amount_expected:
            data = sock.recv(16)
            amount_received += len(data)
            print('Received {!r}'.format(data.decode()))
        '''
        
        

finally:
    print('Closing socket')
    sock.close()