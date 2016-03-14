#!/usr/bin/python
# Filename: generate_routing_policy.py

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

def read_cluster(filename, num_switch):

    """ read cluster from txt file """

    f = open(filename)

    num_m = num_c = -1
    src = dst = 0

    cluster = {}

    line = f.readline()
    while line:
        if line.split(" ")[0] == "next":
            if line.split(" ")[1] == "cluster":
                num_m = -1
                num_c = num_c + 1
                cluster[num_c] = []
            elif line.split(" ")[1] == "tm":
                src = 0
                dst = 0
                num_m = num_m + 1
                cluster[num_c].append(num_m)
                cluster[num_c][num_m] = [[0.0 for col in range(num_switch)]
                                              for row in range(num_switch)]
            line = f.readline()
            continue
        for demand in line.split(" "):
            if demand != "\n":
                cluster[num_c][num_m][src][dst] = float(demand)
                dst = dst + 1
                if 12 == dst:
                    dst = 0
                    src = src + 1
        line = f.readline()
    f.close()

    return cluster

if __name__ == "__main__":

    num_matrix = 288

    link_file = usr_home + "/dhrpox/topology/abilene.txt"
    link, capacity, num_switch, num_link = read_link(link_file)

    cluster_file = usr_home + "/dhrpox/routing/clusters_288TM_k_5_p_1.05.txt"
    cluster = read_cluster(cluster_file, num_switch)

    num_cluster = len(cluster)
    print "num_cluster is :", num_cluster

    output_file = usr_home + "/dhrpox/routing/dhr2_path.txt"

    f = open(output_file,"w+")

    #traffic_file = usr_home + "/dhrpox/traffic/288TM"
    #tm = read_traffic(traffic_file, num_matrix, num_switch)

    #basic_traffic_matrix = get_basic_tm(tm, num_switch)

    #mlu, allocation = destination_based_routing(basic_traffic_matrix, 
    #                                            link, capacity)
        
    #path = allocation_2_path(allocation, link, num_switch)

    for c in range(num_cluster):
        f.write("Cluster %d: \n" % (c + 1))

        basic_traffic_matrix = get_basic_tm(cluster[c], num_switch)

        mlu, allocation = destination_based_routing(basic_traffic_matrix,
                                                    link, capacity)

        path = allocation_2_path(allocation, link, num_switch)


        performance, explicit_fraction, selected_node_pair = \
        explicit_routing(cluster[c], link, capacity)
        
        explicit_path = explicit_fraction_2_path(explicit_fraction,
                                                 selected_node_pair, link)

        # write the final path to the abilene_288TM.txt
        
        for src in range(num_switch):
            for dst in range(num_switch):
                if src == dst:
                    continue
                
                f.write("Paths from %d to %d\n" % (src + 1, dst + 1))
                if (src, dst) in selected_node_pair:
                    count = 1
                    index = selected_node_pair.index((src, dst))
                    for p in explicit_path[index]:
                        f.write("Path %d     " % count)
                        f.write("%s" % explicit_path[index][p]['route'])
                        f.write("     ")
                        f.write("%f" % (explicit_path[index][p]['percent']
                                        * 100))
                        f.write("% ")
                        f.write("\n")
                        count = count + 1
                    f.write("\n")
                else:
                    count = 1
                    for p in path[src][dst]:
                        f.write("Path %d     " % count)
                        f.write("%s" % path[src][dst][p]['route'])
                        f.write("     ")
                        f.write("%f" % (path[src][dst][p]['percent'] * 100))
                        f.write("% ")
                        f.write("\n")
                        count = count + 1
                    f.write("\n")

        # num_pair = len(allocation)
        # num_link = len(link)

        # for p in range(len(allocation)):
        #     for l in range(len(allocation[p])):
        #         if allocation[p][l] != 0.0:
        #             print links[l]," ",allocation[p][l]," ",
        #     print
        #     print

    # for c in range(num_cluster):
    #     print "next cluster"
    #     for m in range(len(cluster[c])):
    #         print "next matrix"
    #         for s in range(num_switch):
    #             for d in range(num_switch):
    #                 print cluster[c][m][s][d]," ",
    #             print
