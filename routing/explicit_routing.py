#!/usr/bin/python
# Filename: explicit_routing.py

import os
usr_home = os.path.expanduser('~')

import sys
sys.path.append(usr_home + "/dhrpox/topology")
sys.path.append(usr_home + "/dhrpox/traffic")
sys.path.append(usr_home + "/dhrpox/routing")

from readlink import *
from readtraffic import *
from basic_routing import *
from util import *

import cplex

SMALL = 0.000001
MAX = 100000000

def build_model(prob, selected_node_pair, tm, link, 
                capacity, opt_utilization, background_load):

    """ build the model for the explicit path routing """
    
    num_pair = len(selected_node_pair)
    num_matrix = len(tm)
    num_switch = len(tm[0])
    num_link = len(link)

    prob.objective.set_sense(prob.objective.sense.minimize)

    obj = [SMALL] * (num_pair * num_link + 1)
    colnames = [""] * (num_pair * num_link + 1)
    rmatind = [0] * (num_pair * num_link + 1)
    rmatval = [0] * (num_pair * num_link + 1)
    obj[num_pair * num_link] = 1

    # give each variable a name
    for p in range(num_pair):
        for l in range(num_link):
            colnames[p * num_link + l] = ("a%d_%d" % (p, l)) 
    colnames[num_pair * num_link] = "Performance"

    prob.variables.add(obj = obj, names = colnames)

    last_column = prob.variables.get_num() - 1

    # the first constraint:

    # the traffic load on link (i, j) contributed by 
    # explicit routing demands and destination-based routing demands 
    # in each traffic matrix should less than the performance ratio constraint 
    for m in range(num_matrix):
        for l in range(num_link):
            #(fst, sec) = link[l]
            for s in range(num_pair):
                (src, dst) = selected_node_pair[s]
                rmatind[s] = s * num_link + l
                rmatval[s] = tm[m][src][dst]

            rmatind[num_pair] = last_column
            rmatval[num_pair] = -capacity[l] * opt_utilization[m]
            
            rhs = [-background_load[m][l]]
            
            prob.linear_constraints.add(lin_expr = [[rmatind[:num_pair + 1],
                                                     rmatval[:num_pair + 1]]],
                                        senses = "L", rhs = rhs)

    # the second constraint:

    # flow conservation constraint for the selected key node pairs
    for p in range(num_pair):
        (src, dst) = selected_node_pair[p]
        for k in range(num_switch):
            count = 0
            # if link[l] is related to the switch k
            for l in range(num_link):
                (fst, sec) = link[l]
                # when k is the egress switch, minus it
                if k == fst:
                    rmatind[count] = p * num_link + l
                    rmatval[count] = -1.0
                    count = count + 1
                # when k is the ingress switch, plus it
                elif k == sec:
                    rmatind[count] = p * num_link + l
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

def calculate_background_load(m, selected_node_pair, tm, link, path):
    
    """ calculate the background load:
        sum up all the traffic generated by all the node pairs
        on the same link, except the selected_node_pair """

    num_switch = len(tm[0])

    tmp_link_traffic = [[0 for col in range(num_switch)]
                           for row in range(num_switch)]
    link_traffic = {}

    for src in range(num_switch):
        for dst in range(num_switch):
            if (src, dst) in selected_node_pair:
              continue  
            if tm[m][src][dst] != 0:
                for num in range(len(path[src][dst])):
                    route = path[src][dst][num]['route'].split("-")
                    route_len = len(route)
                    percentage = path[src][dst][num]['percent']

                    for i in range(route_len - 1):
                        (fst, sec) = (int(route[i]) - 1, int(route[i + 1]) - 1)
                        tmp_link_traffic[fst][sec] += (tm[m][src][dst] 
                                                       * percentage)

            for l in link:
                (fst, sec) = link[l]
                link_traffic[l] = tmp_link_traffic[fst][sec]

    return link_traffic

def calculate_performance(m, selected_node_pair, tm, link,
                          capacity, path, opt_utilization):

    """ calculate performance """

    # first calculate the background_load

    num_link = len(link)

    link_utilization = {}

    mlu = 0.0

    link_traffic = calculate_background_load(m, selected_node_pair, 
                                             tm, link, path)

    # get the link utilization by traffic / capacity
    # and then compare to the opt_utilization of this matrix
    # to get the performance ratio
    # if the performance ratio is bigger, it means that
    # it is more congested


    # if len(selected_node_pair) != 0:
    #     (src, dst) = selected_node_pair[-1]
    #     print ("the selected pairs ", (src + 1, dst + 1), 
    #            " contribute : ", tm[m][src][dst], "kbytes")

    for l in range(num_link):
        (fst, sec) = link[l]
        link_utilization[l] = link_traffic[l] / capacity[l] 
        # print link_utilization[link]," ",

        if mlu < link_utilization[l]:
            mlu = link_utilization[l]
            most_congested_link = link[l]

    # print ("mlu : %f" % mlu)
    # print (most_congested_link)
 
    performance = mlu / opt_utilization[m]

    return performance, most_congested_link

def select_node_pairs(tm, link, capacity, path, opt_utilization, k):

    """ this function is used to select node_pairs for explicit routing
        k is the number of selecting node pairs """

    num_matrix = len(tm)
    num_switch = len(tm[0])

    selected_node_pair = []

    # calculate the contribution each pair contribute to a link
    contribution = path_2_contribution(path, num_switch)

    # select k node pairs
    while k:
        k -= 1 
        max_performance = 0

        # we have to find out the most congested link
        # in the most congested traffic matrix
        for m in range(num_matrix):
            performance, congested_link = \
            calculate_performance(m, selected_node_pair, tm, link, 
                                  capacity, path, opt_utilization)
            #print performance ,
            if performance > max_performance:
                max_performance = performance
                most_congested_link = congested_link
                most_congested_matrix = m
 
        # for (src, dst) in selected_node_pair:
        #     print (src + 1, dst + 1)
        # print ("the perf is: ", performance, 
        #        " the next cong_link: ", most_congested_link)
        # print

        # find the most congested node pairs which contribute most
        # on the most congested link

        min_performance = MAX
        for (src, dst) in contribution[most_congested_link]:
            if (src, dst) in selected_node_pair:
                continue
            selected_node_pair.append((src, dst))
            performance, congested_link = \
            calculate_performance(most_congested_matrix, selected_node_pair,
                                  tm, link, capacity, path, opt_utilization)
            selected_node_pair.pop()
            # print ("after select out ", (src + 1, dst + 1), 
            #        " the performance:", performance)
            # print   
 
            if performance < min_performance:
                min_performance = performance
                next_selected_node_pair = (src, dst)

        selected_node_pair.append(next_selected_node_pair)

    return selected_node_pair

def explicit_routing(tm, link, capacity, num_selected = 35):

    """ this funciton is used to calculate the explicit_path

        tm is a tm[num_matrix][src][dst] 3_dimension_list
            src range from 0 to num_switch
            dst range from 0 to num_switch

        opt_utilization is a list, range from 0 to num_matrix

        num_selected is the number of selected_node_pair """

    num_matrix = len(tm)
    num_switch = len(tm[0])
    num_link = len(link)

    opt_utilization = [0] * num_matrix

    for t in range(num_matrix):
        opt_utilization[t], ignore = \
        destination_based_routing(tm[t], link, capacity)
   
    basic_tm = get_basic_tm(tm, num_switch)

    mlu, basic_allocation = destination_based_routing(basic_tm, link, capacity)

    path = allocation_2_path(basic_allocation, link, num_switch)

    selected_node_pair = select_node_pairs(tm, link, capacity, path,
                                           opt_utilization, num_selected)

    num_pair = len(selected_node_pair)

    # print "finally selected pairs: ", selected_node_pair
 
    # calculate the background_load
    background_load = [0 for m in range(num_matrix)]

    for m in range(num_matrix):
        background_load[m] = \
        calculate_background_load(m, selected_node_pair, tm, link, path)
    
    # use CPLEX to solve the linear programming problem to get 
    # the allocation of the explicit path routing for the selected
    # node pairs based on the background load and the optimal_utilizations

    # input: utilizaion_optimal, background_load for all matrix
    # output: explicit routing ratios which P is minimized

    prob = cplex.Cplex()

    # sys.stdout is the default output stream for log and results
    # so these lines may be omitted

    prob.set_results_stream("/dev/null")
    prob.set_log_stream("/dev/null")

    # prob.set_results_stream(sys.stdout)
    # prob.set_log_stream(sys.stdout)

    # build the explicit routing problem
    ic_handle = build_model(prob, selected_node_pair, tm,
                            link, capacity, opt_utilization, background_load)

    # the following line can write the lp function to a file
    # prob.write("explicitrouting.lp")

    prob.solve()

    sol = prob.solution

    # print the solution
    # solution.get_status() returns an integer code
    # print "Solution status = ", sol.status[sol.get_status()]
    # print "Solution value = ", sol.get_objective_value()

    # x is the variable in the model
    x = sol.get_values(0, num_link * num_pair)

    # performance is the last variable
    performance = x[num_link * num_pair]

    # calculating the corresponding explicit routing fraction
    explicit_fraction = [[0 for col in range(num_link)]
                            for row in range(num_pair)]

    for p in range(num_pair):
        for l in range(num_link):
            explicit_fraction[p][l] = float(x[p * num_link + l])

    return performance, explicit_fraction, selected_node_pair

def main():

    num_matrix = 288

    link, capacity, num_switch, num_link = \
    read_link(usr_home + "/dhrpox/topology/abilene.txt")

    tm = read_traffic(usr_home + "/dhrpox/traffic/288TM",
                      num_matrix, num_switch)

    tm_tmp = {}

    tm_tmp[0] = tm[0] 

    performance, explicit_fraction, selected_node_pair = \
    explicit_routing(tm_tmp, link, capacity)

    num_pair = len(selected_node_pair)

    for p in range(num_pair):
        for l in range(num_link):
            if explicit_fraction[p][l] != 0.0:
                print link[l], " ", explicit_fraction[p][l], " ",
        print

    path = explicit_fraction_2_path(explicit_fraction, 
                                    selected_node_pair, link)

    for p in path:
        print p

if __name__ == "__main__":
    main()

