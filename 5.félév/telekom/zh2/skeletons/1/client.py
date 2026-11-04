import socket
import struct
import sys


def recv_exact(sock, size):
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:              # a másik oldal lezárta a kapcsolatot
            return b""
        data += chunk
    return data


server_address = (sys.argv[1], int(sys.argv[2]))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    values = ("...".encode(), "...".encode(), "...".encode())
    packer = struct.Struct('...')
    packed_data = packer.pack(*values)

    client.connect(server_address)
    client.sendall(packed_data)

    answer_from_server_packer = struct.Struct('...')
    a, b = answer_from_server_packer.unpack(
        # client.recv(answer_from_server_packer.size)
        recv_exact(client, answer_from_server_packer.size)
    )

    a = a.strip(b'\x00').decode()

