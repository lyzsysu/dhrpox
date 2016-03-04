#!/usr/bin/python

from __future__ import print_function

import os
usr_home = os.path.expanduser('~')

import sys
sys.path.append(usr_home + "/dhrpox/topology")
sys.path.append(usr_home + "/dhrpox/traffic")
from readlink import read_link
from readtraffic import read_traffic
from readtraffic import get_basic_tm

import cplex

# global variable
NUMMATRIX = 288
NUMSWITCH = 12
NUMLINK = 30

def _buildmodel(prob, tm, links, capacity):

    '''
        build the model for the destination based routing
    '''
 
    sufficiently_small_number = 0.000001

    prob.objective.set_sense(prob.objective.sense.minimize)

    obj = [sufficiently_small_number] * (NUMSWITCH * NUMLINK + 1)
    colnames = [""] * (NUMSWITCH * NUMLINK + 1)
    rmatind = [0] * (NUMSWITCH * NUMLINK + 1)
    rmatval = [0] * (NUMSWITCH * NUMLINK + 1)
    obj[NUMSWITCH * NUMLINK] = 1

    for d in range(NUMSWITCH):
        for l in range(NUMLINK):
            colnames[d * NUMLINK + l] = ("y%d_%d" % (d, l))
    colnames[NUMLINK * NUMSWITCH] = "MLU"

    prob.variables.add(obj = obj, names = colnames)
    last_column = prob.variables.get_num() - 1

    for l in range(NUMLINK):
        #(fst, sec) = links[l]
        for d in range(NUMSWITCH):
            rmatind[d] = varindex(d, l)
            rmatval[d] = 1.0
        rmatind[NUMSWITCH] = last_column
        rmatval[NUMSWITCH] = -capacity[l]
        rhs = [0.0]
        prob.linear_constraints.add(lin_expr = [[rmatind[:NUMSWITCH + 1],
                                                 rmatval[:NUMSWITCH + 1]]],
                                    senses = "L", rhs = rhs)

    for dst in range(NUMSWITCH):
        for k in range(NUMSWITCH):
            count = 0
            for l in range(NUMLINK):
                (fst, sec) = links[l]
                if k == fst - 1:
                    rmatind[count] = varindex(dst, l)
                    rmatval[count] = -1.0
                    count = count + 1
                elif k == sec - 1:
                    rmatind[count] = varindex(dst, l)
                    rmatval[count] = 1.0
                    count = count + 1
            if k == dst:
                traffic_sum = 0
                for n in range(NUMSWITCH):
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

def varindex(destination, link_num):
    return destination * NUMLINK + link_num

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

    fraction = [[0 for col in range(NUMLINK)]for row in range(NUMSWITCH)]

    for dst in range(NUMSWITCH):
        for l in range(NUMLINK):
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

    #f = open("/home/mininet/dhrpox/routing/fraction.txt","w+")
    #for s in range(NUMSWITCH):
    #    for l in range(NUMLINK):
    #        f.write(str(fraction[s][l]))
    #        f.write(" ")
    #    f.write("\n")
    #f.close()
    
    return fraction

def fraction_2_path(fraction, links):

    '''
        calculating the path and it's percent
    '''

    paths = [[[] for col in range(NUMSWITCH)]for row in range(NUMSWITCH)]

    for dst in range(NUMSWITCH):
    # dst + 1 is the actual switch num range(1,13), dst range(0,12)
        tmp_path = str(dst + 1)
        tmp_percent = 1.0
        search_path(dst, dst + 1, tmp_path, tmp_percent, fraction, links, paths)

    # write the final path to the abilene_path.txt
    #f = open(usr_home + "/dhrpox/routing/abilene_path.txt","w+")
    #for src in range(NUMSWITCH):
    #    for dst in range(NUMSWITCH):
    #        if src == dst:
    #            continue
    #        f.write("Paths from %d to %d\n" % (src + 1, dst + 1))
    #        count  = 1
    #        for p in paths[src][dst]:
    #            f.write("Path %d     " % count)
    #            f.write("%s" % p)
    #            f.write("\n")
    #            count = count + 1
    #        f.write("\n")
    #f.close()

    return paths

def destination_based_routing(tm, links, capacity):

    ''' 
        this function is used to calculate the MLU and 
        the traffic_allocation on each link
        it returns the MLU and the fraction

        tm is a tm[num_matrix][src][dst] 3_dimension_list
            num_matrix range from 0 to NUMMATRIX
            src range from 0 to NUMSWITCH
            dst range from 0 to NUMSWITCH

        links is a dict link[l] = (i, j)
            l range from 0 to NUMLINK

        capacity is a dict capacity[l] = kbps
    '''


    prob = cplex.Cplex()

    # sys.stdout is the default output stream for log and results
    # so these lines may be omitted
    prob.set_results_stream("/dev/null")
    prob.set_log_stream("/dev/null")

    ic_handle = _buildmodel(prob, tm, links, capacity)

    #prob.write("basicrouting.lp")

    prob.solve()

    sol = prob.solution

    #print()
    # solution.get_status() returns an integer code
    #print("Solution status = ", sol.get_status(), ":", end = ' ') 
    
    #print(sol.status[sol.get_status()])
    #print("Solution value = ", sol.get_objective_value())

    x = sol.get_values(0, NUMSWITCH * NUMLINK)

    MLU = x[NUMSWITCH * NUMLINK]

    #print("MLU = ", MLU)

    allocation = [[0 for col in range(NUMLINK)]for row in range(NUMSWITCH)]
    
    '''
        calculating the corresponding destination-based routing allocation
    '''

    for s in range(NUMSWITCH):
        for l in range(NUMLINK):
            allocation[s][l] = float(x[varindex(s, l)])
    
    #print("CPLEX's traffic")
    #for l in range(NUMLINK):
    #    tr = 0
    #    for sw in range(NUMSWITCH):
    #        tr += allocation[sw][l]
    #    result = tr / MLU 
    #    print(tr, end=' ')

    f = open("/home/mininet/dhrpox/routing/allocation.txt","w+")
    for s in range(NUMSWITCH):
        for l in range(NUMLINK):
            f.write(str(allocation[s][l]))
            f.write(" ")
        f.write("\n")
    f.write(str(float(x[360])))
    f.close()
 
    return MLU, allocation

if __name__ == "__main__":

    traffic_matrix = read_traffic(usr_home + "/dhrpox/traffic/2014_06_24TM")

    basic_traffic_matrix = get_basic_tm(traffic_matrix, NUMMATRIX)

    links, capacity = read_link(usr_home + "/dhrpox/topology/abilene.txt")

    MLU, allocation = destination_based_routing(basic_traffic_matrix, links, capacity)

    fraction = allocation_2_fraction(allocation, links)

    paths = fraction_2_path(fraction, links)

    # print the result of fraction
    #for dst in range(NUMSWITCH):
    #    for l in links:
    #        if fraction[dst][l] != 0.0:
    #            print ("%s %f " % (links[l], fraction[dst][l]))
    #    print ()

