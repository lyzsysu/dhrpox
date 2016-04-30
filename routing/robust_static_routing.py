#!/usr/bin/python
# Filename: robust_static_routing.py

import os
usr_home = os.path.expanduser('~')

import sys
sys.path.append(usr_home + "/dhrpox/topology")
sys.path.append(usr_home + "/dhrpox/routing")
sys.path.append(usr_home + "/dhrpox/traffic")

from readlink import *
from readtraffic import *
from util import *

import cplex

SMALL = 0.000001

def build_model(prob, tm, link, capacity, opt_utilization):

    """ Build the model for the robust static routing.
    """

    prob.objective.set_sense(prob.objective.sense.minimize)

    # variable initialization
    num_matrix = len(tm)
    num_switch = len(tm[0])
    num_link = len(link)
    num_pair = (num_switch) * (num_switch - 1)

    obj = [SMALL] * (num_pair * num_link + 1)
    colnames = [""] * (num_pair * num_link + 1)
    rmatind = [0] * (num_pair * num_link + 1)
    rmatval = [0] * (num_pair * num_link + 1)
    obj[num_pair * num_link] = 1

    # give each variable a name
    for s in range(num_pair):
        for l in range(num_link):
            colnames[s * num_link + l] = ("a%d_%d" % (s, l))
    colnames[num_pair * num_link] = "Performance"

    prob.variables.add(obj = obj, names = colnames)

    last_column = prob.variables.get_num() - 1


    # the first constraint:

    # the traffic load on link (i, j) contributed by
    # explicit routing demands and destination-based routing demands
    # in each traffic matrix should less than the performance ratio constraint
    for m in range(num_matrix):
        for l in range(num_link):
            # (fst, sec) = link[l]
            s = 0
            for src in range(num_switch):
                for dst in range(num_switch):
                    if src == dst:
                        continue
                    rmatind[s] = s * num_link + l
                    rmatval[s] = tm[m][src][dst]
                    s = s + 1
            rmatind[num_pair] = last_column
            rmatval[num_pair] = \
                     -capacity[l] * opt_utilization[m]

            rhs = [0]

            prob.linear_constraints.add(lin_expr = \
                     [[rmatind[:num_pair + 1],\
                       rmatval[:num_pair + 1]]],\
                       senses = "L", rhs = rhs)

    # the second constraint:

    # flow conservation constraint for the selected key node pairs
    s = 0
    for src in range(num_switch):
        for dst in range(num_switch):
            if src == dst:
                continue
            for k in range(num_switch):
                count = 0
                # if link[l] is related to the switch k
                for l in range(num_link):
                    (fst, sec) = link[l]
                    # when k is the egress switch, minus it
                    if k == fst:
                        rmatind[count] = s * num_link + l
                        rmatval[count] = -1.0
                        count = count + 1
                    # when k is the ingress switch, plus it
                    elif k == sec:
                        rmatind[count] = s * num_link + l
                        rmatval[count] = 1.0
                        count = count + 1
                # if k is the source switch
                if k == src:
                    rhs = [-1.0]
                    prob.linear_constraints.add(lin_expr = [[rmatind[:count],
                                                        rmatval[:count]]],
                                            senses = "E", rhs = rhs)
                # if k is the destination switch
                elif k == dst:
                    rhs = [1.0]
                    prob.linear_constraints.add(lin_expr = [[rmatind[:count],
                                                        rmatval[:count]]],
                                            senses = "E", rhs = rhs)
                # if k is only a pass-by switch
                else:
                    rhs = [0.0]
                    prob.linear_constraints.add(lin_expr = [[rmatind[:count],
                                                        rmatval[:count]]],
                                            senses = "E", rhs = rhs)
            s = s + 1

def robust_fraction_2_path(fraction, link, num_switch):

    """ Get the explicit path for selected node pairs
        based on the explicit fraction.
    """

    num_pair = (num_switch) * (num_switch - 1)

    path = [{} for p in range(num_pair)]

    p = 0
    for src in range(num_switch):
        for dst in range(num_switch):
            if src == dst:
                continue
            tmp_path = str(dst + 1)
            tmp_percent = 1.0
            egress_switch = dst
            search_explicit_path(p, src, egress_switch, tmp_path,
                                 tmp_percent, fraction, link, path)
            p = p + 1

    return path

def robust_static_routing(tm, link, capacity, opt_utilization):

    """ Implement the robust static routing as comparasion.
    """

    num_link = len(link)
    num_switch = len(tm[0])
    num_pair = (num_switch) * (num_switch - 1)

    prob = cplex.Cplex()

    # sys.stdout is the default output stream for log and results
    # so these lines may be omitted
    
    prob.set_results_stream("/dev/null")
    prob.set_log_stream("/dev/null")

    ic_handle = build_model(prob, tm, link, capacity, opt_utilization)

    # the following line can write the lp function to a file
    # prob.write("robustrouting.lp")

    prob.solve()

    sol = prob.solution

    x = sol.get_values(0, num_link * num_pair)

    performance = x[num_link * num_pair]

    robust_fraction = [[0 for col in range(num_link)]
                          for row in range(num_pair)]

    for p in range(num_pair):
        for l in range(num_link):
            robust_fraction[p][l] = float(x[p * num_link + l])

    return performance, robust_fraction

if __name__ == "__main__":

    num_matrix = 288

    link_file = usr_home + "/dhrpox/topology/abilene.txt"
    link, capacity, num_switch, num_link = read_link(link_file)

    traffic_file = usr_home + "/dhrpox/traffic/288TM"
    tm = read_traffic(traffic_file, num_matrix, num_switch)

    opt_utilization = [0] * num_matrix

    for t in range(num_matrix):
        opt_utilization[t], ignore = \
        destination_based_routing(tm[t], link, capacity)

    performance, robust_fraction = \
    robust_static_routing(tm, link, capacity, opt_utilization)

    print "performance: ", performance

    num_pair = (num_switch) * (num_switch - 1)

    # p = 0
    # for s in range(num_switch):
    #     for d in range(num_switch):
    #         if s == d:
    #             continue
    #         for l in range(num_link):
    #             if robust_fraction[p][l] != 0.0:
    #                 print link[l], " ", robust_fraction[p][l], " ",
    #         print
    #         p = p + 1

    robust_path = robust_fraction_2_path(robust_fraction,
                                         link, num_switch)

    # for p in robust_path:
    #     print p

    output_file = usr_home + "/dhrpox/routing/robust_path.txt"
    f = open(output_file, "w+")
    s = 0
    for src in range(num_switch):
        for dst in range(num_switch):
            if src == dst:
                continue
            f.write("Paths from %d to %d\n" % (src + 1, dst + 1))
            count = 1
            for p in robust_path[s]:
                f.write("Path %d     " % count)
                f.write("%s" % robust_path[s][p]['route'])
                f.write("     ")
                f.write("%f" % (robust_path[s][p]['percent']
                                * 100))
                f.write("% ")
                f.write("\n")
                count = count + 1
            f.write("\n")
            s += 1

