#!/usr/bin/python
# Filename: readtopology.py

import sys
import os

def read_link(filename):

    """ Read topology from filename.
        link: dict eg: LINK[0] = (0, 1) 
             means the first link is from switch 0 to switch 1

        capacity: dict eg: capacities[0] = 992
    """

    link = {}
    capacity = {}

    f = open(filename)
    line = f.readline()
    while line:
        if line.split(" ")[0] == "#": # this line is comment
            pass
        elif line.split(" ")[0] == "NUM_SWITCH":
            num_switch = int(line.split(" ")[1])
        elif line.split(" ")[0] == "NUM_LINK":
            num_link = int(line.split(" ")[1])
        else: 
            fst = int(line.split(" ")[0]) - 1
            sec = int(line.split(" ")[1]) - 1
            link_id = int(line.split(" ")[2]) - 1
            link_capacity = int(line.split(" ")[3])
            link[link_id] = (fst, sec)
            capacity[link_id] = link_capacity # the unit of capacity is Mbps
        line = f.readline()
    f.close()

    return link, capacity, num_switch, num_link

def main():

    path = os.path.realpath("../topology/abilene.txt")

    link, capacity, num_switch, num_link = read_link(path)

    # print the link and capacity
    for l in link:
        print link[l]
        print capacity[l]

if __name__ == "__main__":
    main()
