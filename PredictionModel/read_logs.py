#@hello world
import pandas as pd
import numpy as np

import json
from operator import itemgetter

SEPARATOR = ', '
cur_dir = "D:\\Projects\\_python\\collector-js\\"



def load_data(fname):
    s = None
    with open(cur_dir + fname) as file:
        s = file.readline()
    s = s.strip(SEPARATOR)
    json_string = "[%s]" % s
    data = json.loads(json_string)
    return data


def sort_data_by(key="time"):
    result = sorted(data, key=itemgetter(key))
    return data


def prepare_data(data):
    for d in data:
        for p in d['packages'].iteritems():
            p['upairsCount'] = len(p['uniquePairs'])

    sort_data_by()
    return data

# Structure: 
# data[index]['property:interval|time|flows|packages']['packageName:%filter_type%|packages']['packageProperty:bytesCount|packetsCount']...
# data[1]['packages']['package']['uniquePairs']

def first_level(fname):
    raw_data = load_data(fname)
    data = pd.DataFrame(index=np.arange(0, len(raw_data)), columns=("Time", "Pack", "Bytes", "Pairs", "TCP", "ICMP", "Telnet", "UDP"))
    i = 0
    for d in raw_data:
        data.loc[i].Time = d['time']
        for _, p in d['packages'].iteritems():
            data.loc[i].Pairs = len(p['uniquePairs'])
            data.loc[i].Pack = p['packetsCount']
            data.loc[i].Bytes = p['bytesCount']
            for protocol_k, protocol_v in p['protocols'].iteritems():
                data.loc[i][protocol_k] = protocol_v
        i += 1

    return data

def resolve_dloc_path(dloc, path):
    hosts = path.split("_")
    src = hosts[0].split(":")
    dloc.SrcIP = src[0]
    
    if len(src) > 1:
        dloc.SrcPort = src[1]
    
    if len(hosts) > 1:
        dst = hosts[1].split(":")
        dloc.DstIP = dst[0]
        if len(dst) > 1:
            dloc.DstPort = dst[1]

def second_level(fname):
    raw_data = load_data(fname)
    data = pd.DataFrame(index=np.arange(0, len(raw_data)), columns=("Time", "SrcIP", "SrcPort", "DstIP", "DstPort", "Pack", "Bytes", "Pairs", "TCP", "ICMP", "Telnet", "UDP"))
    i = 0
    for d in raw_data:
        for path, p in d['packages'].iteritems():
            data.loc[i].Time = d['time']
            resolve_dloc_path(data.loc[i], path)
            data.loc[i].Pairs = len(p['uniquePairs'])
            data.loc[i].Pack = p['packetsCount']
            data.loc[i].Bytes = p['bytesCount']
            for protocol_k, protocol_v in p['protocols'].iteritems():
                data.loc[i][protocol_k] = protocol_v
            i += 1
    return data

def save_to(data, fname):
    data.to_csv(fname, sep=' ')
