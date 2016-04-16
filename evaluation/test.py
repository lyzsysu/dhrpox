#!/usr/bin/python
# Filename: test.py

""" test the functions of basic routing and explicit routing """

import os
usr_home = os.path.expanduser('~')

import sys
sys.path.append(usr_home + "/dhrpox/topology")
sys.path.append(usr_home + "/dhrpox/traffic")
sys.path.append(usr_home + "/dhrpox/routing")

import math

from readlink import *
from readtraffic import *
from basic_routing import *
from explicit_routing import *
from generate_routing_policies import *
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

def calculate_utilization(traffic_load, name, capacity):

    link_utilization = {}

    mlu = 0
    congested_link = 0
    for l in range(len(traffic_load)):
        # * 10 means 10 threads

        # / 1000 means KBytes change to MBytes

        # * 10 because the mininet can only create 1000M link, so if the 
        # abilene link is 9920M --> 992M   so the traffic calculate should * 10

        link_utilization[l] = math.floor(traffic_load[l] * 10 / 1000 * 10) / float(capacity[l])
        # print link_utilization[l]," ",

        if link_utilization[l] > mlu:
            mlu = link_utilization[l]
            congested_link = l

    print "the most congested link in %s is %d, the usage is %f" % \
          (name, congested_link, mlu)
    print capacity[congested_link], 
    print math.floor(traffic_load[congested_link] / 10)
    print "%s can raise %f " % (name ,capacity[congested_link] / \
                                (math.floor(traffic_load[congested_link] / 10))
                               )

    return link_utilization

def test_goodput():
     
    num_matrix = 288

    # read link imformations
    link_file = usr_home + "/dhrpox/topology/abilene.txt"
    link, capacity, num_switch, num_link = read_link(link_file)

    # read traffic matrices
    traffic_file = usr_home + "/dhrpox/traffic/288TM"
    tm = read_traffic(traffic_file, num_matrix, num_switch)

    # read cluster imformations
    cluster_file = (usr_home + "/dhrpox/routing/clusters/clusters_288TM_1.05_35.txt")
    cluster = read_cluster(cluster_file, num_switch)

    num_cluster = len(cluster)

    # read dhr paths for each cluster
    dhr_path_file = (usr_home + "/dhrpox/routing/path/dhr_288TM_1.05_35.txt")
    dhr_path = read_dhr_path(dhr_path_file, num_switch, num_cluster)
 
    # read robust path
    robust_path_file = (usr_home + "/dhrpox/routing/path/robust_path.txt")
    robust_path = read_robust_path(robust_path_file, num_switch)

    # read oblivious path
    oblivi_path_file = (usr_home + "/dhrpox/routing/path/oblivious_path.txt")
    oblivi_path = read_robust_path(oblivi_path_file, num_switch) 

    selected_node_pairs = []

    sum_1 = 0
    for i in range(num_switch):
        for j in range(num_switch):
            if i == j:
                continue
            tm[0][i][j] = int(tm[0][i][j] / 100)
            if tm[0][i][j] < 15:
                tm[0][i][j] = 0
            sum_1 += tm[0][i][j]
            print tm[0][i][j]," ",
        print 

    print "sum_1 = %d Kb" % sum_1

    # calculate dhr load
    dhr_load = \
    calculate_background_load(0, selected_node_pairs, tm, link, dhr_path[4])

    # calculate robust load
    robust_load = \
    calculate_background_load(0, selected_node_pairs, tm, link, robust_path)

    # calculate oblivious load
    oblivi_load = \
    calculate_background_load(0, selected_node_pairs, tm, link, oblivi_path)

    # calculate link utilization
    link_utilization = calculate_utilization(dhr_load, "dhr", capacity)
    link_utilization = calculate_utilization(robust_load, "robust", capacity)
    link_utilization = calculate_utilization(oblivi_load, "oblivious", capacity)


if __name__ == "__main__":

    # main()
    test_goodput()
