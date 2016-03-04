"""
Switch
"""
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

# include as part of the betta branch
from pox.openflow.of_json import *

log = core.getLogger()
#log.setLevel(logging.WARNING)

# Borrowed from pox/forwarding/l2_multi
class Switch (object):
  def __init__ (self):
    self.connection = None
    self.ports = None
    self.dpid = None
    self._listeners = None

  def __repr__ (self):
    return dpidToStr(self.dpid)

  def disconnect (self):
    if self.connection is not None:
      log.debug("Disconnect %s" % (self.connection,))
      self.connection.removeListeners(self._listeners)
      self.connection = None
      self._listeners = None

  def connect (self, connection):
    if self.dpid is None:
      self.dpid = connection.dpid
    assert self.dpid == connection.dpid
    if self.ports is None:
      self.ports = connection.features.ports
    self.disconnect()
    log.debug("Connect %s" % (connection,))
    self.connection = connection
    self._listeners = connection.addListeners(self)

  def send_packet_data(self, outport, data = None):
    msg = of.ofp_packet_out(in_port = of.OFPP_NONE, data = data)
    msg.actions.append(of.ofp_action_output(port = outport))
    self.connection.send(msg)

  def install(self, port, match, buf = None, idle_timeout = 0, hard_timeout = 0,
              priority = of.OFP_DEFAULT_PRIORITY):
    msg = of.ofp_flow_mod()
    msg.match = match
    msg.idle_timeout = idle_timeout
    msg.hard_timeout = hard_timeout
    msg.priority = priority
    msg.actions.append(of.ofp_action_output(port = port))
    msg.buffer_id = buf
    self.connection.send(msg)

  def install_multiple(self, actions, match, buf = None, idle_timeout = 0, 
                       hard_timeout = 0, priority = of.OFP_DEFAULT_PRIORITY):
    # install multiple actions
    msg = of.ofp_flow_mod()
    msg.match = match
    msg.idle_timeout = idle_timeout
    msg.hard_timeout = hard_timeout
    msg.priority = priority
    for a in actions:
      msg.actions.append(a)
    msg.buffer_id = buf
    self.connection.send(msg)
    
  def _handle_ConnectionDown (self, event):
    self.disconnect()
    pass

