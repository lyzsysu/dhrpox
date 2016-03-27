#!/usr/bin/python
# Filename: readpath.py

import os
usr_home = os.path.expanduser('~')

import sys
sys.path.append(usr_home + "/dhrpox/topology")
sys.path.append(usr_home + "/dhrpox/traffic")
sys.path.append(usr_home + "/dhrpox/routing")

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

def read_robust_path(robust_path_file, num_switch):

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
            # print line.split("     ")[1], line.split("     ")[2]
            percent = line.split("     ")[2].split("%")[0]
            count = line.split(" ")[1]

            robust_path[src][dst][count] = {}
            robust_path[src][dst][count]['route'] = route
            robust_path[src][dst][count]['percent'] = percent
        line = f.readline()
    f.close()

    return robust_path

def read_dhr_path(dhr_path_file, num_switch, num_cluster):

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

    return dhr_path

def main():

    num_switch = 12

    robust_path_file = (usr_home + "/dhrpox/routing/robust_path.txt")
    robust_path = read_robust_path(robust_path_file, num_switch)

    cluster_file = (usr_home + "/dhrpox/routing/clusters_288TM_k_5_p_1.05.txt")
    cluster = read_cluster(cluster_file, num_switch)

    num_cluster = len(cluster)

    dhr_path_file = (usr_home + "/dhrpox/routing/dhr_path.txt")
    dhr_path = read_dhr_path(dhr_path_file, num_switch, num_cluster)

    # show the robust path result
    # for src in range(num_switch):
    #     for dst in range(num_switch):
    #         if src == dst:
    #             continue
    #         for p in robust_path[src][dst]:
    #             print (robust_path[src][dst][p]['route'],
    #                    robust_path[src][dst][p]['percent'])

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

if __name__ == "__main__":
    main()
