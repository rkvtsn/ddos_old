#!/usr/bin/python
from __future__ import print_function
__author__ = 'SavR11'

import socket, sys, struct, time, signal
from Queue import Empty
from multiprocessing import Process, Queue

import os
import subprocess

from operator import itemgetter
from scipy.stats import randint

import numpy as np
from sklearn.tree import DecisionTreeClassifier

import pickle

def init_socket(port):
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
	except socket.error , msg:
		print('Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
		sys.exit()
	sock.bind(('', port))	
	return sock

def send_udp_message(ip,port,text):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
	sock.sendto(text, (ip, port))
	
def get_packege(sock):
	return sock.recvfrom(65535)	

def attack_type_socket_process(q):
	COLLECTOR_PORT = 6346
	sock = init_socket(COLLECTOR_PORT)
	while True:
		data, addr = get_packege(sock)	# receive from collector
		if (data[:7] == 'vec-1: '):	
			q.put((time.time(),data[7:].split()))	# parse and send data


def model_process(q):
	while True:
		packege_time, data = q.get() # here is data after parse
		with open('models/decisionTreeModelTest.pkl', 'rb') as f:
			dt1 = pickle.load(f)
		print(data[:4], dt1.predict([[data[1], data[2], data[3]],]), data[4])
		diff_time = time.time() * 1000000 - float(data[0])


		
def main():
	q1 = Queue()
	try:
		p_socket = Process(target=attack_type_socket_process, args=(q1,))
		p_model = Process(target=model_process, args=(q1,))
		
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
