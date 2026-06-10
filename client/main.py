from common.constants import HOST, PORT, CHAT_OPCODE, FILE_OPCODE, FILE_NOT_EXISTS_OPCODE, SHA_OPCODE
import common.utils as utils

import socket
import tkinter as tk
from tkinter import messagebox
import threading
from pathlib import Path
import hashlib
import os

sock: socket.socket | None = None

def createFile(file: str, data: bytes):
    path = Path(f"client/{file}")
    filename = path.stem
    fileExtension = path.suffix

    num = 1
    new_path = path

    while new_path.is_file():
        num += 1
        new_path = path.with_name(f"{filename}({num}){fileExtension}")

    with open(new_path, "wb") as f:
        f.write(data)

    try:
        if isFileDataValid(file):
            os.remove(f"client/{filename}")
            messagebox.showerror("Erro", "Arquivo corrompido. Necessária retransferência")
        else:
            messagebox.showinfo("Sucesso", "Arquivo criado")

    except(OSError, ConnectionResetError):
        messagebox.showerror("Erro", "Comunicação com o servidor fechada")

def isFileDataValid(filename: str) -> bool:
    global sock
    if sock:
        sock.sendall(utils.pack(SHA_OPCODE, filename.encode()))

        packet = utils.unpack(sock)
        if packet is None:
            return False
        
        shaServer = packet[1]

        shaClient = utils.calcSHA(f"client/{filename}").digest()

        return shaClient != shaServer
    
    else:
        raise ConnectionResetError

def downloadArchive(filename: str):
    openConnection()

    global sock
    if filename and sock:
        try:
            sock.sendall(utils.pack(FILE_OPCODE, filename.encode()))

            packet = utils.unpack(sock)
            if packet is None:
                messagebox.showerror("Erro", "Comunicação com o servidor fechada")
                return
            
            opcode, data = packet

            if opcode == FILE_NOT_EXISTS_OPCODE:
                messagebox.showerror("Erro", "Arquivo inexistente. O formato aceito é nomeDoArquivo.ext")
            else:
                createFile(filename, data)

        except (OSError, ConnectionResetError):
            messagebox.showerror("Erro", "Comunicação com o servidor fechada")

def openConnection():
    global sock
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
    except Exception:
        showMenu(root)
        messagebox.showerror("Erro", "Servidor não está ligado ou funcionando")
        return

def closeConnection():
    global sock
    if sock:
        try:
            sock.close()
        except OSError:
            pass
        sock = None

def sendMessage(entry: tk.Entry):
    global sock

    if entry.get() and sock:
        try:
            sock.sendall(utils.pack(CHAT_OPCODE, entry.get().encode()))
            entry.delete(0, tk.END)
        except (OSError, ConnectionResetError):
            messagebox.showerror("Erro", "Comunicação com o servidor fechada")

def updateChat(message_variable: tk.StringVar):
    global sock

    while sock:
        try:
            packet = utils.unpack(sock)
            if not packet:
                break

            opcode = packet[0]
            data = packet[1]

            if opcode == CHAT_OPCODE:
                message_variable.set(message_variable.get() + "\n>> " + data.decode())
        
        except (OSError, ConnectionResetError):
            messagebox.showerror("Erro", "Comunicação com o servidor fechada")

def destroyAllWidgets(root: tk.Tk):
    for node in root.winfo_children():
        node.destroy()

def showChat(root: tk.Tk):
    destroyAllWidgets(root)

    openConnection()

    root.title("Chat")

    messageVariable = tk.StringVar()
    messageVariable.set(">> Você está conectado")

    message = tk.Message(root, textvariable=messageVariable, width=250, justify="left")
    message.configure(bg="gray")
    message.pack()

    thread = threading.Thread(target=updateChat, args=(messageVariable, ), daemon=True)
    thread.start()

    entry = tk.Entry(root)
    entry.pack()

    submit = tk.Button(root, text="Enviar", command=lambda: sendMessage(entry))
    submit.pack()

    button = tk.Button(root, text="Voltar ao menu", command=lambda: [closeConnection(), showMenu(root)])
    button.pack(pady=10)

def showDownloadArchive(root: tk.Tk):
    destroyAllWidgets(root)

    root.title("Baixar arquivo")

    tk.Label(root, text="Digite o nome do arquivo:").pack(pady=10)
    entry = tk.Entry(root)
    entry.pack()
    tk.Button(root, text="Baixar", command=lambda: downloadArchive(entry.get())).pack(pady=10)
    tk.Button(root, text="Voltar ao menu", command=lambda: [closeConnection(), showMenu(root)]).pack()

def showMenu(root: tk.Tk):
    destroyAllWidgets(root)

    root.title("Menu")

    title = tk.Label(root, text="Bem-vindo")
    title.pack(pady=50)

    chatButton = tk.Button(root, text="Entrar no chat", width=25, command=lambda: showChat(root))
    chatButton.pack(pady=10)

    arquivoButton = tk.Button(root, text="Baixar arquivo", width=25, command=lambda: showDownloadArchive(root))
    arquivoButton.pack(pady=10)

    sairButton = tk.Button(root, text="Sair", width=25, command=root.destroy)
    sairButton.pack(pady=10)

def on_closing():
    closeConnection()
    root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("300x500")

    root.protocol("WM_DELETE_WINDOW", on_closing)

    showMenu(root)
    root.mainloop()