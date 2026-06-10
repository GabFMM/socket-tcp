from common.constants import HOST, PORT, CHAT_OPCODE, FILE_OPCODE, FILE_NOT_EXISTS_OPCODE, SHA_OPCODE
import common.utils as utils

import socket
import threading
from pathlib import Path
import os

conns = []
lock = threading.Lock()

def sendToConns(opcode: int, data: bytes) -> bool:
    with lock:
        clients = conns.copy()

    for c in clients:
        try:
            c.sendall(utils.pack(opcode, data))

        except (OSError, ConnectionResetError):
            with lock:
                if c in conns:
                    conns.remove(c)
            c.close()

            return False
        
    return True

def chat(data: bytes) -> bool:
    if not data:
        return False

    sendToConns(CHAT_OPCODE, data)

    return True

def trim(filename: str) -> str:
    return filename.strip()

def file(conn, data: bytes) -> bool:
    filename = data.decode()

    archive = Path("server/" + os.path.basename(filename))
    if not archive.is_file():
        conn.sendall(utils.pack(FILE_NOT_EXISTS_OPCODE, b""))
        return False
    
    with open(archive, "rb") as f:
        conn.sendall(utils.pack(FILE_OPCODE, f.read()))

    return True

def shaFile(conn, data: bytes):
    filename = data.decode()

    sha = utils.calcSHA(f"server/{filename}").digest()

    conn.sendall(utils.pack(SHA_OPCODE, sha))

def client_thread(conn):
    while True:
        try:
            packet = utils.unpack(conn)
            if packet is None:
                break

            opcode = packet[0]
            data = packet[1]

            if opcode == CHAT_OPCODE:
                if not chat(data):
                    break

            elif opcode == FILE_OPCODE:
                if not file(conn, data):
                    break

            elif opcode == SHA_OPCODE:
                shaFile(conn, data)

        except (OSError, ConnectionResetError):
            break

    with lock:
        if conn in conns:
            conns.remove(conn)
    conn.close()

if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, PORT))
        sock.listen(10)

        while True:
            conn, addr = sock.accept()

            with lock:
                conns.append(conn)

            threading.Thread(
                target=client_thread,
                args=(conn,),
                daemon=True
            ).start()