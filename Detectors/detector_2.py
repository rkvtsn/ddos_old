#!/usr/bin/python
import sys, time, os
from multiprocessing import Process, Queue

from decision_maker import DecisionMaker
from storage import Storage
from sock import Sock

CONFIG = {
    "port_in": 6350,
    "port_out": 6341,
    "ip_in": "127.0.0.1",
    "ip_out": "127.0.0.1",

    "username": 'postgres',
    "password": '123456',
    "hostname": 'localhost',
    "database": 'traffic',
}

decision_maker = DecisionMaker(CONFIG)
sock = Sock(CONFIG)

# listening socket
def process_socket(q):
    r = sock.socket_r()
    while True:
        pkg = sock.get_package(r)
        print pkg
        q.put(pkg)


# make decision by data
def process_data(q):
    #s = sock.socket_s()
    while True:
        pkg = q.get()
        decision = decision_maker.make(timestamp=int(pkg))
        print decision
        #s.send(decision)
        #print "decision: "
        #print decision


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
        decision_maker.end()


if __name__ == "__main__":
    main()