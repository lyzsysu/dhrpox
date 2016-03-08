#!/usr/bin/python

import os
usr_home = os.path.expanduser('~')

import sys
sys.path.append(usr_home + "/dhrpox/topology")
sys.path.append(usr_home + "/dhrpox/routing")
sys.path.append(usr_home + "/dhrpox/traffic")

from readlink import *
from readtraffic import *
from destination_based_routing import *

import cplex

def _buildmodel(prob, tm, links, capacity, utilization_optimal):

    '''
        build the model for the robust_static_routing
    '''

    
    sufficiently_small_number = 0.000001

    prob.objective.set_sense(prob.objective.sense.minimize)

    num_matrix = len(tm)
    num_switch = len(tm[0])
    num_link = len(links)
    num_pair = (num_switch - 1) * (num_switch - 1)

    obj = [sufficiently_small_number] * (num_pair * num_link + 1)
    colnames = [""] * (num_pair * num_link + 1)
    rmatind = [0] * (num_pair * num_link + 1)
    rmatval = [0] * (num_pair * num_link + 1)
    obj[num_pair * num_link] = 1

    for s in range(num_pair):
        for l in range(num_link):
            colnames[s * num_link + l] = ("a%d_%d" % (s, l))
    colnames[num_pair * num_link] = "Performance"

    prob.variables.add(obj = obj, names = colnames)
    last_column = prob.variables.get_num() - 1

    for m in range(num_matrix):
        for l in range(num_link):
            #(fst, sec) = links[l]
            s = 0
            for src in range(num_switch):
                for dst in range(num_switch):
                    if src != dst:
                        rmatind[s] = s * num_link + l
                        rmatval[s] = tm[m][src][dst]
                        s = s + 1

            rmatind[(num_switch - 1) * (num_switch - 1)] = last_column
            rmatval[(num_switch - 1) * (num_switch - 1)] = \
                     -capacity[l] * utilization_optimal[m]

            rhs = [0]

            prob.linear_constraints.add(lin_expr = \
                     [[rmatind[:(num_switch - 1) * (num_switch - 1) + 1],\
                       rmatval[:(num_switch - 1) * (num_switch - 1) + 1]]],\
                       senses = "L", rhs = rhs)

    s = 0
    for src in range(num_switch):
        for dst in range(num_switch):
            if src != dst:
                continue
            for k in range(num_switch):
                count = 0
                for l in range(num_link):
                    (fst, sec) = links[l]
                    if k == fst - 1:
                        rmatind[count] = s * num_link + l
                        rmatval[count] = -1.0
                        count = count + 1
                    elif k == sec - 1:
                        rmatind[count] = s * num_link + l
                        rmatval[count] = 1.0
                        count = count + 1
                if k == src:
                    rhs = [-1.0]
                    prob.linear_constraints.add(lin_expr = [[rmatind[:count],
                                                        rmatval[:count]]],
                                            senses = "E", rhs = rhs)
                elif k == dst:
                    rhs = [1.0]
                    prob.linear_constraints.add(lin_expr = [[rmatind[:count],
                                                        rmatval[:count]]],
                                            senses = "E", rhs = rhs)
                else:
                    rhs = [0.0]
                    prob.linear_constraints.add(lin_expr = [[rmatind[:count],
                                                        rmatval[:count]]],
                                            senses = "E", rhs = rhs)
            s = s + 1

def robust_static_routing(tm, links, capacity, utilization_optimal):

    '''
        implement the robust_static_routing as comparasion
    '''

    prob = cplex.Cplex()

    # sys.stdout is the default output stream for log and results
    # so these lines may be omitted
    #prob.set_results_stream("/dev/null")
    #prob.set_log_stream("/dev/null")

    prob.set_results_stream(sys.stdout)
    prob.set_log_stream(sys.stdout)

    ic_handle = _buildmodel(prob, tm, links, capacity, utilization_optimal)

    prob.solve()

    sol = prob.solution

    x = sol.get_values(0, num_link * num_pair)

    performance = x[num_link * num_pair]

    robust_static_allocation = [[0 for col in range(num_link)]for row in range(num_pair)]

    for p in range(num_pair):
        for l in range(num_link):
            robust_static_allocation[p][l] = float(x[p * num_link + l])

    return performance, robust_static_allocation

if __name__ == "__main__":

    num_matrix = 12

    links, capacity, num_link, num_switch = read_link(usr_home + "/dhrpox/topology/abilene.txt")

    tm = read_traffic(usr_home + "/dhrpox/traffic/1TM.txt", num_matrix, num_switch)

    utilization_optimal = [0] * num_matrix

    for t in range(num_matrix):
        utilization_optimal[t], ignore = destination_based_routing(tm[t], links, capacity)

    robust_static_routing(tm, links, capacity, utilization_optimal)

