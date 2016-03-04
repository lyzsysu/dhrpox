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
            NUMSWITCH = int(line.split(" ")[1])
        elif line.split(" ")[0] == "NUMLINK":
            NUMLINK = int(line.split(" ")[1])
        else:
            link_num = int(line.split(" ")[2])
            link_capacity = int(line.split(" ")[3])
            links[link_num - 1] = \
            (int(line.split(" ")[0]), int(line.split(" ")[1]))
            capacity[link_num - 1] = link_capacity * 10
            # the unit of capacity is kbps
        line = f.readline()
    f.close()
    return links, capacity

if __name__ == "__main__":

    path = os.path.realpath("../topology/abilene.txt")

    links,capacity = read_link(path)

    for l in capacity:
        print capacity[l]

    for l in links:
        print links[l]
        print capacity[l]
