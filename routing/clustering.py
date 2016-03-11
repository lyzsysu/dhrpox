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

def calculate_merging_cost(cluster_a, cluster_b, link, capacity):

    """ merge cluster_b into cluster_a, and return the performance 
        after merging """

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

    performance, ignore1, ignore2 = explicit_routing(traffic_matrix, 
                                                     link, capacity)

    return performance

def insert_traffic_matrices(cluster_a, cluster_b):

    """ insert cluster_b into cluster_a """

    for tm in cluster_b:
        cluster_a.append(tm)

    return cluster_a

def clustering(traffic_matrix, link, capacity, p_threshold):
    
    """ do the clustering by input all the tm """

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

    for i in cluster:
        for j in cluster:
            if i == j:
                continue
            cost[i][j] = calculate_merging_cost(cluster[i], cluster[j], 
                                                link, capacity)

            print ("the performance of merging cluster %d and %d : %f"
                   % (i, j, cost[i][j]))

            # print "cost[i][j] = ", cost[i][j]

    print "Finish initial merging cost calculation"

    print "use time: ", (time() - start), " secs."

    f = open("/home/mininet/dhrpox/routing/cost_tmp","w+")
    for i in cluster:
        for j in cluster:
            f.write("%d %d %f" % (i, j, cost[i][j]))
            f.write("\n")
    f.close()

    while num_cluster != 1:
        #  Find the pair of clusters Ci and Cj with minimum costi, j.
        #  If the minimum costi, j > Pthreshold, set R =CN and exit.
        #  Otherwise go to next step.
        min_cost = MAX
        for i in cluster:
            for j in cluster:
                if i == j:
                    continue
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
                    calculate_merging_cost(cluster[selected_a], 
                                           cluster[j], link, capacity)
                    print "update cost %d,%d : %f" % (selected_a, j,
                                                      cost[selected_a][j]) 

    clusters_after_clustering = {}
    num_cluster = 0
    for i in cluster:
        clusters_after_clustering[num_cluster] = []
        for tm in cluster[i]:
            clusters_after_clustering[num_cluster].append(tm)

        num_cluster = num_cluster + 1

    return clusters_after_clustering

if __name__ == "__main__":

    num_matrix = 12

    link, capacity, num_switch, num_link = \
    read_link("/home/mininet/dhrpox/topology/abilene.txt")

    tm = read_traffic("/home/mininet/dhrpox/traffic/12TM",
                      num_matrix, num_switch)

    start = time()

    clusters = clustering(tm, link, capacity, 1.05)
  
    now = time()
 
    print 'All done in %0.2fs!' % (now - start)

    print "cluster num : ", len(clusters) 
 
    f = open("/home/mininet/dhrpox/routing/try_clusters.txt","w+")
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
         
     
