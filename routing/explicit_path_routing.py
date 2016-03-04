#!/usr/bin/python

from __future__ import division

import os
usr_home = os.path.expanduser('~')

import sys
sys.path.append(usr_home + "/dhrpox/topology")
sys.path.append(usr_home + "/dhrpox/traffic")
sys.path.append(usr_home + "/dhrpox/routing")

from readlink import read_link
from readtraffic import read_traffic
from destination_based_routing_problem import destination_based_routing, get_basic_tm, allocation_2_fraction, fraction_2_path

import cplex

# global variable
NUMMATRIX = 288
NUMSWITCH = 12

def _buildmodel(prob, tm, links, capactity, selected_node_pairs, utilization_optimal, background_load):
    
    '''
        build the model for the explicit routing
    '''

    sufficiently_small_number = 0.000001

    prob.objective.set_sense(prob.objective.sense.minimize)

    num_link = len(links)

    num_pair = len(selected_node_pairs)

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
     
    for m in tm:
        for l in range(num_link):
            #(fst, sec) = links[l]
            for s in range(num_pair):
                (src, dst) = selected_node_pairs[s]
                rmatind[s] = s * num_link + l
                rmatval[s] = tm[m][src][dst]

            rmatind[num_pair] = last_column
            rmatval[num_pair] = \
                     -capacity[l] * utilization_optimal[m]
            
            rhs = [-background_load[m][l]]
            
            prob.linear_constraints.add(lin_expr = \
                     [[rmatind[:num_pair + 1],\
                       rmatval[:num_pair + 1]]],\
                       senses = "L", rhs = rhs)

    for s in range(num_pair):
        (src, dst) = selected_node_pairs[s]
        for k in range(NUMSWITCH): 
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

def path_2_route(paths):

    '''
        this function get the route and its percentage from the path
        path[src][dst] is a list like : ["1-2     50%", "1-3-2     50%"]
        route[src][dst] is a list like : ["1-2", "1-3-2"] two routes
        percent[src][dst] is a list like " ["50%", "50%"]
        have contribution onthe link, and save it in the contribution[] list
    '''

    route = [[[]for col in range(NUMSWITCH)]for row in range(NUMSWITCH)]
    percent = [[[]for col in range(NUMSWITCH)]for row in range(NUMSWITCH)]
    for src in range(NUMSWITCH):
        for dst in range(NUMSWITCH):
            for path in paths[src][dst]:
                route[src][dst].append(path.split("     ")[0])
                percent[src][dst].append(path.split("     ")[1])

    return route, percent

def route_2_contribution(route):

    '''
        this function get the mapping of which src-dst pair
        have contribution onthe link, and save it in the "contribution" dict
    '''

    contribution = {}

    for src in range(NUMSWITCH):
        for dst in range(NUMSWITCH):
            if src != dst:
                for num in range(len(route[src][dst])):
                  switch = route[src][dst][num].split("-")
                  route_len = len(switch)
                  for i in range(route_len - 1):
                      (fst, sec) = (int(switch[i]), int(switch[i + 1]))
                      if (fst, sec) not in contribution:
                          contribution[(fst, sec)] = []
                      if (src, dst) not in contribution[(fst, sec)]:
                          contribution[(fst, sec)].append((src, dst))

    return contribution

def calculate_background_load(m, selected_node_pairs, route, percent):
    
    '''
        calculate the background load:
        sum up all the traffic generated by all the node pairs
        on the same link, except the selected_node_pairs
    '''

    tmp_link_traffic = [[0 for col in range(NUMSWITCH)]for row in range(NUMSWITCH)]
    link_traffic = {}

    for src in range(NUMSWITCH):
        for dst in range(NUMSWITCH):

            if (src, dst) in selected_node_pairs:
              continue  

            if tm[m][src][dst] != 0:
                for num in range(len(route[src][dst])):
                    switch_on_route = route[src][dst][num].split("-")
                    route_len = len(switch_on_route)
                    percentage = \
                      float(percent[src][dst][num].split("%")[0]) / 100

                    for i in range(route_len - 1):
                        fst = int(switch_on_route[i]) - 1
                        sec = int(switch_on_route[i + 1]) - 1
                        tmp_link_traffic[fst][sec] += tm[m][src][dst] * percentage
            for l in links:
                (fst, sec) = links[l]
                link_traffic[l] = tmp_link_traffic[fst - 1][sec - 1]

    return link_traffic

def calculate_performance(selected_node_pairs, m, route, percent):

    '''
        calculate performance:
        first calculate the background_load
    '''

    link_utilization = {}
    mlu = 0.0
    link_traffic = calculate_background_load(m, selected_node_pairs, route, percent)

    '''
        get the link utilization by traffic / capacity
        and then compare to the utilization_optimal of this matrix
        to get the performance ratio
        if the performance ratio is bigger, it means that
        it is more congested
    '''
    #if len(selected_node_pairs) != 0:
        #(src, dst) = selected_node_pairs[-1]
        #print "the selected pairs ", (src + 1, dst + 1), " contribute : ", tm[m][src][dst], "kbytes"

    for link in links:
        (fst, sec) = links[link]
        link_utilization[link] = link_traffic[link] / capacity[link] 
        #print link_utilization[link]," ",

        if mlu < link_utilization[link]:
            mlu = link_utilization[link]
            most_congested_link = links[link]

    #print ("mlu : %f" % mlu)
    #print (most_congested_link)
 
    performance = mlu / utilization_optimal[m]

    #print "the traffic: ", link_traffic[11][1]," the mlu: ", mlu, " next congested link: ", most_congested_link

    return performance, most_congested_link

def select_node_pairs(tm, utilization_optimal, k, route, percent):

    '''
        this function is used to select node_pairs for explicit routing
        k is the number of selecting node pairs

        PAY ATTANTION!!!    
            the pairs in select node pair are range(NUMSWITCH)
            which means src and dst both range from 0 to NUMSWITCH - 1
    '''

    selected_node_pairs = []

    contribution = route_2_contribution(route)

    while k:
        k -= 1 
        max_performance = 0

        '''
            we have to find out the most congested link
            in the most congested traffic matrix
        '''

        for m in tm:

            performance, congested_link = calculate_performance(selected_node_pairs, m, route, percent)

            if performance > max_performance:
                max_performance = performance
                most_congested_link = congested_link
                most_congested_matrix = m

        #for (src, dst) in selected_node_pairs:
        #    print (src + 1, dst + 1)
        #print "the perf is: ", performance, " the next cong_link: ", most_congested_link
        #print

        ''' find the most congested node pairs which contribute most
            on the most congested link
        '''

        min_performance = 100000000
        for (src, dst) in contribution[most_congested_link]:
            if (src, dst) in selected_node_pairs:
                continue
            selected_node_pairs.append((src, dst))
            performance, congested_link = calculate_performance(selected_node_pairs, m, route, percent)
            selected_node_pairs.pop()
            #print "after select out ", (src + 1, dst + 1), " the performance:", performance
            #print   
 
            if performance < min_performance:
                min_performance = performance
                next_selected_node_pair = (src, dst) 

        selected_node_pairs.append(next_selected_node_pair)

    return selected_node_pairs

def explicit_routing(tm, utilization_optimal):

    '''
        this funciton is used to calculate the explicit_path

        tm is a tm[num_matrix][src][dst] 3_dimension_list
            src range from 0 to NUMSWITCH
            dst range from 0 to NUMSWITCH

        utilization_optimal is a list, range from 0 to NUMMATRIX

        k is the number of selected_node_pairs

    '''

    basic_tm = get_basic_tm(tm, len(tm))

    MLU, allocation = destination_based_routing(basic_tm, links, capacity)

    print ("MLU by CPLEX : %f" % MLU)

    fraction = allocation_2_fraction(allocation, links)

    paths = fraction_2_path(fraction, links)

    route, percent = path_2_route(paths)

    selected_node_pairs = select_node_pairs(tm, utilization_optimal, 3, route, percent)

    print "finally selected pairs: ", selected_node_pairs

    '''
        calculate the background_load
    '''

    background_load = [{} for m in tm]

    for m in tm:
        background_load[m] = calculate_background_load(m, selected_node_pairs, route, percent)

    '''
        use CPLEX to solve the linear programming problem to get 
        the allocation of the explicit path routing for the selected
        node pairs based on the background load and the optimal_utilizations

        input: utilizaion_optimal, background_load for all matrix
        output: explicit routing ratios which P is minimized

    ''' 

    prob = cplex.Cplex()

    # sys.stdout is the default output stream for log and results
    # so these lines may be omitted
    #prob.set_results_stream("/dev/null")
    #prob.set_log_stream("/dev/null")

    prob.set_results_stream(sys.stdout)
    prob.set_log_stream(sys.stdout)

    ic_handle = _buildmodel(prob, tm, links, capacity, selected_node_pairs, utilization_optimal, background_load)

    #prob.write("explicitrouting.lp")

    prob.solve()

    sol = prob.solution

    print 
    # solution.get_status() returns an integer code
    print "Solution status = ", sol.status[sol.get_status()]
    print "Solution value = ", sol.get_objective_value()

    num_link = len(links)
    num_pair = len(selected_node_pairs)

    x = sol.get_values(0, num_link * num_pair)

    performance = x[num_link * num_pair]

    allocation = [[0 for col in range(num_link)]for row in range(num_pair)]

    for p in range(num_pair):
        for l in range(num_link):
            allocation[p][l] = float(x[p * num_link + l])

    return performance, allocation, selected_node_pairs

def search_path(p, src, tmp_next_node, tmp_path, tmp_percent, fraction, links, paths):

    '''
        deep first search for the path from a switch to another
    '''


    for l in links:
        (node, next_node) = links[l]
        # dst + 1 is the actual switch num range(1,13), dst range(0,12)
        if next_node == tmp_next_node and fraction[p][l] != 0.0:

            prev_path = tmp_path
            prev_percent = tmp_percent
            tmp_path = str(node) + "-" + tmp_path
            if fraction[p][l] < tmp_percent:
                tmp_percent = fraction[p][l]
            
            if node == src:
                paths[p].append(tmp_path + "     " + "%.2f" % (tmp_percent * 100) + "%")
            # search node as the next_node :  x -> node -> next_node
            search_path(p, src, node, tmp_path, tmp_percent, fraction, links, paths)
            # append the path that towards the dst 
            # from this node and its percentage
            tmp_path = prev_path
            tmp_percent = prev_percent




if __name__ == "__main__":

    tm = read_traffic(usr_home + "/dhrpox/traffic/2014_06_24TM")

    links, capacity = read_link(usr_home + "/dhrpox/topology/abilene.txt")

    NUMMATRIX = len(tm)

    utilization_optimal = [0] * NUMMATRIX

    for t in range(0, 1):
        utilization_optimal[t], ignore = destination_based_routing(tm[t], links, capacity)
   
    tm_tmp = {}

    tm_tmp[0] = tm[0] 

    performance, allocation, selected_node_pairs = explicit_routing(tm_tmp, utilization_optimal)

    num_pair = len(allocation)
    num_link = len(links)

    for p in range(len(allocation)):
        for l in range(len(allocation[p])):
            if allocation[p][l] != 0.0:
                print links[l]," ",allocation[p][l]," ",
        print
        print 


    paths = [[] for col in range(num_pair)]

    for p in range(num_pair):
    # dst + 1 is the actual switch num range(1,13), dst range(0,12)
        (src, dst) = selected_node_pairs[p]
        tmp_path = str(dst + 1)
        tmp_percent = 1.0
        search_path(p, src + 1, dst + 1, tmp_path, tmp_percent, allocation, links, paths)
        print paths[p]

