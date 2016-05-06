#!/usr/bin/python
from __future__ import print_function
import sys, time, os, zmq, zlib, json
from multiprocessing import Process, Queue


COLLECTOR_PORT_IN = 6346
COLLECTOR_PORT_OUT = 6347
SERVICE_IP = "127.0.0.1"


def get_socket_r():
    try:
        context = zmq.Context()
        r = context.socket(zmq.PULL)
    except Exception as e:
        print('Socket "R" couldn\'t be created')
        sys.exit()
    r.bind("tcp://%s:%s" % (SERVICE_IP, COLLECTOR_PORT_OUT))
    return r

def get_socket_s():
    try:
        context = zmq.Context()
        s = context.socket(zmq.PUSH)
    except Exception as e:
        print('Socket "S" couldn\'t be created')
        sys.exit()
    s.connect("tcp://%s:%s" % (SERVICE_IP, COLLECTOR_PORT_IN))
    return s


def get_package(r):
    data = json.loads(zlib.decompress(r.recv()))
    print("Received request: ", data)
    return data

def recive_from_collector_process(q):
    r = get_socket_r()
    while True:
        data = get_package(r)
        q.put(data)

def predict(d):
    time.sleep(3) # SOME HARD WORK
    result = str(d['value']) + " finished!" # RESP
    return result

def predict_process(q):
    s = get_socket_s()
    while True:
        data = q.get()
        result = predict(data)
        s.send(result)
        
def main():
    q1 = Queue()
    try:
        p_socket = Process(target=recive_from_collector_process, args=(q1,))
        p_model = Process(target=predict_process, args=(q1,))
        
        p_model.start()
        p_socket.start()
        
        while True:
            time.sleep(3600)
            
    except KeyboardInterrupt:
        print ("Caught KeyboardInterrupt, terminating workers")
        p_socket.terminate()
        p_model.terminate()


if __name__ == "__main__":
    main()
