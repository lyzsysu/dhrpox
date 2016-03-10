#!/usr/bin/python
# Filename: basic_routing.py

import os
usr_home = os.path.expanduser('~')

import sys
sys.path.append(usr_home + "/dhrpox/topology")
sys.path.append(usr_home + "/dhrpox/traffic")
sys.path.append(usr_home + "/dhrpox/routing")

from readlink import *
from readtraffic import *
from util import *

import cplex

SMALL = 0.000001

def build_model(prob, tm, link, capacity):

    """ build the model for the destination based routing """

    num_link = len(link)
    num_switch = len(tm)
 
    prob.objective.set_sense(prob.objective.sense.minimize)

    obj = [SMALL] * (num_switch * num_link + 1)
    colnames = [""] * (num_switch * num_link + 1)
    rmatind = [0] * (num_switch * num_link + 1)
    rmatval = [0] * (num_switch * num_link + 1)
    obj[num_switch * num_link] = 1

    # give each variable a name 
    for d in range(num_switch):
        for l in range(num_link):
            colnames[d * num_link + l] = ("y%d_%d" % (d, l))
    colnames[num_link * num_switch] = "MLU"

    prob.variables.add(obj = obj, names = colnames)

    last_column = prob.variables.get_num() - 1

    # the first constraint: link capacity utilization constraint
    for l in range(num_link):
        #(fst, sec) = link[l]
        for d in range(num_switch):
            rmatind[d] = d * num_link + l
            rmatval[d] = 1.0
        rmatind[num_switch] = last_column
        rmatval[num_switch] = -capacity[l]
        rhs = [0.0]
        prob.linear_constraints.add(lin_expr = [[rmatind[:num_switch + 1],
                                                 rmatval[:num_switch + 1]]],
                                    senses = "L", rhs = rhs)

    # the second constraint: flow conservation constraint.
    for d in range(num_switch):
        for k in range(num_switch):
            count = 0
            # if link[l] is related to the switch k
            for l in range(num_link):
                (fst, sec) = link[l]
                # when k is the egress switch, minus it
                if k == fst:
                    rmatind[count] = d * num_link + l
                    rmatval[count] = -1.0
                    count = count + 1
                # when k is the ingress switch, plus it
                elif k == sec:
                    rmatind[count] = d * num_link + l
                    rmatval[count] = 1.0
                    count = count + 1
            # if k is the destination switch
            if k == d:
                Sum = 0
                for n in range(num_switch):
                    if n == d:
                        continue
                    Sum += tm[n][d]
                prob.linear_constraints.add(lin_expr = [[rmatind[:count],
                                                         rmatval[:count]]],
                                            senses = "E", rhs = [Sum])
            # if k is only a pass-by switch
            else:
                rhs = [-tm[k][d]]
                prob.linear_constraints.add(lin_expr = [[rmatind[:count],
                                                         rmatval[:count]]],
                                            senses = "E", rhs = rhs)

def destination_based_routing(tm, link, capacity):

    """ this function is used to calculate the maximum link utilization
        and the traffic allocation """

    num_link = len(link)
    num_switch = len(tm) 

    prob = cplex.Cplex()

    # sys.stdout is the default output stream for log and results
    # so these lines may be omitted

    prob.set_results_stream("/dev/null")
    prob.set_log_stream("/dev/null")

    # build the destination-based routing problem
    ic_handle = build_model(prob, tm, link, capacity)

    # the following line can write the lp function to a file
    # prob.write("basicrouting.lp")

    prob.solve()

    sol = prob.solution

    # print the solution
    # print
    # solution.get_status() returns an integer code
    # print "Solution status = ", sol.get_status(), ": "
    
    # print sol.status[sol.get_status()]
    # print "Solution value = ", sol.get_objective_value()

    # x is the variable in the model
    x = sol.get_values(0, num_switch * num_link)
    
    # mlu is the last variable
    mlu = x[num_switch * num_link]

    # print "mlu = ", mlu

    # calculating the corresponding destination-based routing allocation
    allocation = [[0 for col in range(num_link)]for row in range(num_switch)]

    for s in range(num_switch):
        for l in range(num_link):
            allocation[s][l] = float(x[s * num_link + l])
    
    return mlu, allocation

def main():

    num_matrix = 288

    link, capacity, num_switch, num_link = \
    read_link("/home/mininet/dhrpox/topology/abilene.txt")

    tm = read_traffic("/home/mininet/dhrpox/traffic/288TM",
                      num_matrix, num_switch)

    basic_tm = get_basic_tm(tm, num_switch)

    mlu, allocation = destination_based_routing(basic_tm, link, capacity)

    path = allocation_2_path(allocation, link, num_switch)

    # write the destination-based routing path to the basic_path.txt
    f = open(usr_home + "/dhrpox/routing/basic_path.txt","w+")
    for src in range(num_switch):
        for dst in range(num_switch):
            if src == dst:
                continue
            f.write("Paths from %d to %d\n" % (src + 1, dst + 1))
            count  = 1
            for p in path[src][dst]:
                f.write("Path %d     " % count)
                f.write("%s" % path[src][dst][p]['route'])
                f.write("     ")
                f.write("%f" % (path[src][dst][p]['percent'] * 100))
                f.write("% ")
                f.write("\n")
                count = count + 1
            f.write("\n")
    f.close()

if __name__ == "__main__":
    main()
