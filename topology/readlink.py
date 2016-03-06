#!/usr/bin/python

import sys
import os

def read_link(filename):

    links = {}
    capacity = {}
    f = open(filename)
    line = f.readline()
    while line:
        if line.split(" ")[0] == "#": # this line is comment
            pass
        elif line.split(" ")[0] == "NUMSWITCH":
            num_switch = int(line.split(" ")[1])
        elif line.split(" ")[0] == "NUMLINK":
            num_link = int(line.split(" ")[1])
        else:
            link_num = int(line.split(" ")[2])
            link_capacity = int(line.split(" ")[3])
            links[link_num - 1] = \
            (int(line.split(" ")[0]), int(line.split(" ")[1]))
            capacity[link_num - 1] = link_capacity * 10
            # the unit of capacity is Mbps
        line = f.readline()
    f.close()
    return links, capacity, num_link, num_switch

if __name__ == "__main__":

    path = os.path.realpath("../topology/abilene.txt")

    links, capacity, num_link, num_switch = read_link(path)

    for l in links:
        print links[l]
        print capacity[l]
