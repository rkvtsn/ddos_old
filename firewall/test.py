#!/usr/bin/python
import json

from sock import Sock

sock = Sock({
    "port_out": 6350,
    "ip_out": "127.0.0.1",
})


def send_json(data):
    s = sock.socket_s()
    s.send(json.dumps(data))
    s.close()


if __name__ == "__main__":

    data = [
        { 't': 'range', 'ip': '1.1.1.1', 'bad_ports': [1, 4],  'good_ports': [1,2,3], 'timeout': 60 * 1, 'is_inner': True },   # close ports range on IP address
        { 't': 'list', 'ip': '1.2.1.1', 'bad_ports': [1, 3, 4], 'good_ports': [3,4,5], 'timeout': 60 * 3, 'is_inner': False }, # close ports list on IP address
        { 't': None, 'ip': '1.3.1.1', 'bad_ports': [1, 3, 4], 'good_ports': [3,4,5], 'timeout': 60 * 5, 'is_inner': False },   # close IP address
    ]
    
    send_json(data)

    print "Done!"
