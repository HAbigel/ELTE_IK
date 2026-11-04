import sys
import socket
import select
import struct

proxy_address = ("localhost", int(sys.argv[1]))
server_address = ("localhost", int(sys.argv[2]))

client_packer = struct.Struct("...")
server_packer = struct.Struct("...")


def recv_exact(sock, size):
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            return None
        data += chunk
    return data


def proxy():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp, \
        socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:

        tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp.bind(proxy_address)
        tcp.listen()

        inputs = [tcp, udp]
        pending = {}

        while True:
            readables, _, _ = select.select(inputs, [], [])
            for s in readables:
                if s is tcp:
                    client, addr = tcp.accept()
                    inputs.append(client)
                elif s is udp:
                    data, addr = udp.recvfrom(4096)
                    # Match the response to its waiting TCP client.
                    client = pending.pop(addr, None)
                    if client:
                        client.sendall(data)
                else:
                    msg = recv_exact(s, client_packer.size)
                    if not msg:
                        inputs.remove(s)
                        s.close()
                        continue
                    a, b = client_packer.unpack(msg)
                    request = server_packer.pack(b"xx", 8)
                    # This example needs a unique request association.
                    udp.sendto(request, server_address)


if __name__ == "__main__":
    try:
        proxy()
    except KeyboardInterrupt:
        print("Proxy stopped")