"""
transfer two files from server to client using TCP sockets
"""
import os.path
import pathlib
import pickle
import socket

import tqdm

from utility.Task import Task

HOST = "localhost"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)
BUFFER_SIZE = 4096


def send_file(filename, conn):
    filesize = os.path.getsize(filename)
    progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
    with open(filename, "rb") as f:
        while True:
            bytes_read = f.read(BUFFER_SIZE)
            if not bytes_read:
                # file transmitting is done
                break
            conn.sendall(bytes_read)
            # update the progress bar
            progress.update(len(bytes_read))

    # TODO: checksum verification


def send_input_file(conn, input_type, filename=None):
    """
    sends input_file such as X.npy data values and y.npy their respective label

    if filename not given will request the user for one

    uses Task class to store important information about the files such as filename and filesize

    protocol:
    - sends length of task instance in bytes in fixed length of 1024
    - sends task instance serialized
    - sends file contents using send_file()
    :param conn: connection from the socket
    :param input_type: 'X' or 'Y'
    """
    # check if filename is given from the arguments
    if not filename:
        file = ''
        filename = ''
        while not os.path.isfile(file):
            # filename = input('enter the filename: ')
            filename = 'X.npy'
            file = pathlib.Path(__file__).parent.joinpath(filename).resolve()
    else:
        file = pathlib.Path(__file__).parent.joinpath(filename).resolve()

    # create Task instance
    task = Task(input_type, filename, os.path.getsize(file))
    # serialize task
    pickled_task = pickle.dumps(task)

    # convert task length to bytes of fixed size 1024
    # the fixed size is necessary when receiving the data

    task_length = len(pickled_task)
    task_length_fixed_bytes = task_length.to_bytes(byteorder='little', length=1024)

    # print("bytes",task_length_fixed_bytes)
    conn.sendall(task_length_fixed_bytes)
    print('[x] task length sent:', task_length)
    conn.sendall(pickled_task)
    print('[x] serialized task sent')
    send_file(file, conn)
    print('[x] file sent', task.filename)
    #


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # dev environment only
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        s.bind((HOST, PORT))
        s.listen()
        print(f"[*] Listening as {HOST}:{PORT}")
        conn, addr = s.accept()
        print(f"[x] {addr} is connected.")

        with conn:
            send_input_file(conn, 'X', 'X.npy')
            send_input_file(conn, 'Y', 'y.npy')


if __name__ == '__main__':
    main()
