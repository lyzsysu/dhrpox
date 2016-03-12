#!/usr/bin/python
# Filename: test.py

""" test the functions of basic routing and explicit routing """

import os
usr_home = os.path.expanduser('~')

import sys
sys.path.append(usr_home + "/dhrpox/topology")
sys.path.append(usr_home + "/dhrpox/traffic")
sys.path.append(usr_home + "/dhrpox/routing")

from readlink import *
from readtraffic import *
from basic_routing import *
from explicit_routing import *
from util import *

def main():
    
    num_matrix = 288

    link_file = usr_home + "/dhrpox/topology/abilene.txt"
    link, capacity, num_switch, num_link = read_link(link_file)

    traffic_file = usr_home + "/dhrpox/traffic/288TM"
    tm = read_traffic(traffic_file, num_matrix, num_switch)

    basic_tm = get_basic_tm(tm, num_switch)

    mlu, allocation = destination_based_routing(basic_tm, link, capacity) 

    path = allocation_2_path(allocation, link, num_switch)

    # print path

    ################################################################

    tm_tmp = {}

    tm_tmp[0] = tm[0]

    performance, explicit_fraction, selected_node_pair = \
    explicit_routing(tm_tmp, link, capacity)

    explicit_path = explicit_fraction_2_path(explicit_fraction,
                                    selected_node_pair, link)

    for p in explicit_path:
        print p

if __name__ == "__main__":

    main()
