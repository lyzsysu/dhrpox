#!/usr/bin/python

import os
usr_home = os.path.expanduser('~')

import sys
sys.path.append(usr_home + "/dhrpox/routing")
sys.path.append(usr_home + "/dhrpox/topology")
sys.path.append(usr_home + "/dhrpox/traffic")

from readlink import *
from readtraffic import *
from destination_based_routing import *
from explicit_path_routing import *

MAX = 100000000

def calculate_merging_cost(cluster_one, cluster_two, links, capacity):

    num_matrix = len(cluster_one) + len(cluster_two)
    num_switch = len(cluster_one[0])

    traffic_matrix = [[[0.0 for col in range(num_switch)]for row in range(num_switch)]for row in range(num_matrix)]

    num = 0
    for tm in cluster_one:
        traffic_matrix[num] = tm
        num = num + 1

    for tm in cluster_two:
        traffic_matrix[num] = tm
        num = num + 1

    performance, ignore1, ignore2 = explicit_routing(traffic_matrix, links, capacity)

    return performance

def insert_traffic_matrices(cluster_one, cluster_two):

    for tm in cluster_two:
        cluster_one.append(tm)

    return cluster_one

def traffic_matrix_clustering(traffic_matrix, links, capacity, p_threshold):
    
    '''
        Initialize each given traffic matrix as a cluster, 
        set cluster number CN = L 
        (L is the number of total given traffic matrices)
    '''

    num_matrix = len(traffic_matrix)
    num_cluster = num_matrix

    cluster = {}

    for i in range(num_matrix):
        cluster[i] = []
        cluster[i].append(traffic_matrix[i])
    
    #print cluster

    '''
        For each pair of clusters Ci and Cj, 
        calculate the "merging cost" and denote it as costi, j.
    '''

    cost = [[0.0 for col in range(num_cluster)]for row in range(num_cluster)]

    for i in cluster:
        for j in cluster:
            if i == j:
                continue

            cost[i][j] = calculate_merging_cost(cluster[i],cluster[j], links, capacity)
            print "cost[i][j] = ", cost[i][j]

    while num_cluster != 1:

        '''
            Find the pair of clusters Ci and Cj with minimum costi, j.
            If the minimum costi, j > Pthreshold, set R =CN and exit.
            Otherwise go to next step.
        '''

        min_cost = MAX
        for i in cluster:
            for j in cluster:
                if i == j:
                    continue

                if cost[i][j] < min_cost:
                    min_cost = cost[i][j]
                    one = i
                    two = j
        print "min_cost: ", min_cost

        if min_cost > p_threshold:
            break

        else:        

            '''
                Insert all traffic matrices belonging to Cj into Ci, 
                and then remove Cj. CN =CN .1.
            '''

            insert_traffic_matrices(cluster[one], cluster[two])
            cluster.pop(two)
            num_cluster = num_cluster - 1

            '''
                Update the costi, j related to the new cluster, 
                and delete the costi, j related to the removed cluster. 
            '''
            for j in cluster:
                if j == one:
                    continue
                else:
                    cost[one][j] = calculate_merging_cost(\
                                       cluster[one], cluster[j], links, capacity)

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

    links, capacity, num_link, num_switch = read_link(usr_home + "/dhrpox/topology/abilene.txt")

    traffic_matrix = read_traffic(usr_home + "/dhrpox/traffic/2014_06_24_12TM", num_matrix, num_switch)

    clusters = traffic_matrix_clustering(traffic_matrix, links, capacity, 1.05)
   
    print "cluster num : ", len(clusters)
    
 
    f = open("/home/mininet/dhrpox/routing/clusters.txt","w+")
    for c in range(len(clusters)):
         print "cluster %d" % c, "has %d" % len(clusters[c]), " matrices"
         for m in range(len(clusters[c])):
             for s in range(num_switch):
                 for d in range(num_switch):
                     f.write(str(clusters[c][m][s][d]))
                     f.write(" ")
             f.write("\n")
         f.write("next cluster\n")
    
         
     
