#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, time, os, datetime, json
from multiprocessing import Process, Queue

from tinterval import TimeInterval
from firewall import Firewall
from sock import Sock

import config



sock = Sock({
    "port_in": config.config['firewall']['port'],
    "ip_in": config.config['firewall']['ip'],
})

firewall = Firewall()

# looking for dead rules by life_time in DB
def process_warden():
    
    # update tables by life_time
    fw = Firewall()
    removed = fw.refresh()

    if len(removed) > 0:
        print removed
    
    fw.close_connection()


# listening socket
def process_socket(q):
    r = sock.socket_r()
    while True:
        pkg = sock.get_package(r)
        data = json.loads(pkg)
        q.put(data)




# make decision by data
def process_data(q):
    while True:
        data = q.get()
        #data = [
        #    { 't': 'range', 'ip': '1.1.1.1', 'bad_ports': [1, 4],  'good_ports': [1,2,3], 'timeout': 1, 'is_inner': True },   # close ports range on IP address
        #    { 't': 'list', 'ip': '1.2.1.1', 'bad_ports': [1, 3, 4], 'good_ports': [3,4,5], 'timeout': 3, 'is_inner': False }, # close ports list on IP address
        #    { 't': None, 'ip': '1.2.1.1', 'bad_ports': [1, 3, 4], 'good_ports': [3,4,5], 'timeout': 5, 'is_inner': False },   # close IP address
        #]
        for d in data:
            firewall.block(**d)


def main():
    q1 = Queue()
    try:

        warden = TimeInterval(config.timeout, process_warden)
        warden.start()

        p_socket = Process(target=process_socket, args=(q1,))
        p_data = Process(target=process_data, args=(q1,))

        p_data.start()
        p_socket.start()
        
        while True:
            time.sleep(3600)

    except KeyboardInterrupt:
        print "Caught KeyboardInterrupt, terminating"
        warden.stop()
        p_socket.terminate()
        p_data.terminate()
        

if __name__ == "__main__":
    main()