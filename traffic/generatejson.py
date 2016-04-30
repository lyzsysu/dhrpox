#!/usr/bin/python
# Filename: generatejson.py

import os
usr_home = os.path.expanduser('~')

import sys

from readtraffic import *

def generate_json(filename, tm):

    """ Generate traffic json by tm and save into a file called *.json
    """

    num_switch = len(tm)

    f = open(filename,"w+")
    f.write("{")
    s_count = 0
    for s in range(num_switch):
        f.write("\"%d\": {" % s)
        d_count = 0
        for d in range(num_switch):
            if s == d:
                continue
            if d_count == 10:
                f.write("\"%d\": %d" % (d, tm[s][d]))
            else:
                f.write("\"%d\": %d, " % (d, tm[s][d]))
            d_count += 1
        if s_count == 11:
            f.write("}\n")
        else:
            f.write("},\n")
        s_count += 1
    f.write("}")
    f.close()

def main():

    num_matrix = 288
    num_switch = 12

    traffile = usr_home + "/dhrpox/traffic/288TM"
    tm = read_traffic(traffile, num_matrix, num_switch)

    for i in range(0,10):    
        outfile = usr_home + "/dhrpox/traffic/TM" + str(i) + ".json"
        generate_json(outfile, tm[i * 28])
        
if __name__ == "__main__":
    main()
