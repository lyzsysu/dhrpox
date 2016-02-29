"""
DynamicHybridRouting + POX.
First version is only proactively set all path on the abilene topology
next step is to calculate the dynamic part
"""

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

from util import buildTopo, getRouting

# add my packages
import sys
sys.path.append("/home/mininet/traffic")

from readtraffic import read_traffic

from basepox import Switch

# include as part of the betta branch
from pox.openflow.of_json import *

log = core.getLogger()
#log.setLevel(logging.WARNING)

# Number of switches
NUMSWITCH = 12

# Number of links
NUMLINK = 30

# Number of links
NUMMATRIX = 288

# Number of bytes to send for packet_ins
MISS_SEND_LEN = 2000

# global matrixs
(basic_tm, tm) = read_traffic("/home/mininet/traffic/2014_06_24TM")

def sep():
  log.info("****************************************")

class RipLController(object):
    
  def __init__(self, t):
    self.switches = {}
    self.t = t #Master Topo object, passed in and never modified.

    self.routeTable = {}
    self.percentTable = {}
    self.macTable = {}

    self.all_switches_up = False  #Sequences event handling.
    core.openflow.addListeners(self, priority=0)

  def _raw_dpids(self, arr):
    return [self.t.id_gen(name = a).dpid for a in arr]

  def _flood(self, event):
    packet = event.parsed
    dpid = event.dpid
    in_port = event.port
    t = self.t
		
    #sw is all the switches
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
    "Return an ECMP-style 5-tuple hash for TCP/IP packets, otherwise 0."
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
      log.info("Saw PacKetIn %s before all switches were up -ignoring." % event.parsed)
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
        # mode proactive use this code
        log.info("here we handle a packet_proactive")
        log.info("src  = %s" % packet.src)
        log.info("dst  = %s" % packet.dst)

  def _handle_FlowStatsReceived (self, event):
    stats = flow_stats_to_list(event.stats)
    log.debug("FlowStatsReceived from %s: %s", dpidToStr(event.connection.dpid), stats)

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
      log.info("traffic from %s: %s bytes (%s packets) over %s flows", dpidToStr(event.connection.dpid), all_bytes, all_packet, all_flows)

  def calculate_performance(self, num, selected_node_pairs):
    #calculate the performance after pick out the selected_pairs
    lm = defaultdict(lambda:defaultdict(lambda:None)) # link matrix
    lu = defaultdict(lambda:defaultdict(lambda:None)) # link utility
    for src in NUMSWITCH:
      for dst in NUMSWITCH:
        if src == dst or (src,dst) in selected_node_pairs:
          continue
        src_dst_pair = (src << 4) + dst
        routes = self.routeTable[src_dst_pair]
        percentages = self.percentTable[src_dst_pair]
        for j, node in enumerate(route):
          fst = self.t.id_gen(name = node).sw  # the first node of the link
          if j < len(route) - 1:
            next_node = route[j + 1]
            sec = self.t.id_gen(name = next_node).sw 
            # the second node of the link

            if tm[num][src * NUMSWITCH + dst] != 0:
              if fst not in lm or sec not in lm[fst]:
                lm[fst][sec] = 0.0
                lm[fst][sec] += tm[num][src * NUMSWITCH + dst] * percentage
    
    #calculate MLU
    MLU = 0
    for fst in range(1, NUMSWITCH + 1):
      for sec in range(1, NUMSWITCH + 1):
        if lm[fst][sec] is not None:
          lu[fst][sec] = lm[fst][sec] / capacity[fst][sec]
          if MLU < lu[fst][sec]:
            MLU = lu[fst][sec]
            most_Congested_link = (fst, sec)
    #calculate the Optimal Performance for the traffic matrix 
        
      
 
  def key_node_pairs_selection(self):
    pass

  def calculate_background_load(self, num, selected_node_pairs):
    pass

  def calculate_explicit_routing_for_selected_key_node_pairs(self):
    selected_node_pairs = self.key_node_pairs_selection()
    num = 0
    background_load = self.calculate_background_load(num, selected_node_pairs)
    explicit_route = ""
    return explicit_route

  def _choose_path(self, route_list, percent_list):
    while(True):
      for i in range(0, len(route_list)):
        if random.random() * 100 < percent_list[i]:
          return route_list[i]

  def _install_explicit_path(self, src, dst, route):
    #log.info("route for %s %s: %s" % (src,dst,route))
    src_sw = self.t.up_switches(src)
    assert len(src_sw) == 1
    src_sw_name = src_sw[0]
    dst_sw = self.t.up_switches(dst)
    assert len(dst_sw) == 1
    dst_sw_name = dst_sw[0]

    # Form OF match
    match = of.ofp_match()
    src_id = self.t.id_gen(name = src)
    src_etha = src_id.etha_str()
    dst_id = self.t.id_gen(name = dst)
    dst_etha = dst_id.etha_str()
    #log.info("src-etha : %s" % EthAddr(src_etha))
    #log.info("dst-etha : %s" % EthAddr(dst_etha))
    match.dl_src = EthAddr(src_etha).toRaw()
    match.dl_dst = EthAddr(dst_etha).toRaw()

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
    f = open("/home/mininet/topology/abilene_path.txt")
    line = f.readline()
    while line:
      word = line.split("     ")
      if len(word) == 3:
        route = []
        percent = ""
        path = word[1]       

        # get the path
        for sw in path.split("-"):
          route.append(sw + "_1")
        #log.info("route: %s" % route)

        # get the percent
        for i in range(word[2].find('%')):
          percent = percent + word[2][i]
        #log.info("percent: %s" % percent)

        src = self.t.id_gen(name = route[0])
        dst = self.t.id_gen(name = route[-1])
        src_dst_pair = (src.sw << 4) + dst.sw
        if src_dst_pair not in self.routeTable :
          #initialize the tables for the src id
          self.routeTable[src_dst_pair] = []
          self.percentTable[src_dst_pair] = []
        self.routeTable[src_dst_pair].append(route)
        self.percentTable[src_dst_pair].append(float(percent))

      line = f.readline()
    f.close()
    log.info("all the paths have been saved in the routeTable")

    # next step is to put the route on the topology

  def _install_paths(self):
    for src in range(1, NUMSWITCH + 1):
      for dst in range(1, NUMSWITCH + 1):
        if src != dst:
          src_dst_pair = (src << 4) + dst
          ingress_router = str(src) + '_1'
          egress_router = str(dst) + '_1'
          for host_src in sorted (self.t.down_hosts(ingress_router)):
            for host_dst in sorted (self.t.down_hosts(egress_router)):
              route  = self._choose_path(self.routeTable[src_dst_pair], 
                                         self.percentTable[src_dst_pair])
              #log.info("route : %s" % route)
              self._install_explicit_path(host_src, host_dst, route)
        else:
          # for hosts in the same switch
          router = str(src) + '_1'
          node_dpid = self.t.id_gen(name = router).dpid
          for host_dst in sorted (self.t.down_hosts(router)):
            final_out_port, ignore = self.t.port(router, host_dst)

            # Form OF match
            match = of.ofp_match()
            match.dl_dst = EthAddr(self.t.id_gen(name = host_dst).etha_str()).toRaw()
            self.switches[node_dpid].install(final_out_port, match)

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
      #log.info("self.routeTable : %s" % self.routeTable)
      self._install_paths()
      
      # the pre_install_paths should habe been installed    
      log.info("Woo! All paths ok")

def _timer_func():
  for connection in core.openflow._connections.values():
    connection.send(of.ofp_stats_request(body = of.ofp_flow_stats_request()))
  log.info("Sent %i flow stats requests", len(core.openflow._connections))
 
def launch(topo = None):

  if not topo:
    raise Exception("please specify topo and args on cmd line")
  else:
    t = buildTopo(topo,topos)

  core.registerNew(RipLController, t)

  # timer set to excute every ten seconds to get the feedback from the routers.
  #Timer(10, _timer_func, recurring = True)

  log.info("DHR-POX running with topo=%s." % topo)

