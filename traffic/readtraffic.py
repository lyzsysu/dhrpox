#!/usr/bin/python

import sys
import os

import cplex

NUMSWITCH = 12
NUMMATRIX = 288

def read_traffic(filename):

    traffic_matrix = [[[0.0 for col in range(NUMSWITCH)]for row in range(NUMSWITCH)]for row in range(NUMMATRIX)]

    f = open(filename)
    line = f.readline()

    matrix_num = 0
    while line:
        src = 0
        dst = 0
        for word in line.split(" "):
            if word == "\n":
                break
            traffic_matrix[matrix_num][src][dst] = int(float(word) / 3000.0)
            dst = dst + 1
            if dst == 12:
                src = src + 1
                dst = 0
        matrix_num = matrix_num + 1
        line = f.readline()
    f.close()

    return traffic_matrix

def get_basic_tm(traffic_matrix, tm_num):

    basic_traffic_matrix = [[0.0 for col in range(NUMSWITCH)]for row in range(NUMSWITCH)]
    
    for s in range(NUMSWITCH):
        for d in range(NUMSWITCH):
            max_traffic = 0
            for m in range(tm_num):
                max_traffic = max(max_traffic, traffic_matrix[m][s][d])
            basic_traffic_matrix[s][d] = max_traffic 

    return basic_traffic_matrix

if __name__ == "__main__":

    traffic_matrix = [[[0 for col in range(NUMSWITCH)]for row in range(NUMSWITCH)]for row in range(NUMMATRIX)]

    basic_traffic_matrix = [[0 for col in range(NUMSWITCH)]for row in range(NUMSWITCH)]

    path = os.path.expanduser('~') + "/dhrpox/traffic/2014_06_24TM"

    traffic_matrix = read_traffic(path)

    basic_traffic_matrix = get_basic_tm(traffic_matrix, len(traffic_matrix))

    # show all traffic matrixs
    for m in range(0, 1):
        for s in range(NUMSWITCH):
            for d in range(NUMSWITCH):
                print ("%d" % traffic_matrix[m][s][d]),
            print
        print

    # show the basic traffic matrix
    #for s in range(NUMSWITCH):
    #    for d in range(NUMSWITCH):
    #        print ("%f " % basic_traffic_matrix[s][d]),
    #    print
