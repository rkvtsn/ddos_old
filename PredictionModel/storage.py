import pandas as pd
from pandas.io import sql
import psycopg2
import base64
import numpy as np
import struct
from socket import inet_ntoa

SIZE_OF_HEADER = 24
SIZE_OF_RECORD = 48

PROTOCOL = { 1: "ICMP", 6: "TCP", 14: "Telnet", 17: "UDP" }

def get_upair_group(flow, t=None):
    if t == None or t == "all":
        return "all"
    s = ""
    for x in t.split('_'):
        if 'd' in x:
            s += "_"
        s += flow[x[0] + "addr"]
        if 'p' in x: 
            s += ":" + str(flow[x[0] + "port"])
    return s


def nfdata_new():
    nfdata = {}
    
    nfdata['flow_count'] = 0
    nfdata['pcount'] = 0
    nfdata['bcount'] = 0
    nfdata['upairs'] = set()
    nfdata['protocol'] = { 'TCP': 0, 'ICMP': 0, 'Telnet': 0, 'UDP': 0 }
    
    return nfdata
    

def nfdata_add(nfdata, flow):
    
    nfdata['pcount'] += flow['pcount']
    nfdata['bcount'] += flow['bcount']
    
    nfdata['upairs'] = nfdata['upairs'].union(flow['upairs'])
    
    nfdata['flow_count'] += 1
    
    for p in flow['protocol']:
        nfdata['protocol'][p] += flow['protocol'][p]
    
    return nfdata
    

    

def select(conn, t1=None, t2=None):
    limit = ""
    if t1 != None and t2 != None:
        limit = "WHERE time > %s AND time < %s" % (t1, t2)
    elif t1 != None:
        limit = "WHERE time == %s" % t1
    
    sqlquery = "SELECT * FROM flows " + limit
    data = sql.read_sql(sqlquery, conn, index_col='id')
    return data


def get_data(conn, t1=None, t2=None, nf_group_type=None):
    data = select(conn, t1, t2)
    result = { }
    for i in range(len(data)):
        nfc_group = { }
        
        #X-threads:
        for j in range(len(data.iloc[i]["data"])):
            
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
                    flow['saddr'] = inet_ntoa(buf[offset + 0:offset + 4])
                    flow['sport'] = d[4]

                    flow['daddr'] = inet_ntoa(buf[offset + 4:offset + 8])
                    flow['dport'] = d[5]

                    flow['pcount'] = d[0]
                    flow['bcount'] = d[1]

                    flow['protocol'] = { }
                    flow['protocol'][PROTOCOL[ord(buf[offset + 38])]] = 1

                    flow['upairs'] = set()
                    flow['upairs'].add((buf[offset + 0:offset + 4], d[4], buf[offset + 4:offset + 8], d[5]))
                    
                    s = get_upair_group(flow, nf_group_type)
                    if s not in nfc_group:
                        nfc_group[s] = nfdata_new()
                    nfc_group[s] = nfdata_add(nfc_group[s], flow)
        
        for k in nfc_group:
            nfc_group[k]['ucount'] = len(nfc_group[k]['upairs'])
            del nfc_group[k]['upairs']
        result[data.iloc[i]["time"]] = nfc_group
    return result