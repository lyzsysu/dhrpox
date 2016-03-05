#!/usr/bin/python

import sys
import os

def read_traffic(filename, num_matrix, num_switch):

    traffic_matrix = [[[0.0 for col in range(num_switch)]for row in range(num_switch)]for row in range(num_matrix)]

    f = open(filename)
    line = f.readline()

    num = 0
    while line:
        src = 0
        dst = 0
        for data in line.split(" "):
            if data == "\n":
                break
            traffic_matrix[num][src][dst] = int(float(data) / 3000.0)
            dst = dst + 1
            if dst == 12:
                src = src + 1
                dst = 0
        num = num + 1
        line = f.readline()
    f.close()

    return traffic_matrix

def get_basic_tm(traffic_matrix, num_matrix, num_switch):

    basic_traffic_matrix = [[0.0 for col in range(num_switch)]for row in range(num_switch)]
    
    for s in range(num_switch):
        for d in range(num_switch):
            max_traffic = 0
            for m in range(num_matrix):
                max_traffic = max(max_traffic, traffic_matrix[m][s][d])
            basic_traffic_matrix[s][d] = max_traffic 

    return basic_traffic_matrix

if __name__ == "__main__":

    path = os.path.expanduser('~') + "/dhrpox/traffic/2014_06_24TM"

    num_matrix = 288
    num_switch = 12

    traffic_matrix = read_traffic(path, num_matrix, num_switch)

    num_matrix = len(traffic_matrix)
    num_switch = len(traffic_matrix[0])

    basic_traffic_matrix = get_basic_tm(traffic_matrix, num_matrix, num_switch)

    # show all traffic matrixs
    for m in range(0, 1):
        for s in range(num_switch):
            for d in range(num_switch):
                print ("%d" % traffic_matrix[m][s][d]),
            print
        print

    # show the basic traffic matrix
    #for s in range(num_switch):
    #    for d in range(num_switch):
    #        print ("%f " % basic_traffic_matrix[s][d]),
    #    print
