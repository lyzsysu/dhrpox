#!/usr/bin/python
'''@package asymmetrictopo

Asymmetric topology creation and drawing.

'''

import sys
import os

from mininet.topo import Topo
from mininet.link import TCLink

class NodeID(object):
    '''Topo node identifier.'''

    def __init__(self, dpid = None):
        '''Init.

        @param dpid dpid
        '''
        # DPID-compatible hashable identifier: opaque 64-bit unsigned int
        self.dpid = dpid

    def __str__(self):
        return str(self.dpid)

    def name_str(self):
        return str(self.dpid)

    def ip_str(self):
        mid = (self.dpid & 0xff00) >> 8
        lo = self.dpid & 0xff
        return "10.0.%i.%i" % (mid,lo)
   
    def def_nopts(self):
        return {}

class AsymmetricTopo(Topo):

    NUMSWITCH = 0
    NUMLINK = 0
    
    class Node(NodeID):
    
        def __init__(self, sw = 0, host = 0, dpid = None, name = None):
            
            if dpid:
                self.sw = (dpid & 0xff00) >> 8
                self.host = (dpid & 0xff)
                self.dpid = dpid
            elif name:
                sw, host = [int(s) for s in name.split('_')]
                self.sw = sw
                self.host = host
                self.dpid = (sw << 8) + host
            else:
                self.sw = sw
                self.host = host
                self.dpid = (sw << 8) + host

        def __str__(self):
            return "(%i, %i)" % (self.sw, self.host)

        def name_str(self):
            return "%i_%i" % (self.sw, self.host)

        def mac_str(self):
            return "00:00:00:00:%02x:%02x" % (self.sw, self.host)

        def ip_str(self):
            return "10.0.%i.%i" % (self.sw, self.host)
        
        def etha_str(self):
            etha_str = ("0000%x%x" % (self.sw,self.host))
            etha = ""
            for i in range(0, 6):
                if ord(etha_str[i]) < 58:
                    etha = etha + chr(ord(etha_str[i]) - 48)
                else:
                    etha = etha + chr(ord(etha_str[i]) - 97 + 10)
            return etha

        def is_switch(self):
            name = self.name_str()
            if self.host == 1:
                return True
            return False

        def is_host(self):
            if self.is_switch():
                return False
            return True 

    def def_nopts(self, name = None):
        '''return default dict for my topo

        @param name name of node
        '''
        d = {}
        if name:
            id = self.id_gen(name = name)
            sw,host = [int(s) for s in name.split('_')]
            
            #host ==1 means it is switch,
            #for hosts only, set the IP
            if host != 1:
              d.update({'ip': id.ip_str()})
              d.update({'mac': id.mac_str()})
            d.update({'dpid': "%016x" % id.dpid})
        return d

    def down_hosts(self, name):
        nodes = [n for n in self.g[name] if self.id_gen(name = n).is_host()]
        #print nodes
        return nodes

    def up_switches(self, name):
        nodes = [n for n in self.g[name] if self.id_gen(name = n).is_switch()]
        return nodes

    def __init__( self, toponame = "abilene", NUMHOST = 2):
        
        Topo.__init__( self )
        
        self.id_gen = AsymmetricTopo.Node

        path = os.path.expanduser('~') + "/dhrpox/topology/" + toponame + ".txt"

        f = open(path)
        line = f.readline()
        link = {}
        switch = {}
        capacity = {}
        while line:
            if line.split(" ")[0] == "#": # this line is comment
                pass
            elif line.split(" ")[0] == "NUMSWITCH":
                NUMSWITCH = int(line.split(" ")[1])
            elif line.split(" ")[0] == "NUMLINK":
                NUMLINK = int(line.split(" ")[1])
            else:
                first = line.split(" ")[0]
                second = line.split(" ")[1]
                link_num = line.split(" ")[2]
                link[link_num] = (first, second)
                link_capacity = line.split(" ")[3]
                capacity[link_num] = int(link_capacity)
            line = f.readline()
        f.close()

        for e in range(1, NUMSWITCH + 1):
            sw_id = self.id_gen(e, 1).name_str()
            sw_opts = self.def_nopts(sw_id)
            self.add_switch(sw_id, **sw_opts)

            for h in range(2, 2 + NUMHOST):
                host_id = self.id_gen(e,h).name_str()
                host_opts = self.def_nopts(host_id)
                self.add_host(host_id, **host_opts)
                self.add_link(host_id, sw_id)
     
        for l in link:
            (first, second) = link[l]
            if first > second:
                continue
            self.add_link(str(first) + "_1", str(second) + "_1", bw = capacity[l])
