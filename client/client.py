import os
import pathlib
import pickle
import shutil
import socket
import time

import numpy as np
import tqdm

from utility.Task import Task

HOST = "localhost"  # The server's hostname or IP address
PORT = 65432  # The port used by the server
BUFFER_SIZE = 4096
input_filepath = None
label_filepath = None

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
    global input_filepath, label_filepath

    task_length = 0
    while task_length == 0:
        task_length_bytes = s.recv(1024)
        task_length = int.from_bytes(task_length_bytes, byteorder='little')
        print('[x] task length received:', task_length)
        if task_length == 0:
            time.sleep(1)

    data = s.recv(task_length)
    task: Task = pickle.loads(data)
    task.filepath = os.path.join(datapath, task.filename)
    received_files.append(task)
    print('[x] task received')

    recv_file(s, task)
    print(f'[x] file {task.filename} received')
    return task


def check_file(task):
    global input_filepath, label_filepath
    filepath = task.filepath
    if filepath is None:
        raise RuntimeError
    if os.path.isdir(filepath):
        raise IsADirectoryError
    if not os.path.isfile(filepath):
        raise RuntimeError
    if os.path.getsize(filepath) == 0:
        print('file empty:', filepath)
        raise RuntimeError
    if task.filetype == 'X':
        input_filepath = task.filepath
    elif task.filetype == 'Y':
        label_filepath = task.filepath


def train_model():
    from sklearn.linear_model import SGDClassifier
    with open(input_filepath, 'rb') as f:
        X = np.load(f, allow_pickle=True)
    print('[x] X file loaded length:', len(X))
    with open(label_filepath, 'rb') as f:
        y = np.load(f, allow_pickle=True)
    print('[x] y file loaded length:', len(y))

    sgd_clf = SGDClassifier(max_iter=1000, tol=1e-3, random_state=42)
    print('[x] SGDClassifier model chosen')
    sgd_clf.fit(X, y)
    print('[x] model training complete')
    return sgd_clf


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

        task1 = recv_input_file(s, datapath)
        check_file(task1)

        task2 = recv_input_file(s, datapath)
        check_file(task2)

        model = train_model()
        pickled_model = pickle.dumps(model)
        model_length = len(pickled_model)
        s.sendall(model_length.to_bytes(length=1024, byteorder='little'))
        print('[x] model length sent')
        s.sendall(pickled_model)
        print('[x] pickled model sent')
        print('[x] shutting down')


if __name__ == '__main__':
    main()
