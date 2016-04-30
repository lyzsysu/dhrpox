import os
usr_home = os.path.expanduser('~')
project_path = usr_home + "/dhrpox"

import sys
sys.path.append(project_path + "/topology")
sys.path.append(project_path + "/traffic")
sys.path.append(project_path + "/routing")

import random

from readlink import *
from generate_routing_policies import *
from readpath import *
from readtraffic import *

def write_traffic(filename, tm):

    """ Write traffic matrix to filename.
    """

    num_matrix = len(tm)
    num_switch = len(tm[0])

    print num_matrix
    print num_switch

    f = open(filename,'w+')
    for m in range(num_matrix):
        for src in range(num_switch):
            for dst in range(num_switch):
                f.write("%f " % (tm[m][src][dst] * 3000))
        f.write("\n")
    f.close()
    

def oblivious_matrix(tm, num_switch):
    
    """ calculate the matrix for oblivious routing from all tm """

    max_ingress = [0.0] * num_switch
    max_egress = [0.0] * num_switch

    for m in range(0, 288):
        sum_ingress = [0.0] * num_switch
        sum_egress = [0.0] * num_switch
        for s in range(num_switch):
            for d in range(num_switch):
                if s == d:
                    continue
                sum_ingress[s] += tm[m][s][d]
                sum_egress[d] += tm[m][s][d]
        for s in range(num_switch):
            if sum_ingress[s] > max_ingress[s]:
                max_ingress[s] = sum_ingress[s]
            if sum_egress[s] > max_egress[s]:
                max_egress[s] = sum_egress[s]

    #for s in range(num_switch):
    #    print max_ingress[s], max_egress[s]
    return max_ingress, max_egress


def generate_random_element(max_value):

    """ generate random tm's element in range of basic tm's corresponding maximum
        the value of element should retain 8 significant digits """

    a = random.uniform(0.0, max_value)
    #a = random.uniform(a , max_value)
    a = ("%.7e" % a)
    s = float(a)*1.1
    
    return s


def generate_random_tm(max_in, max_eg, basic_traffic_matrix, num_switch, num_tm):
    new_tm = [[[0.0 for s in range(num_switch)] 
                    for d in range(num_switch)] 
                    for m in range(num_tm)]
    tmp_tm = [[0.0 for s in range(num_switch)]
                   for d in range(num_switch)]

    m = 0
    # tm's sum of ingress/egress != max
    while(m < num_tm):
        sum_ingress = [0.0] * num_switch
        sum_egress = [0.0] * num_switch
        delta = [0.0] * num_switch
        flag = 0
        for s in range(num_switch):
            for d in range(num_switch):
                tmp_tm[s][d] = generate_random_element(basic_traffic_matrix[s][d])
                if s == d:
                    continue
                sum_ingress[s] += tmp_tm[s][d]
                sum_egress[d] += tmp_tm[s][d]

            # "flag = 1" means that there exists one sum of ingress traffic vloume
            # has exceeded the maximum of oblivious routing, so give up this tm
            if sum_ingress[s] > max_in[s]:
                flag = 1
                break
            delta[s] = max_in[s] - sum_ingress[s]
        if flag == 1:
            continue
        
        # "flag = 1" means that there exists one sum of egress traffic vloume has
        # exceeded the maximum of oblivious routing, so give up this tm
        
        for d in range(num_switch):
            if sum_egress[d] > max_eg[d]:
                flag = 1
                break
            if sum_egress == 0:
                flag = 2
                break

        if flag != 0:
            continue

        # the tm meets the requirement, so keep it
        for s in range(num_switch):
            for d in range(num_switch):
                new_tm[m][s][d] = tmp_tm[s][d]

        m += 1
        
    return new_tm

    # tm's sum of ingress/egress == max
    # while(i < 2*num_tm):

def main():

    num_matrix = 288
    num_random_tm = 10
    
    link_file = project_path + "/topology/abilene.txt"
    link, capacity, num_switch, num_link = read_link(link_file)

    tm_file = project_path + "/traffic/288TM"
    tm = read_traffic(tm_file, num_matrix, num_switch)
   
    basic_traffic_matrix = get_basic_tm(tm, num_switch)
 
    max_ingress, max_egress = oblivious_matrix(tm, num_switch)
    #print max_ingress,max_egress
    
    new_tm = generate_random_tm(max_ingress, max_egress, basic_traffic_matrix, num_switch, num_random_tm)

    output_file = project_path + "/traffic/10random"
    write_traffic(output_file, new_tm)
    print new_tm
    random_tm = read_traffic(output_file, num_random_tm, num_switch)
    print random_tm

if __name__ == "__main__":
    main()
