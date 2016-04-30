#!/usr/bin/python
# Filename: clustering.py

import os
usr_home = os.path.expanduser('~')

import sys
sys.path.append(usr_home + "/dhrpox/routing")
sys.path.append(usr_home + "/dhrpox/topology")
sys.path.append(usr_home + "/dhrpox/traffic")

from readlink import *
from readtraffic import *
from basic_routing import *
from explicit_routing import *
from util import *

from time import time

MAX = 100000000

def calculate_merging_cost(cluster_a, cluster_b, all_tm,
                           link, capacity, num_pair):

    """ Merge cluster_b into cluster_a, and return the performance 
        after merging.
    """

    num_matrix = len(cluster_a) + len(cluster_b)
    num_switch = len(cluster_a[0])

    traffic_matrix = [[[0.0 for col in range(num_switch)]
                            for row in range(num_switch)]
                            for row in range(num_matrix)]

    num = 0
    for tm in cluster_a:
        traffic_matrix[num] = tm
        num = num + 1

    for tm in cluster_b:
        traffic_matrix[num] = tm
        num = num + 1

    performance, ignore1, ignore2 = explicit_routing(traffic_matrix, all_tm,
                                                     link, capacity, num_pair)

    return performance

def insert_traffic_matrices(cluster_a, cluster_b):

    """ insert cluster_b into cluster_a """

    for tm in cluster_b:
        cluster_a.append(tm)

    return cluster_a

def clustering(traffic_matrix, link, capacity, p_threshold, num_pair):
    
    """ Clustering by input all the traffic matrices.
    """

    # Initialize each given traffic matrix as a cluster, 
    # set cluster number CN = L 
    # (L is the number of total given traffic matrices)

    start = time()

    num_matrix = len(traffic_matrix)
    num_cluster = num_matrix

    cluster = {}

    for i in range(num_matrix):
        cluster[i] = []
        cluster[i].append(traffic_matrix[i])
    
    # print cluster

    # For each pair of clusters Ci and Cj, 
    # calculate the "merging cost" and denote it as costi, j.

    cost = [[0.0 for col in range(num_cluster)]
                 for row in range(num_cluster)]

    # read cost from cost file

    # f = open(usr_home + "/dhrpox/routing/cost/cost_" + str(num_matrix) + \
    #          "TM_" + str(p_threshold) + "_" + str(num_pair) + ".txt")
    # line = f.readline()
    # while line:
    #     i = int(line.split(' ')[0])
    #     j = int(line.split(' ')[1])
    #     cost[i][j] = float(line.split(' ')[2])
    #     line = f.readline()
    # f.close()

    # calculate cost and save them into cost file
    for i in cluster:
        for j in cluster:
            if i == j:
                continue
            cost[i][j] = calculate_merging_cost(cluster[i], cluster[j],
                                                traffic_matrix, 
                                                link, capacity, num_pair)
    
            print ("the performance of merging cluster %d and %d : %f"
                   % (i, j, cost[i][j]))

            # print "cost[%d][%d] = %f" % (i, j, cost[i][j])

    print "Finish initial merging cost calculation"

    print "use time: ", (time() - start), " secs."

    # open the cost file to save the clustering cost
    f = open(usr_home + "/dhrpox/routing/cost/cost_" + str(num_matrix) + \
             "TM_" + str(p_threshold) + "_" + str(num_pair) + ".txt","w+")

    for i in range(num_cluster):
        for j in range(num_cluster):
            f.write("%d %d %f" % (i, j, cost[i][j]))
            f.write("\n")
    f.close()

    # start to cluster
    while num_cluster != 1:
        #  Find the pair of clusters Ci and Cj with minimum costi, j.
        #  If the minimum costi, j > Pthreshold, set R =CN and exit.
        #  Otherwise go to next step.
        min_cost = MAX
        for i in cluster:
            for j in cluster:
                if i == j:
                    continue
                # print "cost[%d][%d] : %f" % (i, j, cost[i][j])
                if cost[i][j] < min_cost:
                    min_cost = cost[i][j]
                    selected_a = i
                    selected_b = j
       
        # print "min_cost: ", min_cost

        if min_cost > p_threshold:
            print "min_cost : %s > p_threshold, clustering finish" % min_cost
            break
        else:        
            # Insert all traffic matrices belonging to Cj into Ci, 
            # and then remove Cj. 
            # CN = CN - 1.
            print "merge %d into %d" % (selected_b, selected_a)
            insert_traffic_matrices(cluster[selected_a], cluster[selected_b])
            cluster.pop(selected_b)
            num_cluster = num_cluster - 1

            # Update the costi, j related to the new cluster, 
            # and delete the costi, j related to the removed cluster. 
            for j in cluster:
                if j == selected_a:
                    continue
                else:
                    cost[selected_a][j] = \
                    calculate_merging_cost(cluster[selected_a], cluster[j],
                                           traffic_matrix, link, 
                                           capacity, num_pair)
                    cost[j][selected_a] = cost[selected_a][j]
                    print "update cost %d,%d : %f" % (selected_a, j,
                                                      cost[selected_a][j]) 

    # save the clusters into the dict
    clusters_after_clustering = {}
    num_cluster = 0
    for i in cluster:
        clusters_after_clustering[num_cluster] = []
        for tm in cluster[i]:
            clusters_after_clustering[num_cluster].append(tm)

        num_cluster = num_cluster + 1

    return clusters_after_clustering

def main(argv):
    
    num_matrix = int(argv[1])
    p_threshold = float(argv[2])
    num_pair = int(argv[3])

    link_file = usr_home + "/dhrpox/topology/abilene.txt"
    link, capacity, num_switch, num_link = read_link(link_file)

    traffic_file = usr_home + "/dhrpox/traffic/" + str(num_matrix) + "TM"
    tm = read_traffic(traffic_file, num_matrix, num_switch)

    start = time()

    clusters = clustering(tm, link, capacity, 1.05, 35)
  
    now = time()
 
    print 'All done in %0.2fs!' % (now - start)

    print "cluster num : ", len(clusters) 

    # save cluster result into clusters file
 
    f = open(usr_home + "/dhrpox/routing/clusters/clusters_" + \
             str(num_matrix) + "TM_" + str(p_threshold) + \
             "_" + str(num_pair) + ".txt","w+")
    for c in range(len(clusters)):
        f.write("next cluster  \n")
        print "cluster %d" % c, "has %d" % len(clusters[c]), " matrices"
        for m in range(len(clusters[c])):
            f.write("next tm  \n")
            for s in range(num_switch):
                for d in range(num_switch):
                    f.write(str(clusters[c][m][s][d]))
                    f.write(" ")
                f.write("\n")
    f.close() 
        
if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise Exception("you should input 'python clustering.py num_matrix" + 
                        "p_threshold selected_node_pair")
    main(sys.argv)
