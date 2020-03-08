#!/usr/local/bin/python3

# import packages
import sys
import heapq
import copy

# create a priority queue class that can update priority values
class updatingPriorityQueue:
    """(priority_val, curr_city, t_seg, t_miles, t_hrs, t_gas, cities_so_far)"""
    def __init__(self):
        self.queue = [] 
        self.dict = {} # save lowest priority values
        
    def qsize(self):
        return len(self.queue)
    
    def add(self, new_item):
        priority_val, curr_city, t_seg, t_miles, t_hrs, t_gas, cities_so_far = new_item
        # if new_item has higher priority than existing priority, then do not add
        if curr_city in self.dict and self.dict[curr_city] <= priority_val:
            return
        heapq.heappush(self.queue, (priority_val, curr_city, t_seg, t_miles, t_hrs, t_gas, cities_so_far))
        self.dict[curr_city] = priority_val
    
    def pop(self):
        priority_val, curr_city, t_seg, t_miles, t_hrs, t_gas, cities_so_far = heapq.heappop(self.queue)
        if self.dict[curr_city] == -1:
            return None
        self.dict[curr_city] = -1 # this state has been removed
        return priority_val, curr_city, t_seg, t_miles, t_hrs, t_gas, cities_so_far
    
# define functions
def load_map(filename):
    """load map to a list of lists"""
    with open(filename, "r") as f:
        return [[i for i in row.split()] for row in f ]

def gps2dict(gps):
    """convert gps to dictionary"""
    return {g[0]: {'lat': float(g[1]), 'lon': float(g[2])} for g in gps}

def seg2dict(seg):
    """convert segment to dictionary"""
    res = {}
    for s in seg:
        if s[0] not in res:
            res[s[0]] = {s[1]: {'len': int(s[2]), 'speed_l': int(s[3]), 'h_way': s[4]}} 
        else:
            res[s[0]][s[1]] = {'len': int(s[2]), 'speed_l': int(s[3]), 'h_way': s[4]}
        
        if s[1] not in res:
            res[s[1]] = {s[0]: {'len': int(s[2]), 'speed_l': int(s[3]), 'h_way': s[4]}} 
        else:
            res[s[1]][s[0]] = {'len': int(s[2]), 'speed_l': int(s[3]), 'h_way': s[4]}
    return res

def successors(city):
    """find successors"""
    return segment_dict[city]

# define heuristic functions
def est_euclidean_dist(o, d):
    """estimate euclidean distance between current place and destination"""
    return (((gps_dict[o]['lat'] - gps_dict[d]['lat'])**2) + ((gps_dict[o]['lon'] - gps_dict[d]['lon'])**2))**0.5 \
if o in all_gps and d in all_gps else 0

def est_travel_time(o, d):
    """estimate travel time from current place to destination"""
    return est_euclidean_dist(o, d) / max_vel

def est_gas(o, d):
    """estimate gas usage from current place to destination"""
    return est_euclidean_dist(o, d) / cal_mpg(max_vel)

def select_heuristic_fcn(cost):
    """select heuristic function based on cost"""
    if cost == 'segments': return lambda o, d:0
    elif cost == 'distance': return est_euclidean_dist
    elif cost == 'time': return est_travel_time
    elif cost == 'mpg': return est_gas

# define g functions
def select_g_fcn(cost):
    """select g function based on cost"""
    if cost == 'segments': return lambda ns, nm, nh, ng: ns #new_seg
    elif cost == 'distance': return lambda ns, nm, nh, ng: nm #new_miles
    elif cost == 'time': return lambda ns, nm, nh, ng: nh #new_hrs
    elif cost == 'mpg': return lambda ns, nm, nh, ng: ng #new_gas

def cal_hrs(distance, speed):
    """calculate travel time"""
    return distance / speed

def cal_mpg(speed):
    """calculare mileage per gallon(mpg)"""
    return 400 * (speed / 150) * ((1 - (speed / 150))** 4)

def solve(cost, start_city, end_city):
    """solve the problem by using A star algorithm"""
    # priority_val, curr_city, [total-segments] [total-miles] [total-hours] [total-gas-gallons] , cities_so_far
    fringe = updatingPriorityQueue()
    fringe.add((0, start_city, 0, 0, 0, 0, ()))
    
    heuristic_fcn = select_heuristic_fcn(cost)
    g_fcn = select_g_fcn(cost)

    while fringe.qsize() > 0:
        curr = fringe.pop()
        if curr is None:
            continue
        priority_val, curr_city, curr_seg, curr_miles, curr_hrs, curr_gas, cities_so_far = curr
        if curr_city == end_city:
            return curr_seg, curr_miles, curr_hrs, curr_gas, cities_so_far
            
        succ = successors(curr_city)
        for s in succ.items():
            nxt_city = s[0]
            nxt_miles, nxt_speed_limit, nxt_h_way = [v for v in s[1].values()]
            new_cities_so_far = cities_so_far + (nxt_city,)
            new_seg = len(new_cities_so_far)
            new_miles = curr_miles + nxt_miles
            new_hrs = curr_hrs + cal_hrs(nxt_miles, nxt_speed_limit)
            new_gas = curr_gas + (nxt_miles / cal_mpg(nxt_speed_limit))
            
            fringe.add(((g_fcn(new_seg, new_miles, new_hrs, new_gas) +\
                         heuristic_fcn(nxt_city, end_city)), \
                       nxt_city, new_seg, new_miles, new_hrs, new_gas, new_cities_so_far))
    return None


# driver code
if __name__ == "__main__":
    if(len(sys.argv) != 4):
        raise(Exception("Error: expect 3 arguments"))
    if sys.argv[3] not in ['segments', 'distance', 'time', 'mpg']:
        raise(Exception("Error: Unknown cost!"))
    
    start_city, end_city, cost_function = str(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3])
    gps = load_map('city-gps.txt')
    gps_dict = gps2dict(gps)
    all_gps = set(k for k in gps_dict.keys())

    segment = load_map('road-segments.txt')
    max_vel = max([int(s[3]) for s in segment])
    segment_dict = seg2dict(segment)

    sol = solve(cost_function, start_city, end_city)
    #[total-segments] [total-miles] [total-hours] [total-gas-gallons] [start-city] [city-1] [city-2] ... [end-city]
    print(str(sol[0]) + " " + str(sol[1]) + " " + str(round(sol[2], 4)) + " " + str(round(sol[3], 4)) + " " \
        + start_city + " " +  " ".join(sol[-1]))
