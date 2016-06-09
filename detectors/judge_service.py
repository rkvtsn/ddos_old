#!/usr/bin/python
import sys, time, os
from multiprocessing import Process, Queue
import json


from sock import Sock

from config import config


sock = Sock({
    "port_in": config['judge_service']['port'],
    "port_out": config['firewall']['port'],
    "ip_in": config['judge_service']['ip'],
    "ip_out": config['firewall']['ip']
})


def process_socket(q):
    
    r = sock.socket_r()

    while True:
        pkg = sock.get_package(r)
        q.put(pkg)


def judge(data):

    result = []

    # TODO:
    for d in data:
        #only IP
        result.append({ 't': None, 'ip': d, 'bad_ports': [], 'good_ports': [], 'timeout': 5, 'is_inner': True })
    
    return result


def process_data(q):
    
    s = sock.socket_s()
    
    while True:
        pkg = q.get()
        data = json.loads(pkg) # get decision: list of tuple(ip, port) # TODO: now only IP
        judgment = judge(data) # judge them
        s.send(judgment) # send judgment to firewall


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
