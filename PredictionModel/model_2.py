#!/usr/bin/python
import sys
import time
import os
import zmq
import zlib
import json
from multiprocessing import Process, Queue
import psycopg2
from storage import get_data

COLLECTOR_PORT_IN = 6346
COLLECTOR_PORT_OUT = 6347
SERVICE_IP = "127.0.0.1"

_username = 'postgres'
_password = '123456'
_hostname = 'localhost'
_database = 'traffic'

conn = psycopg2.connect(host=_hostname, user=_username, password=_password, database=_database)

model = None # TODO


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


def receive_package(r):
    pkg = json.loads(zlib.decompress(r.recv()))
    return pkg


def hard_work(d):
    data = get_data(conn, d['t1'], d['t2']) #, d['nf_group_type']
    pred = model.predict()
    #pred = MODELS[d['nf_group_type']].predict(data)
    return pred


def process_model(q):
    s = get_socket_s()
    while True:
        pkg = q.get()
        result = hard_work(pkg)
        s.send(result)

def process_socket(q):
    r = get_socket_r()
    while True:
        pkg = receive_package(r)
        q.put(pkg)
        



def main():

    q1 = Queue()
    try:
        p_socket = Process(target=process_socket, args=(q1,))
        p_model = Process(target=process_model, args=(q1,))
        
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

