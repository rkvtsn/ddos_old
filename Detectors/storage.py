#!/usr/bin/python
# -*- coding: utf-8 -*-
import pandas as pd
from pandas.io import sql
import psycopg2
import base64
import numpy as np
import struct
from socket import inet_ntoa
import datetime
import pickle

SIZE_OF_HEADER = 24
SIZE_OF_RECORD = 48

PROTOCOL = { 1: "ICMP", 6: "TCP", 14: "Telnet", 17: "UDP" }


class Storage():
    def __init__(self, config):
        self.conn = psycopg2.connect(host=config["hostname"], 
                                    user=config["username"], 
                                    password=config["password"], 
                                    database=config["database"])
        self.ipassoc = self.get_iptable()

    def close(self):
        self.conn.close()


    def get_iptable(self):
        
        ipassoc = []
        with open('ip.dat', 'rd') as f:
            ipassoc = pickle.load(f)

        return ipassoc
    
    def check_ip(self, ip):
        
        a = ip
        inlist = False
        for i in xrange(len(self.ipassoc)):
            if ip == self.ipassoc[i][0]:
                a = self.ipassoc[i][1]
                inlist = True
        
        if inlist == False:
            for i in xrange(len(self.ipassoc)):
                if ip == self.ipassoc[i][1]:                
                    inlist = True        

        if inlist == False:
            a = '0'

        return a

    def get_upair_group(self, flow, t=None):
        if t is None or t == "all":
            return "all"
        s = ""
        for x in t.split('_'):
            if 'd' in x:
                s += "_"
            s += flow[x[0] + "addr"]
            if 'p' in x: 
                s += ":" + str(flow[x[0] + "port"])
        return s


    def nfdata_new(self):
        nfdata = {}
    
        nfdata['flow_count'] = 0
        nfdata['pcount'] = 0
        nfdata['bcount'] = 0
        nfdata['upairs'] = set()
        nfdata['protocol'] = { 'TCP': 0, 'ICMP': 0, 'Telnet': 0, 'UDP': 0 }
    
        return nfdata
    

    def nfdata_add(self, nfdata, flow):
    
        nfdata['pcount'] += flow['pcount']
        nfdata['bcount'] += flow['bcount']
    
        nfdata['upairs'] = nfdata['upairs'].union(flow['upairs'])
    
        nfdata['flow_count'] += 1
    
        for p in flow['protocol']:
            nfdata['protocol'][p] += flow['protocol'][p]
    
        return nfdata
    

    def get_src_by_predict(self, data, pred):
        src_list = set()
        for i in xrange(len(pred)):
            if pred[i] != "BENIGN":
                src_list.add(data.iloc[i].src)
        return src_list


    def select(self, t1=None, limit=None):
        lim = ""
        if t1 is not None:
            lim += " WHERE time <= '%s' ORDER BY time DESC " % (datetime.datetime.fromtimestamp(t1 / 1000.0))
        if limit is not None:
            lim += " LIMIT %s" % limit
            
        sqlquery = "SELECT * FROM flows " + lim
        data = sql.read_sql(sqlquery, self.conn, index_col='id')
        return data
        

    def filter_data(self, data, nf_group_type=None, malware_tables=None):
        result = []
        for i in xrange(len(data)):
            nfc_group = { }
            
            #X-threads:
            for j in xrange(len(data.iloc[i]["data"])):
            
                #1-thread:
                s_buf = data.iloc[i]["data"][j]
                if s_buf == "": 
                    continue
                buf = s_buf.decode('base64')
                flow_count = struct.unpack('B', buf[3:4])[0]
            
                for index in xrange(flow_count):
                    offset = SIZE_OF_HEADER + (index * SIZE_OF_RECORD)
                    flow = { }
                
                    if len(buf) - offset > 47:
                        d = struct.unpack('!IIIIHH',buf[offset + 16:offset + 36])
                        flow['saddr'] = self.check_ip(inet_ntoa(buf[offset + 0:offset + 4]))
                        flow['sport'] = d[4]

                        flow['daddr'] = self.check_ip(inet_ntoa(buf[offset + 4:offset + 8]))
                        flow['dport'] = d[5]
                        
                        upair = self.get_upair_group(flow, nf_group_type)

                        if malware_tables is not None:
                            t_src, t_dst = malware_tables
                            address = upair.split('_')
                            if address[0] not in t_src and address[1] not in t_dst:
                                continue
                        
                        if int(flow['sport']) == 22 or int(flow['dport']) == 22 or int(flow['sport']) == 0 or int(flow['dport']) == 0 or flow['saddr'] == '0' or flow['daddr'] == '0':
                            continue

                        flow['pcount'] = d[0]
                        flow['bcount'] = d[1]
                        
                        flow['protocol'] = { }
                        flow['protocol'][PROTOCOL[ord(buf[offset + 38])]] = 1
                    
                        flow['upairs'] = set()
                        
                        flow['upairs'].add((flow['saddr'], d[4], flow['daddr'], d[5]))
                        
                        flow['upairs'].add(upair)
                        if s not in nfc_group:
                            nfc_group[upair] = self.nfdata_new()
                        
                        nfc_group[upair] = self.nfdata_add(nfc_group[upair], flow)
        
            for k in nfc_group:
                nfc_group[k]['ucount'] = len(nfc_group[k]['upairs'])
                #del nfc_group[k]['upairs']
                nfc_group[k]['upairs'] = None
                ip = k.split('_')
                row = [data.iloc[i]['time']]
                row += ip
                row += [nfc_group[k]['ucount'], 
                       nfc_group[k]['pcount'], 
                       nfc_group[k]['bcount']]
                row += nfc_group[k]['protocol'].values()
                
                row += [data.iloc[i]['atk_desc']]
                row += [data.iloc[i]['atk_name']]
                result.append(row)
        
        columns = ['time','src','dst','ucount','pcount', 'bcount'] + self.nfdata_new()['protocol'].keys() + ['desc', 'target']
        if nf_group_type is None or nf_group_type == 'all':
            columns = ['time','-','ucount','pcount', 'bcount'] + self.nfdata_new()['protocol'].keys() + ['desc', 'target']
        if nf_group_type == 's':  
            columns = ['time','src','ucount','pcount', 'bcount'] + self.nfdata_new()['protocol'].keys() + ['desc', 'target'] 
        return pd.DataFrame(result, columns=columns)