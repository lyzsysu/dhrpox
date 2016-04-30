#!/usr/bin/python
# Filename: test.py
# use to do some test to debug

import os
usr_home = os.path.expanduser('~')

import sys
sys.path.append(usr_home + "/dhrpox/topology")
sys.path.append(usr_home + "/dhrpox/traffic")
sys.path.append(usr_home + "/dhrpox/routing")

from basic_routing import *
from explicit_routing import *
from util import *
from readcost import *
from readtraffic import *
from readpath import *
from clustering import *
from generate_routing_policies import *

if __name__ == "__main__":

    num_matrix = 12

    link_file = usr_home + "/dhrpox/topology/abilene.txt"
    link, capacity, num_switch, num_link = read_link(link_file)

    #cluster_file = usr_home + "/dhrpox/routing/clusters_288TM_1.05_35.txt"
    #cluster = read_cluster(cluster_file, num_switch)

    traf_file = usr_home + "/dhrpox/traffic/12TM"
    tm = read_traffic(traf_file, num_matrix, num_switch)

    num_cluster = num_matrix
    cluster = {}
    num_pair = 35   
 
    for i in range(num_matrix):
        cluster[i] = []
        cluster[i].append(tm[i])
    
    p1 = calculate_merging_cost(cluster[10], cluster[11],
                                link, capacity, num_pair)
    p2 = calculate_merging_cost(cluster[11], cluster[10],
                                link, capacity, num_pair)
    print p1,p2

'''
    num_cluster = len(cluster)
    print "num_cluster is :", num_cluster

    print "num_matrix is :", len(tm)

    basic_traffic_matrix = get_basic_tm(tm, num_switch)

    mlu, allocation = destination_based_routing(basic_traffic_matrix,
                                                link, capacity)

    path = allocation_2_path(allocation, link, num_switch)

    num_selected = 35

    for c in range(1):
        print "Cluster %d: " % (c + 1)
        for m in range(len(cluster[c])):
            
            cluster_one = []
            cluster_one.append(0)
            cluster_one[0] = cluster[c][m]
            cluster_two = []
            cluster_two.append(0)
            cluster_two[0] = cluster[c][(m + 1)%len(cluster[c])]
            #print cluster_one[0][0][0]
            performance = \
            calculate_merging_cost(cluster_one, cluster_two, link,
                                   capacity, num_selected)
            print "performance of tm %d in cluster %d is %f" % (m, c,
                                                            performance)
'''
