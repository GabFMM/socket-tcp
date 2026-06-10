from __future__ import annotations

from common.constants import CHUNK_SIZE

import struct
import hashlib

def recv_all(conn, size: int) -> bytes | None:
    data = b""

    while len(data) < size:
        packet = conn.recv(size - len(data))

        if not packet:
            return None

        data += packet

    return data

def unpack(conn) -> tuple[int, bytes] | None:
    opcode_bytes = recv_all(conn, 1)
    if opcode_bytes is None:
        return None

    size_bytes = recv_all(conn, 4)
    if size_bytes is None:
        return None

    opcode = struct.unpack("!B", opcode_bytes)[0]
    size = struct.unpack("!I", size_bytes)[0]

    data = recv_all(conn, size)
    if data is None:
        return None
    
    return (opcode, data)

def pack(opcode: int, data: bytes) -> bytes:
    return struct.pack("!BI", opcode, len(data)) + data

def calcSHA(filePath: str) -> hashlib._Hash:
    sha = hashlib.sha256()
    with open(filePath, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break

            sha.update(chunk)

    return sha