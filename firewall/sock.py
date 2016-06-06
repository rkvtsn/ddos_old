#!/usr/bin/python
import zmq, zlib, json


class Sock():
    def __init__(self, config):
        self.config = config

    def socket_r(self):
        try:
            context = zmq.Context()
            r = context.socket(zmq.PULL)
        except Exception as e:
            print('Socket "R" couldn\'t be created')
            sys.exit()
        r.bind("tcp://%s:%s" % (self.config['ip_in'], self.config['port_in']))
        return r

    def socket_s(self):
        try:
            context = zmq.Context()
            s = context.socket(zmq.PUSH)
        except Exception as e:
            print('Socket "S" couldn\'t be created')
            sys.exit()
        s.connect("tcp://%s:%s" % (self.config['ip_out'], self.config['port_out']))
        return s

    def unpack(self, d):
        return zlib.decompress(d)

    def get_package_u(self, r):
        data = json.loads((unpack(r.recv())))
        return data

    def get_package(self, r):
        data = r.recv()
        return data

    def pack(self, data):
        return data
