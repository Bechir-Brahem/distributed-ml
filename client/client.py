import os
import pathlib
import pickle
import shutil
import socket

import tqdm

from utility.Task import Task

HOST = "localhost"  # The server's hostname or IP address
PORT = 65432  # The port used by the server
BUFFER_SIZE = 4096

received_files = []


def recv_file(s, task):
    """
    receives file and writes it with exact attention to the number of bytes read
    :param s: socket
    :param task: Task class instance
    """
    progress = tqdm.tqdm(range(task.filesize), f"Receiving {task.filename}", unit="B", unit_scale=True,
                         unit_divisor=1024)
    tmp_size = task.filesize
    buffer = BUFFER_SIZE
    done = False
    count = 0
    with open(task.filepath, "wb") as f:
        while tmp_size > 0:
            if tmp_size < BUFFER_SIZE:
                buffer = tmp_size
                done = True
            bytes_read = s.recv(buffer)
            count += buffer
            f.write(bytes_read)
            progress.update(len(bytes_read))
            if done:
                break

            tmp_size -= buffer


def recv_input_file(s, datapath):
    task_length_bytes = s.recv(1024)
    task_length = int.from_bytes(task_length_bytes, byteorder='little')
    print('[x] task length received:', task_length)

    data = s.recv(task_length)
    task: Task = pickle.loads(data)
    task.filepath = os.path.join(datapath, task.filename)
    received_files.append(task)
    print('[x] task received')

    recv_file(s, task)
    print(f'[x] file {task.filename} received')


def main():
    # creating directory data
    datapath = pathlib.Path(__file__).parent.joinpath('data').resolve()
    try:
        shutil.rmtree(datapath)
    except FileNotFoundError:
        pass
    os.mkdir(datapath)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        recv_input_file(s, datapath)
        recv_input_file(s, datapath)


if __name__ == '__main__':
    main()
