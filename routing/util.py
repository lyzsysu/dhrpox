#!/usr/bin/python
# Filename: util.py

""" provide some functions for basic_routing and explicit_routing"""

import os
usr_home = os.path.expanduser('~')

import sys
sys.path.append(usr_home + "/dhrpox/topology")
sys.path.append(usr_home + "/dhrpox/traffic")
sys.path.append(usr_home + "/dhrpox/routing")

from readlink import *
from readtraffic import *
from basic_routing import *

def search_basic_path(dst, egress_switch, tmp_path, tmp_percent, 
                fraction, link, path):

    """ deep first search for the path from an ingress switch 
        to an egress switch """

    num_link = len(link)

    for l in range(num_link):
        (node, next_node) = link[l]
        if next_node == egress_switch and fraction[dst][l] != 0.0:
            prev_path = tmp_path
            prev_percent = tmp_percent
            tmp_path = str(node + 1) + "-" + tmp_path
            tmp_percent = tmp_percent * fraction[dst][l]

            # search node as the next_node :  x -> node -> next_node
            search_basic_path(dst, node, tmp_path, tmp_percent, 
                        fraction, link, path)

            count = len(path[node][dst])
            path[node][dst][count] = {}
            path[node][dst][count]['route'] = tmp_path
            path[node][dst][count]['percent'] = tmp_percent

            tmp_path = prev_path
            tmp_percent = prev_percent

def allocation_2_path(allocation, link, num_switch):
    
    """ this function is used to derive destination-based routing fractions 
        and paths from traffic allocation """

    num_link = len(link)

    fraction = [[0 for col in range(num_link)] 
                   for row in range(num_switch)]

    # fraction is the traffic allocation on the same switch
    #  devided by different links
    # eg:
    #               30%  --->  switch2
    #          switch1
    #               70%  --->  switch3
    for d in range(num_switch):
        for l in range(num_link):
            (i, j) = link[l]
            Sum = 0.0
            for out_link in range(num_link):
                (out, ignore) = link[out_link]
                if out == i:
                    Sum = Sum + allocation[d][out_link]
            if Sum == 0.0:
                fraction[d][l] = 0
            else:
                fraction[d][l] = allocation[d][l] / Sum

    # print the result of fraction
    # for dst in range(num_switch):
    #     for l in range(num_link):
    #         if fraction[dst][l] != 0.0:
    #             print ("%s %f " % (link[l], fraction[dst][l]))
    #    print 

    # after getting the destination-based routing fractions, 
    # we can formulate the paths

    path = [[{} for col in range(num_switch)]
                for row in range(num_switch)]

    for dst in range(num_switch):
        tmp_path = str(dst + 1)
        tmp_percent = 1.0
        egress_switch = dst
        search_basic_path(dst, egress_switch, tmp_path, tmp_percent, fraction, link, path)

    return path

#########################################################################
# above : some utility functions for basic routing
# below : some utility functions for explicit routing
#########################################################################

def path_2_contribution(path, num_switch):

    """ this function get the mapping of which src-dst pair
        have contribution on the link,
        and save it in the "contribution" dict """

    contribution = {}

    for src in range(num_switch):
        for dst in range(num_switch):
            if src != dst:
                for num in range(len(path[src][dst])):
                  route = path[src][dst][num]['route'].split("-")
                  for i in range(len(route) - 1):
                      (fst, sec) = (int(route[i]) - 1, int(route[i + 1]) - 1)
                      if (fst, sec) not in contribution:
                          contribution[(fst, sec)] = []
                      if (src, dst) not in contribution[(fst, sec)]:
                          contribution[(fst, sec)].append((src, dst))

    return contribution

def search_explicit_path(p, src, egress_switch, tmp_path, tmp_percent,
                fraction, link, path):

    """ deep first search for the path from a switch to another """

    num_link = len(link)

    for l in range(num_link):
        (node, next_node) = link[l]
        if next_node == egress_switch and fraction[p][l] != 0.0:
            prev_path = tmp_path
            prev_percent = tmp_percent
            tmp_path = str(node + 1) + "-" + tmp_path
            if fraction[p][l] < tmp_percent:
                tmp_percent = fraction[p][l]

            if node == src:
                count = len(path[p])
                path[p][count] = {}
                path[p][count]['route'] = tmp_path
                path[p][count]['percent'] = tmp_percent

            # search node as the next_node :  x -> node -> next_node
            search_explicit_path(p, src, node, tmp_path, tmp_percent,
                                 fraction, link, path)
            # append the path that towards the dst
            # from this node and its percentage
            tmp_path = prev_path
            tmp_percent = prev_percent

def explicit_fraction_2_path(fraction, selected_node_pair, link):

    """ get the explicit path for selected node pairs 
        based on the explicit fraction """

    num_pair = len(selected_node_pair)

    path = [{} for p in range(num_pair)]

    for p in range(num_pair):
        (src, dst) = selected_node_pair[p]
        tmp_path = str(dst + 1)
        tmp_percent = 1.0
        egress_switch = dst
        search_explicit_path(p, src, egress_switch, tmp_path,
                             tmp_percent, fraction, link, path)

    return path

def main():

    num_matrix = 288

    link, capacity, num_switch, num_link = \
    read_link("/home/mininet/dhrpox/topology/abilene.txt")

    tm = read_traffic("/home/mininet/dhrpox/traffic/288TM",
                      num_matrix, num_switch)

    basic_tm = get_basic_tm(tm, num_switch)

    mlu, allocation = destination_based_routing(basic_tm, link, capacity)

    path = allocation_2_path(allocation, link, num_switch)

    # save the allocation result into a txt file
    # f = open("/home/mininet/dhrpox/routing/allocation.txt","w+")
    # for s in range(num_switch):
    #     for l in range(num_link):
    #         f.write(str(allocation[s][l]))
    #         f.write(" ")
    #     f.write("\n")
    # f.close()

    # the allocation sum on the same link, get the total traffic on a link
    # for l in range(num_link):
    #    tr = 0
    #    for sw in range(num_switch):
    #        tr += allocation[sw][l]
    #    result = tr / mlu
    #    print tr," "

if __name__ == "__main__":
    main()

