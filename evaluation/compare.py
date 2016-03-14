#!/usr/bin/python
# Filename: compare.py

""" compare the performance of dhr and robust static routing
    to get a result like the paper give """

import os
usr_home = os.path.expanduser('~')

import sys
sys.path.append(usr_home + "/dhrpox/topology")
sys.path.append(usr_home + "/dhrpox/traffic")
sys.path.append(usr_home + "/dhrpox/routing")

from readlink import *
from readtraffic import *
from generate_routing_policies import *
from readpath import *

MAX = 10000

def calculate_traffic(tm, path, link, num_switch):

    """ calculate the traffic sum on each link using tm running in this path """

    tmp_link_traffic = [[0 for col in range(num_switch)]
                           for row in range(num_switch)]

    link_traffic = {}

    # tm is the test traffic matrix
    for src in range(num_switch):
        for dst in range(num_switch):
            if src == dst:
                continue
            if tm[src][dst] != 0:
                for num in path[src][dst]:
                    # come through all the route
                    route = path[src][dst][num]['route'].split("-")
                    route_len = len(route)
                    percentage = float(path[src][dst][num]['percent']) / 100

                    for i in range(route_len - 1):
                        # when the route pass by one link, add the traffic on
                        # on this link
                        (fst, sec) = (int(route[i]) - 1, int(route[i + 1]) - 1)
                        tmp_link_traffic[fst][sec] += (tm[src][dst]
                                                       * percentage)
           
            # change the traffic from t[node][node] to t[link] 
            for l in link:
                (fst, sec) = link[l]
                link_traffic[l] = tmp_link_traffic[fst][sec]
    
    return link_traffic 

def calculate_performance(tm, m, path, link, capacity, 
                          optimal_utilization, num_switch):

    """ calculate the performance when we use this path to run this tm """

    num_link = len(link)

    link_traffic = calculate_traffic(tm, path, link, num_switch)
   
    link_utilization = {}
 
    mlu = 0
    for l in range(num_link):
        (fst, sec) = link[l]
        link_utilization[l] = link_traffic[l] / capacity[l]

        if link_utilization[l] > mlu:
            mlu = link_utilization[l]
   
    #print mlu, optimal_utilization[m]
 
    performance = mlu / optimal_utilization[m]

    return performance

def main():
    
    num_matrix = 288

    link_file = usr_home + "/dhrpox/topology/abilene.txt"
    link, capacity, num_switch, num_link = read_link(link_file)

    traffic_file = usr_home + "/dhrpox/traffic/288TM"
    tm = read_traffic(traffic_file, num_matrix, num_switch)

    optimal_utilization = [0] * num_matrix

    for t in range(num_matrix):
        optimal_utilization[t], ignore = \
        destination_based_routing(tm[t], link, capacity)

    robust_path_file = (usr_home + "/dhrpox/routing/robust_path.txt")
    robust_path = read_robust_path(robust_path_file, num_switch)

    cluster_file = (usr_home + "/dhrpox/routing/clusters_288TM_k_5_p_1.05.txt")
    cluster = read_cluster(cluster_file, num_switch)

    num_cluster = len(cluster)

    dhr_path_file = (usr_home + "/dhrpox/routing/dhr_path.txt")
    dhr_path = read_dhr_path(dhr_path_file, num_switch, num_cluster)

    dhr2_path_file = (usr_home + "/dhrpox/routing/dhr2_path.txt")
    dhr2_path = read_dhr_path(dhr2_path_file, num_switch, num_cluster)

    compare_result_file = usr_home + "/dhrpox/evaluation/compare_result"
    f = open(compare_result_file,"w+")

    # for every matrix in traffic matrix list
    # calculate the robust_performance and the dhr_performance
    # and compare them
    for m in range(num_matrix):
        robust_performance = calculate_performance(tm[m], m, robust_path, 
                                            link, capacity, 
                                            optimal_utilization, num_switch)
        # because we have many dhr path for different clusters,
        # we choose the best performance among them.
        # for we can find out the tm is mostly close to which cluster
        # and use the path for that cluster
        dhr_performance = MAX
        for c in range(num_cluster):
            performance = calculate_performance(tm[m], m, dhr_path[c],
                                                link, capacity, 
                                                optimal_utilization,
                                                num_switch)
            if performance < dhr_performance:
                dhr_performance = performance

        # if i calculate the basic path based on cluster, not on all the tm(288)
        # then i may get another result, but it may have bad things when
        # put into the real switch
        # for we have to change all the flow table when we change policy
        dhr2_performance = MAX
        for c in range(num_cluster):
            performance = calculate_performance(tm[m], m, dhr2_path[c],
                                                link, capacity,
                                                optimal_utilization,
                                                num_switch)
            if performance < dhr2_performance:
                dhr2_performance = performance

        f.write("robust %f VS dhr %f VS dhr2 %f\n" % (robust_performance,
                                                     dhr_performance,
                                                     dhr2_performance))
        print "robust %f VS dhr %f VS dhr2 %f" % (robust_performance,
                                                 dhr_performance,
                                                 dhr2_performance)
    f.close()

if __name__ == "__main__":
    main()

