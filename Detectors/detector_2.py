#!/usr/bin/python
import sys, time, os
from multiprocessing import Process, Queue
import datetime
import json

from decision_maker import DecisionMaker
from storage import Storage
from sock import Sock

from config import config

decision_maker = DecisionMaker(config['database'])

sock = Sock({
    "port_in": config['detector_2']['port'],
    "port_out": config['judge_service']['port'],
    "ip_in": config['detector_2']['ip'],
    "ip_out": config['judge_service']['ip']
})

# listening socket
def process_socket(q):
    r = sock.socket_r()
    while True:
        pkg = sock.get_package(r)
        #print pkg
        time1 = datetime.datetime.now()
        print 'received', time1
        q.put((pkg, time1))


# make decision by data
def process_data(q):
    s = sock.socket_s()
    while True:
        pkg, time1 = q.get()
        decision = decision_maker.make(timestamp=int(pkg), depth=2)
        print decision
        time2 = datetime.datetime.now()
        print 'decision', time2
        time3 = (time2 - time1).total_seconds()
        print 'delta', time3
        s.send(json.dumps(decision))
        

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
