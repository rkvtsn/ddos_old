#!/usr/bin/python
import sys, time, os
from multiprocessing import Process, Queue
from sklearn.externals import joblib
from sklearn.tree import DecisionTreeClassifier

from sock import Sock

CONFIG = {
    "port_in": 6347,
    "port_out": 6350,
    "ip_in": "127.0.0.1",
    "ip_out": "127.0.0.1",
}

ATTACK_THRESHOLD = 2

sock = Sock(CONFIG)

model = joblib.load("models/100decisionTreeALL.pkl")

attack_count = 0

# listening socket
def process_socket(q):
    r = sock.socket_r()
    while True:
        pkg = sock.get_package(r)
        q.put(pkg)


# make predict by data
def process_data(q):
    s = sock.socket_s()
    global attack_count
    while True:
        pkg = q.get()
        data = [int(x) for x in pkg.split(",")]
        pred = model.predict([data[1:]])
        
        print pkg, pred
        print "attacks in row", attack_count

        if pred[0] != 'BENIGN':
            attack_count += 1
            if attack_count > ATTACK_THRESHOLD:
                s.send(str(data[0]))
        else:
            attack_count = 0

def main():
    q1 = Queue()
    try:
        p_socket = Process(target=process_socket, args=(q1,))
        p_data = Process(target=process_data, args=(q1,))

        p_data.start()
        p_socket.start()

        while True:
            time.sleep(3600)

    except KeyboardInterrupt:
        print ("Caught KeyboardInterrupt, terminating workers")
        p_socket.terminate()
        p_data.terminate()


if __name__ == "__main__":
    main()

