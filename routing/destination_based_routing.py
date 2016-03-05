#!/usr/bin/python

from __future__ import print_function

import os
usr_home = os.path.expanduser('~')

import sys
sys.path.append(usr_home + "/dhrpox/topology")
sys.path.append(usr_home + "/dhrpox/traffic")
from readlink import read_link
from readtraffic import *

import cplex

def _buildmodel(prob, tm, links, capacity, num_link, num_switch):

    '''
        build the model for the destination based routing
    '''
 
    sufficiently_small_number = 0.000001

    prob.objective.set_sense(prob.objective.sense.minimize)

    obj = [sufficiently_small_number] * (num_switch * num_link + 1)
    colnames = [""] * (num_switch * num_link + 1)
    rmatind = [0] * (num_switch * num_link + 1)
    rmatval = [0] * (num_switch * num_link + 1)
    obj[num_switch * num_link] = 1

    for d in range(num_switch):
        for l in range(num_link):
            colnames[d * num_link + l] = ("y%d_%d" % (d, l))
    colnames[num_link * num_switch] = "MLU"

    prob.variables.add(obj = obj, names = colnames)
    last_column = prob.variables.get_num() - 1

    for l in range(num_link):
        #(fst, sec) = links[l]
        for d in range(num_switch):
            rmatind[d] = d * num_link + l
            rmatval[d] = 1.0
        rmatind[num_switch] = last_column
        rmatval[num_switch] = -capacity[l]
        rhs = [0.0]
        prob.linear_constraints.add(lin_expr = [[rmatind[:num_switch + 1],
                                                 rmatval[:num_switch + 1]]],
                                    senses = "L", rhs = rhs)

    for dst in range(num_switch):
        for k in range(num_switch):
            count = 0
            for l in range(num_link):
                (fst, sec) = links[l]
                if k == fst - 1:
                    rmatind[count] = dst * num_link + l
                    rmatval[count] = -1.0
                    count = count + 1
                elif k == sec - 1:
                    rmatind[count] = dst * num_link + l
                    rmatval[count] = 1.0
                    count = count + 1
            if k == dst:
                traffic_sum = 0
                for n in range(num_switch):
                    if n == dst:
                        continue
                    traffic_sum = traffic_sum + tm[n][dst]
                prob.linear_constraints.add(lin_expr = [[rmatind[:count],
                                                    rmatval[:count]]],
                                        senses = "E", rhs = [traffic_sum])
            else:
                rhs = [-tm[k][dst]]
                prob.linear_constraints.add(lin_expr = [[rmatind[:count],
                                                         rmatval[:count]]],
                                            senses = "E", rhs = rhs)

def search_path(dst, tmp_next_node, tmp_path, tmp_percent, fraction, links, paths):

    '''
        deep first search for the path from a switch to another
    '''

    for l in links:
        (node, next_node) = links[l]
        # dst + 1 is the actual switch num range(1,13), dst range(0,12)
        if next_node == tmp_next_node and fraction[dst][l] != 0.0:
            prev_path = tmp_path
            prev_percent = tmp_percent
            tmp_path = str(node) + "-" + tmp_path
            tmp_percent = tmp_percent * fraction[dst][l]
            # search node as the next_node :  x -> node -> next_node
            search_path(dst, node, tmp_path, tmp_percent, fraction, links, paths)
            # append the path that towards the dst from this node
            # and its percentage
            paths[node - 1][dst].append(tmp_path + "     " + "%.2f" % (tmp_percent * 100) + "%")
            tmp_path = prev_path
            tmp_percent = prev_percent

def allocation_2_fraction(allocation, links):

    '''
        calculating the corresponding destination-based routing fractions
    '''

    num_link = len(links)
    num_switch = len(allocation)

    fraction = [[0 for col in range(num_link)]for row in range(num_switch)]

    for dst in range(num_switch):
        for l in range(num_link):
            (i, j) = links[l]
            traffic_sum = 0.0
            for out_link in links:
                (out, unuse) = links[out_link]
                if out == i:
                    traffic_sum = traffic_sum + allocation[dst][out_link]
            if traffic_sum == 0:
                fraction[dst][l] = 0
            else:
                fraction[dst][l] = allocation[dst][l] / traffic_sum

    return fraction

def fraction_2_path(fraction, links):

    '''
        calculating the path and it's percent
    '''

    num_switch = len(fraction)

    paths = [[[] for col in range(num_switch)]for row in range(num_switch)]

    for dst in range(num_switch):
    # dst + 1 is the actual switch num range(1,13), dst range(0,12)
        tmp_path = str(dst + 1)
        tmp_percent = 1.0
        search_path(dst, dst + 1, tmp_path, tmp_percent, fraction, links, paths)

    return paths

def destination_based_routing(tm, links, capacity):

    ''' 
        this function is used to calculate the MLU and 
        the traffic_allocation on each link
        it returns the MLU and the fraction

        tm is a tm[num_matrix][src][dst] 3_dimension_list
            num_matrix range from 0 to num_matrix
            src range from 0 to num_switch
            dst range from 0 to num_switch

        links is a dict link[l] = (i, j)
            l range from 0 to num_link

        capacity is a dict capacity[l] = kbps
    '''

    num_link = len(links)
    num_switch = len(tm) 

    prob = cplex.Cplex()

    # sys.stdout is the default output stream for log and results
    # so these lines may be omitted
    prob.set_results_stream(sys.stdout)
    prob.set_log_stream(sys.stdout)
    #prob.set_results_stream("/dev/null")
    #prob.set_log_stream("/dev/null")

    ic_handle = _buildmodel(prob, tm, links, capacity, num_link, num_switch)

    #prob.write("basicrouting.lp")

    prob.solve()

    sol = prob.solution

    #print()
    # solution.get_status() returns an integer code
    #print("Solution status = ", sol.get_status(), ":", end = ' ') 
    
    #print(sol.status[sol.get_status()])
    #print("Solution value = ", sol.get_objective_value())

    x = sol.get_values(0, num_switch * num_link)

    MLU = x[num_switch * num_link]

    #print("MLU = ", MLU)

    allocation = [[0 for col in range(num_link)]for row in range(num_switch)]
    
    '''
        calculating the corresponding destination-based routing allocation
    '''

    for s in range(num_switch):
        for l in range(num_link):
            allocation[s][l] = float(x[s * num_link + l])
    
    #print("CPLEX's traffic")
    #for l in range(num_link):
    #    tr = 0
    #    for sw in range(num_switch):
    #        tr += allocation[sw][l]
    #    result = tr / MLU 
    #    print(tr, end=' ')

    return MLU, allocation

if __name__ == "__main__":

    num_matrix = 288

    links, capacity, num_link, num_switch = read_link(usr_home + "/dhrpox/topology/abilene.txt")

    traffic_matrix = read_traffic(usr_home + "/dhrpox/traffic/2014_06_24TM", num_matrix, num_switch)

    basic_traffic_matrix = get_basic_tm(traffic_matrix, len(traffic_matrix), num_switch)

    MLU, allocation = destination_based_routing(basic_traffic_matrix, links, capacity)

    #f = open("/home/mininet/dhrpox/routing/allocation.txt","w+")
    #for s in range(num_switch):
    #    for l in range(num_link):
    #        f.write(str(allocation[s][l]))
    #        f.write(" ")
    #    f.write("\n")
    #f.write(str(float(x[360])))
    #f.close()
 
    fraction = allocation_2_fraction(allocation, links)

    #f = open("/home/mininet/dhrpox/routing/fraction.txt","w+")
    #for s in range(num_switch):
    #    for l in range(num_link):
    #        f.write(str(fraction[s][l]))
    #        f.write(" ")
    #    f.write("\n")
    #f.close()
    
    paths = fraction_2_path(fraction, links)

    # write the final path to the abilene_path.txt
    f = open(usr_home + "/dhrpox/path/abilene_path.txt","w+")
    for src in range(num_switch):
        for dst in range(num_switch):
            if src == dst:
                continue
            f.write("Paths from %d to %d\n" % (src + 1, dst + 1))
            count  = 1
            for p in paths[src][dst]:
                f.write("Path %d     " % count)
                f.write("%s" % p)
                f.write("\n")
                count = count + 1
            f.write("\n")
    f.close()

    # print the result of fraction
    #for dst in range(num_switch):
    #    for l in links:
    #        if fraction[dst][l] != 0.0:
    #            print ("%s %f " % (links[l], fraction[dst][l]))
    #    print ()

