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

    link, capacity, num_switch, num_link = \
    read_link("/home/mininet/dhrpox/topology/abilene.txt")

    tm = read_traffic("/home/mininet/dhrpox/traffic/288TM", 
                      num_matrix, num_switch)

    print tm[0]

    basic_tm = get_basic_tm(tm, num_switch)

    mlu, allocation = destination_based_routing(basic_tm, link, capacity) 

    path = allocation_2_path(allocation, link, num_switch)

    #print path

    ################################################################

    tm_tmp = {}

    tm_tmp[0] = tm[0]

    performance, explicit_fraction, selected_node_pair = \
    explicit_routing(tm_tmp, link, capacity)

    num_pair = len(selected_node_pair)

    explicit_path = explicit_fraction_2_path(explicit_fraction,
                                    selected_node_pair, link)

    for p in explicit_path:
        print p

if __name__ == "__main__":

    main()
