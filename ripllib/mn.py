"""Custom topologies for Mininet

author: Brandon Heller (brandonh@stanford.edu)

To use this file to run a RipL-specific topology on Mininet.  Example:

  sudo mn --custom ~/ripl/ripl/mn.py --topo ft,4
"""

from ripllib.dctopo import FatTreeTopo #, VL2Topo, TreeTopo
from ripllib.abilene import AbileneTopo
from ripllib.asymmetry import AsymmetricTopo

topos = { 'ft': FatTreeTopo,
          'abilene': AbileneTopo,
          'asym': AsymmetricTopo}
#,
#          'vl2': VL2Topo,
#          'tree': TreeTopo }
