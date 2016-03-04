#!/usr/bin/python

import os
usr_home = os.path.expanduser('~')

import sys
sys.path.append(usr_home + "/dhrpox/topology")

# solve the recursive problem
sys.setrecursionlimit(100000)

from readlink import read_link

NUMLINK = 30
NUMSWITCH = 12

path = [[[] for col in range(NUMSWITCH)]for row in range(NUMSWITCH)]

def allocation_2_fraction(filename):

    fraction = [[0 for col in range(NUMLINK)]for row in range(NUMSWITCH)]

    allocation  = [[0 for col in range(NUMLINK)]for row in range(NUMSWITCH)]

    destination = 0

    f = open(filename)
    line = f.readline()
    while line:
        link = 0
        for word in line.split(" "):
            if word == "\n":
                break
            allocation[destination][link] = int(word)
            link = link + 1
        destination = destination + 1
        line = f.readline()
    f.close()
    
    # calculating the corresponding destination-based routing fractions
    for dst in range(NUMSWITCH):
        for l in links:
            (i, j) = links[l]
            traffic_sum = 0.0
            for out_link in links:
                (out, unuse) = links[out_link] 
                if out == i:
                    traffic_sum = traffic_sum + allocation[dst][out_link]
            if traffic_sum == 0:
                fraction[dst][l] = 0
            else:
                fraction[dst][l] = allocation[dst][l] / traffic_sum
            #print allocation[dst][l]," ",traffic_sum," ",fraction[dst][l]
    return fraction

def fraction_2_path():
    for dst in range(NUMSWITCH):
    # dst + 1 is the actual switch num range(1,13), dst range(0,12)
        tmp_path = str(dst + 1)
        tmp_percent = 1.0 
        search_path(dst, dst + 1, tmp_path, tmp_percent)

def search_path(dst, tmp_next_node, tmp_path, tmp_percent):
    for l in links:
        (node, next_node) = links[l]
        # dst + 1 is the actual switch num range(1,13), dst range(0,12)
        if next_node == tmp_next_node and fraction[dst][l] != 0.0:
            prev_path = tmp_path
            prev_percent = tmp_percent
            tmp_path = str(node) + "-" + tmp_path
            tmp_percent = tmp_percent * fraction[dst][l]
            # search node as the next_node :  x -> node -> next_node
            search_path(dst, node, tmp_path, tmp_percent)
            # append the path that towards the dst from this node 
            # and its percentage
            path[node - 1][dst].append(tmp_path + "     " + "%.2f" % (tmp_percent * 100) + "%") 
            tmp_path = prev_path
            tmp_percent = prev_percent

if __name__ == "__main__":

    fraction = [[0 for col in range(NUMLINK)]for row in range(NUMSWITCH)]

    links,ignore = read_link(usr_home + "/dhrpox/topology/abilene.txt")

    fraction = allocation_2_fraction(usr_home + "/dhrpox/routing/allocation.txt")

    fraction_2_path()

    # print the result
    for dst in range(NUMSWITCH):
        for l in links:
            if fraction[dst][l] != 0.0: 
                print links[l]," ",fraction[dst][l]," ",
        print

    # write the final path to the abilene_path.txt
    f = open(usr_home + "/dhrpox/routing/abilene_path.txt","w+")
    for src in range(NUMSWITCH):
        for dst in range(NUMSWITCH):
            if src == dst:
                continue
            f.write("Paths from %d to %d\n" % (src + 1, dst + 1))
            count  = 1
            for p in path[src][dst]:
                f.write("Path %d     " % count)
                f.write("%s" % p)
                f.write("\n")
                count = count + 1
            f.write("\n")
    f.close() 
