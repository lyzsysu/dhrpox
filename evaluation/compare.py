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

    robust_path = [[{} for col in range(num_switch)]
                       for row in range(num_switch)]

    # write down the robust_path in the file
    f = open(robust_path_file)
    line = f.readline()
    while line:
        if line.split(" ")[0] == "Paths":
            src = int(line.split(" ")[2]) - 1
            dst = int(line.split(" ")[4].split("\n")[0]) - 1
        if line.split(" ")[0] == "Path":
            route = line.split("     ")[1]
            percent = line.split("     ")[2].split("%")[0]
            count = line.split(" ")[1]

            robust_path[src][dst][count] = {}
            robust_path[src][dst][count]['route'] = route
            robust_path[src][dst][count]['percent'] = percent
        line = f.readline()
    f.close()

    # show the robust path result
    # for src in range(num_switch):
    #     for dst in range(num_switch):
    #         if src == dst:
    #             continue
    #         for p in robust_path[src][dst]:
    #             print (robust_path[src][dst][p]['route'],
    #                    robust_path[src][dst][p]['percent'])

    cluster_file = (usr_home + "/dhrpox/routing/clusters_288TM_k_5_p_1.05.txt")
    cluster = read_cluster(cluster_file, num_switch)

    num_cluster = len(cluster)

    dhr_path_file = (usr_home + "/dhrpox/routing/dhr_path.txt")

    dhr_path = [[[{} for col in range(num_switch)]
                     for row in range(num_switch)]
                     for c in range(num_cluster)]

    # write down the dhr path in the file
    f = open(dhr_path_file)
    line = f.readline()
    while line:
        if line.split(" ")[0] == "Cluster":
            c = int(line.split(" ")[1].split(":")[0]) - 1
        if line.split(" ")[0] == "Paths":
            src = int(line.split(" ")[2]) - 1
            dst = int(line.split(" ")[4].split("\n")[0]) - 1
        if line.split(" ")[0] == "Path":
            route = line.split("     ")[1]
            percent = line.split("     ")[2].split("%")[0]
            count = line.split(" ")[1]

            dhr_path[c][src][dst][count] = {}
            dhr_path[c][src][dst][count]['route'] = route
            dhr_path[c][src][dst][count]['percent'] = percent
        line = f.readline()

    # show the dhr path result
    # for c in range(num_cluster):
    #     print "cluster %d " % c
    #     for src in range(num_switch):
    #         for dst in range(num_switch):
    #             if src == dst:
    #                 continue
    #             for p in dhr_path[c][src][dst]:
    #                 print (dhr_path[c][src][dst][p]['route'],
    #                        dhr_path[c][src][dst][p]['percent'])


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

        print "robust %f VS %f dhr" % (robust_performance, dhr_performance)

if __name__ == "__main__":
    main()

