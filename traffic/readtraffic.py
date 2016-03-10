#!/usr/bin/python
# Filename: readtraffic.py

import sys
import os

def read_traffic(filename, num_matrix, num_switch):

    """ read traffic matrix from filename
        tm: list eg: tm[0][src][dst] = 100 """

    tm = [[[0.0 for s in range(num_switch)] 
                for d in range(num_switch)] 
                for m in range(num_matrix)]

    m = 0 # number of matrices

    f = open(filename)
    line = f.readline()
    while line:
        src = dst = 0
        for demand in line.split(" "):
            if demand == "\n":
                break
            # demand is x * 100bytes in 5 minutes,
            # so it has to divide 3000 to byte/sec
            tm[m][src][dst] = float(demand) / 3000
            dst += 1
            if dst == num_switch:
                src += 1
                dst = 0
        m += 1
        line = f.readline()
    f.close()

    return tm

def get_basic_tm(tms, num_switch):

    """ we choose maximum demand volume traffic matrix 
        as the basic traffic matrix """

    basic_traffic_matrix = [[0.0 for col in range(num_switch)]
                                 for row in range(num_switch)]   

    num_matrix = len(tms) 

    for s in range(num_switch):
        for d in range(num_switch):
            Max = 0
            for m in range(num_matrix):
                Max = max(Max, tms[m][s][d])
            basic_traffic_matrix[s][d] = Max

    return basic_traffic_matrix

def main():

    num_matrix = 288
    num_switch = 12

    path = os.path.expanduser('~') + "/dhrpox/traffic/288TM"

    tm = read_traffic(path, num_matrix, num_switch)

    basic_traffic_matrix = get_basic_tm(tm, num_switch)

    # show the sample of traffic matrices eg: tm[0]
    for m in range(0, 1):
        for s in range(num_switch):
            for d in range(num_switch):
                print ("%d" % tm[m][s][d]),
            print
        print

    # show the basic traffic matrix
    for s in range(num_switch):
        for d in range(num_switch):
            print ("%d " % basic_traffic_matrix[s][d]),
        print

if __name__ == "__main__":
    main()
