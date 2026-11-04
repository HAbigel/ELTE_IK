import socket
import struct
import select
import sys
import time

# server_address = (sys.argv[1], int(sys.argv[2]))
server_address = ('localhost', int(sys.argv[1]))
packer = struct.Struct('...')
answer_to_client_packer = struct.Struct('...')


def recv_exact(sock, size):
    """Addig olvas, amíg pontosan size byte meg nem érkezik (vagy a másik oldal bont)."""
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            return b""
        data += chunk
    return data


def select_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(server_address)
        server.listen()
        inputs = [server]
        while True:
            readables, _, _ = select.select(inputs, [], [], 1.0)
            for s in readables:
                if s is server:
                    client, client_addr = server.accept()
                    inputs.append(client)
                    continue
                time.sleep(1)
                msg = recv_exact(s, packer.size)
                if not msg:
                    s.close()
                    inputs.remove(s)
                    continue
                (a, b, c) = packer.unpack(msg)

                a = a.strip(b'\x00').decode()

                x = 2
                y = "..."

                s.sendall(answer_to_client_packer.pack(x))
                s.sendall(answer_to_client_packer.pack(y.encode()))


if __name__ == "__main__":
    select_server()
