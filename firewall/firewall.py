#!/usr/bin/python
import sys
import os
import subprocess
import sqlite3
from datetime import datetime as dt
from datetime import timedelta
from tinterval import TimeInterval

import config


if not os.getuid() == 0:
    print "You must be root to work with firewall."
    sys.exit(2)


'''
  TABLE FIELDS
  @rule_str
  @life_time
'''


class Firewall(object):

    def __init__(self):

        self._conn = sqlite3.connect(config.db_path)
        self._c = self._conn.cursor()

    
    def close_connection(self):

        self._conn.close()


    def _add_rule(self, rule, life_time):
        
        t = dt.now()
        params = (rule, life_time)
        self._c.execute("INSERT INTO rules VALUES (?, ?)", params)


    def refresh(self):

        #select dead rules
        t = dt.now()
        params = (t, )
        r = self._c.execute('SELECT * FROM rules WHERE life_time < ?', params)

        rules = r.fetchall()

        for rule in rules:
            #delete from 'iptables'
            result = subprocess.call('iptables -D INPUT ' + rule[1], shell=True)
            
            # smth wrong!
            if result != 0:
                print "Error with rule: ", rule
                continue
            #drop from 'DB'
            id = (rule[0], )
            self._c.execute('DELETE * FROM rules WHERE id = ?', id)
        
        #TODO:
        min_life_time = config.timeout
        
        #TODO: If Count of rules is equal 0 rise Timeout by the TOP from SELECT:
        if len(rules) == 0:
            self._c.execute('SELECT life_time FROM rules LIMIT 1')
        
            
                
    '''
    type: type of bad_ports, in ('list', 'range', None)
        list -> block by each
        range -> block inline
        None -> block only IP
    ip: source IP address
    bad_ports: ports to be blocked
    good_ports: ports to be allowed
    '''
    def block(self, ip, t, bad_ports, good_ports, timeout, is_inner):
        
        #prepare rule template
        rule = " -s " + ip

        #set -j param
        j = " -j REJECT" if is_inner else " -j DROP"

        #make `life_time` for rule
        life_time = dt.now() + timedelta(minutes=timeout)

        if t == "list":
            # iptables has limit for ports (15 items) -> split it on chunks by 15
            drop_rules = self._rules_batch_ports(rule, bad_ports)
            for r in drop_rules:
                rule_str = r + j
                subprocess.call('iptables -A INPUT ' + rule_str, shell=True)
                self._add_rule(rule_str, life_time)

        elif t == "range":
            rule_str = rule + ' --sport %d:%d' % (bad_ports[0], bad_ports[1]) + j
            subprocess.call('iptables -A INPUT ' + rule_str, shell=True)
            self._add_rule(rule_str, life_time)

        else:
            rule_str = rule + j
            subprocess.call('iptables -A INPUT ' + rule_str, shell=True)
            self._add_rule(rule_str, life_time)

        # insert ALLOWED ports on IP
        access_rules = self._rules_batch_ports(rule, good_ports)
        for r in access_rules:
            rule_str = r + " -j ACCESS"
            subprocess.call('iptables -I INPUT 1 ' + rule_str, shell=True)
            self._add_rule(rule_str, life_time)


    def _rules_batch_ports(self, r, ports):
        
        rules = []
        rule = r
        if ports is not None and len(ports) > 0:
            rule += " -p tcp -m multiport --sports "
            for i in xrange(int(ceil(len(ports)/float(15)))):
                rules.append(rule + ','.join(ports[i*15:(i+1)*15]))                
        
        return rules
    




