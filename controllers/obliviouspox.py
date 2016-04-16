#!/usr/bin/python
# Filename: obliviouspox.py

"""
    ObliviousRouting + POX.
"""

import os
usr_home = os.path.expanduser('~')

import sys
sys.path.append(usr_home + "/dhrpox/topology")
sys.path.append(usr_home + "/dhrpox/traffic")
sys.path.append(usr_home + "/dhrpox/routing")

import random
import logging
from struct import pack
from zlib import crc32
from copy import copy
from random import choice

from pox.core import core
from pox.lib.util import dpidToStr
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import EventMixin
from pox.lib.addresses import EthAddr
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.udp import udp
from pox.lib.packet.tcp import tcp
from pox.lib.recoco import Timer

from ripllib.mn import topos

from util import buildTopo

# my package
from switch import Switch

from readpath import *

# include as part of the betta branch
from pox.openflow.of_json import *

log = core.getLogger()
#log.setLevel(logging.WARNING)

# Number of switches
NUMSWITCH = 12

# Number of links
NUMLINK = 30

# Number of matrixs
NUMMATRIX = 288

# Number of bytes to send for packet_ins
MISS_SEND_LEN = 2000

PRIO_HIGH = 100
PRIO_LOW = 10

def sep():
    log.info("****************************************")

class DHRController(object):
    
  def __init__(self, t):
      self.switches = {}
      self.t = t # Master Topo object, passed in and never modified.

      self.routeTable = {}
      self.percentTable = {}
      self.macTable = {}
      self.packetTable = {}

      self.count = 0

      self.all_switches_up = False   #Sequences event handling.
      core.openflow.addListeners(self, priority=0)

  def _raw_dpids(self, arr):
      return [self.t.id_gen(name = a).dpid for a in arr]

  def _flood(self, event):

      packet = event.parsed
      dpid = event.dpid
      in_port = event.port
      t = self.t
		
      # sw is all the switches
      for sw in self._raw_dpids(t.switches()):
          ports = []
          sw_name = t.id_gen(dpid = sw).name_str()
          for host in t.down_hosts(sw_name):
              sw_port, host_port = t.port(sw_name, host)	
              if sw != dpid or (sw == dpid and in_port != sw_port):
                  ports.append(sw_port)
          for port in ports:
              self.switches[sw].send_packet_data(port, event.data)

  def _ecmp_hash(self, packet):

      '''
        Return an ECMP-style 5-tuple hash for TCP/IP packets, otherwise 0.
      '''

      hash_input = [0] * 5
      if isinstance(packet.next, ipv4):
          ip = packet.next
          hash_input[0] = ip.srcip.toUnsigned()
          hash_input[1] = ip.dstip.toUnsigned()
          hash_input[2] = ip.protocol
          if isinstance(ip.next, tcp) or isinstance(ip.next, udp):
              l4 = ip.next
              hash_input[3] = l4.srcport
              hash_input[4] = l4.dstport
              return crc32(pack('LLHHH', *hash_input))
      return 0 

  def _handle_PacketIn(self, event):

    if not self.all_switches_up:
        log.info("Saw PacKetIn %s before all switches were up \
                 -ignoring." % event.parsed)
        return
    else:
        packet = event.parse()
        dpid = event.dpid
        in_port = event.port
        t = self.t

        self.macTable[packet.src] = (dpid, in_port)
        if packet.dst.isMulticast():
            self._flood(event)

        else:
            
            # log.info("src  = %s" % packet.src)
            # log.info("dst  = %s" % packet.dst)
            self.macTable[packet.src] = (dpid, in_port)
            if packet.dst in self.macTable:
                out_dpid, final_out_port = self.macTable[packet.dst]
                if isinstance(packet.next, ipv4):
                    match = of.ofp_match.from_packet(packet)
                    # print match.__dict__
                    if match not in self.packetTable:
                        self.count += 1
                        log.info("%d" % self.count)
                        # log.info("%s %s %s %s" % (match._nw_src,match._nw_dst,match._tp_src,match._tp_dst))
                        self.packetTable[match] = 1
                    else:
                        self.packetTable[match] += 1
                        # log.info("here we handle a packet reactively")
                        log.info("%s" % packet)
                        log.info("the number %d" % self.packetTable[match])
                        #if self.packetTable[match] == 200:
                        #    self.packetTable[match] = 1
                        #else:
                        #    return
                    src = self.t.id_gen(dpid = event.dpid).sw
                    dst = self.t.id_gen(dpid = out_dpid).sw
                    if src == dst:
                        return
                    src_dst_pair = (src << 4) + dst
	            route = self._choose_path(self.routeTable[src_dst_pair], 
                                              self.percentTable[src_dst_pair])
            
                    log.info("route : %s" % route)
                    for i, node in enumerate(route):
                        node_dpid = self.t.id_gen(name = node).dpid
                        if i < len(route) - 1:
                            next_node = route[i + 1]
                            out_port, next_in_port = self.t.port(node,
                                                                 next_node)
                        else:
                            out_port = final_out_port
                        self.switches[node_dpid].install(out_port, match, priority = PRIO_HIGH)
                    self.switches[out_dpid].send_packet_data(final_out_port,
                                                             event.data)
                # else: for arp icmp use the basic path
                else:
                    # log.info("get a arp packet %s" % packet.__dict__)   
                    # Form OF match
                    match = of.ofp_match()
                    match.dl_src = packet.src
                    match.dl_dst = packet.dst
                    match.dl_type = packet.type
                    if match in self.packetTable:
                        # log.info("ARP has set path")
                        return
                    self.packetTable[match] = 1
                    src = self.t.id_gen(dpid = event.dpid).sw
                    dst = self.t.id_gen(dpid = out_dpid).sw
                    if src == dst:
                        return
                    src_dst_pair = (src << 4) + dst
	            route = self._choose_path(self.routeTable[src_dst_pair], 
                                              self.percentTable[src_dst_pair])
            
                    # log.info("route : %s" % route)
                    for i, node in enumerate(route):
                        node_dpid = self.t.id_gen(name = node).dpid
                        if i < len(route) - 1:
                            next_node = route[i + 1]
                            out_port, next_in_port = self.t.port(node,
                                                                 next_node)
                        else:
                            out_port = final_out_port
                        self.switches[node_dpid].install(out_port, match, priority = PRIO_LOW)
                    self.switches[out_dpid].send_packet_data(final_out_port,
                                                             event.data)
            else:
                self._flood(event)

  def _handle_FlowStatsReceived (self, event):
      stats = flow_stats_to_list(event.stats)
      log.debug("FlowStatsReceived from %s: %s", \
                dpidToStr(event.connection.dpid), stats)

      #log.info("flowstatsreceived")
      all_bytes = 0
      all_packet = 0
      all_flows = 0
      for f in event.stats:
          all_bytes += f.byte_count
          all_packet += f.packet_count
          if f.packet_count != 0:
              all_flows += 1
      if all_flows != 0:
          log.info("traffic from %s: %s bytes (%s packets)\
                   over %s flows", dpidToStr(event.connection.dpid),
                   all_bytes, all_packet, all_flows)

  def _choose_path(self, route_list, percent_list):
      while(True):
          for i in range(0, len(route_list)):
              if random.random() * 100 < percent_list[i]:
                  return route_list[i]

  def _install_explicit_path(self, src, dst, route, match):
      #log.info("route for %s %s: %s" % (src,dst,route))
      src_sw = self.t.up_switches(src)
      assert len(src_sw) == 1
      src_sw_name = src_sw[0]
      dst_sw = self.t.up_switches(dst)
      assert len(dst_sw) == 1
      dst_sw_name = dst_sw[0]

      final_out_port, ignore = self.t.port(route[-1],dst)

      for i, node in enumerate(route):
          node_dpid = self.t.id_gen(name = node).dpid

          if i < len(route) -1:
              next_node = route[i + 1]
              #log.info("node:%s, next_node:%s" % (node, next_node))
              out_port, next_in_port = self.t.port(node, next_node)
          else:
              out_port = final_out_port
          self.switches[node_dpid].install(out_port, match)

  def _save_paths(self):

      oblivious_path_file = usr_home + "/dhrpox/routing/path/oblivious_path.txt"
      oblivious_path = read_robust_path(oblivious_path_file, NUMSWITCH)

      for src in range(NUMSWITCH):
          for dst in range(NUMSWITCH):

              #save oblivious_path
              for p in oblivious_path[src][dst]:
                  route = []
                  path = oblivious_path[src][dst][p]['route']
                  percent = oblivious_path[src][dst][p]['percent']
                  for sw in path.split("-"):
                      route.append(sw + "_1")
                  
                  src_dst_pair = ((src + 1)<< 4) + dst + 1
                  if src_dst_pair not in self.routeTable:
                      # initialize the tables for the src id
                      self.routeTable[src_dst_pair] = []
                      self.percentTable[src_dst_pair] = []
                  self.routeTable[src_dst_pair].append(route)
                  self.percentTable[src_dst_pair].append(float(percent))

      log.info("all the paths have been saved in the routeTable")
      # next step is to put the route on the topology

      #self._install_paths()
      #log.info("all basic paths set")

  def _install_paths(self):

      for src in range(1, NUMSWITCH + 1):
          for dst in range(1, NUMSWITCH + 1):
              if src != dst:
                  src_dst_pair = (src << 4) + dst
                  ingress_router = str(src) + '_1'
                  egress_router = str(dst) + '_1'

                  # log.info("%d" % len(self.routeTable[src_dst_pair]))
                  if len(self.routeTable[src_dst_pair]) == 1:
                      route = self.routeTable[src_dst_pair][0]
                      for host_src in sorted (self.t.down_hosts(ingress_router)):
                          for host_dst in sorted (self.t.down_hosts(egress_router)):
                              log.info("route : %s" % route)

                              # Form OF match
                              match = of.ofp_match()
                              match.dl_src = EthAddr(self.t.id_gen(name = host_src).etha_str()).toRaw()
                              match.dl_dst = EthAddr(self.t.id_gen(name = host_dst).etha_str()).toRaw()
                              self._install_explicit_path(host_src, host_dst, route, match)

                  # install ICMP path:
                  #route = self.routeTable[src_dst_pair][0]
                  #for host_src in sorted (self.t.down_hosts(ingress_router)):
                  #    for host_dst in sorted (self.t.down_hosts(egress_router)):
                  #        log.info("route : %s" % route)

                          # Form OF match
                  #        match = of.ofp_match()
                  #        match.dl_src = EthAddr(self.t.id_gen(name = host_src).etha_str()).toRaw()
                  #        match.dl_dst = EthAddr(self.t.id_gen(name = host_dst).etha_str()).toRaw()
                  #        match.dl_type = 2048
                  #        match.nw_proto = 1
                  #        self._install_explicit_path(host_src, host_dst, route, match)
              #else:
              #    # for hosts in the same switch
              #    router = str(src) + '_1'
              #    node_dpid = self.t.id_gen(name = router).dpid
              #    for host_dst in sorted (self.t.down_hosts(router)):
              #        final_out_port, ignore = self.t.port(router, host_dst)
              #
              #    # Form OF match
              #    match = of.ofp_match()
              #    match.dl_dst = \
              #    EthAddr(self.t.id_gen(name = host_dst).etha_str()).toRaw()
              #    self.switches[node_dpid].install(final_out_port, match)

  def _handle_ConnectionUp (self, event):

      sw = self.switches.get(event.dpid)
      sw_str = dpidToStr(event.dpid)
      log.info("Saw switch com up: %s", sw_str)
      name_str = self.t.id_gen(dpid = event.dpid).name_str()

      if name_str not in self.t.switches():
          log.warn("Ignoring unknown switch %s" % sw_str)
          return

      if sw is None:
          log.info("Added fresh switch %s" % sw_str)
          sw = Switch()
          self.switches[event.dpid] = sw
          sw.connect(event.connection)

      else:
          log.info("Odd - already saw switch %s come up" % sw_str)
          sw.connect(event.connection)
      sw.connection.send(of.ofp_set_config(miss_send_len = MISS_SEND_LEN))
        
      if len(self.switches) == len(self.t.switches()):
          log.info("Woo! All switches up")
          self.all_switches_up = True

          self._save_paths()
          # log.info("self.routeTable : %s" % self.routeTable)
          self._install_paths()
          log.info("Woo! All paths ok")

def _timer_func():

    for connection in core.openflow._connections.values():
        connection.send(of.ofp_stats_request(\
                        body = of.ofp_flow_stats_request()))
        log.info("Sent %i flow stats requests", len(core.openflow._connections))
 
def launch(topo = None):

    if not topo:
        raise Exception("please specify topo and args on cmd line")
    else:
        t = buildTopo(topo,topos)

    core.registerNew(DHRController, t)

    # timer set to excute every ten seconds to get the feedback 
    # from the routers.
    # Timer(10, _timer_func, recurring = True)

    log.info("DHR-POX running with topo=%s." % topo)

