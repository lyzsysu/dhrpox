#!/usr/bin/python
# Filename: readcost.py

import os
usr_home = os.path.expanduser('~')

import sys


def read_cost(filename, num_cluster):

    """ read the cost of merging each clusters """

    cost = [[0.0 for col in range(num_cluster)]
                 for row in range(num_cluster)]

    f = open(filename)

    line = f.readline()
    while line:
        fst = int(line.split(" ")[0])
        sec = int(line.split(" ")[1])
        c = float(line.split(" ")[2])
        cost[fst][sec] = c
        line = f.readline()
    f.close()

    return cost

def main():

    num_cluster = 288

    filename = usr_home + "/dhrpox/routing/cost/cost"

    cost = read_cost(filename, num_cluster)

    for fst in range(num_cluster):
        for sec in range(num_cluster):
            print fst," ",sec," ",cost[fst][sec]

if __name__ == "__main__":
    main()
