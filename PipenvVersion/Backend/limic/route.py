GRAPH = (("file_name",),{'type':str,'help':"use graph file GRAPH",'metavar':'GRAPH'})
CACHE = (("file_name",),{'type':str,'help':"use cache file CACHE",'metavar':'CACHE'})
SOURCE = (("-s","--source"),{'type':int,'dest':'source_id','help':"set source power tower to SOURCE (default: random)",'metavar':'SOURCE'})
TARGET = (("-t","--target"),{'type':int,'dest':'target_id','help':"set target power tower to TARGET (default: random)",'metavar':'TARGET'})
OUT = (("-o","--output"),{'type':str,'dest':'out_file','help':"write path to OUT (default: stdout)",'metavar':'OUT'})
INDIRECT = (("-i","--indirect"),{'action':'store_true','dest':'indirect','default':False,'help':"transform indirectly (default: False)"})
PENALIZE = (("-p","--penalize"),{'type':int,'default':20,'dest':'penalize','help':"penalize air time by factor PENALTY",'metavar':'PENALTY'})
VISUALIZE = (("-m","--map"),{'action':'store_true','dest':'visualize','default':False,'help':"render route to HTML map"})
BENCHMARK = (("-b","--benchmark"),{'type':str,'dest':'benchmark','help':"specify file with routes to benchmark",'metavar':'ROUTES'})

CONFIG = [
    ("npz",{'help':"route using NPZ graph",'args':[INDIRECT,PENALIZE,SOURCE,TARGET,OUT,VISUALIZE,GRAPH]}),
    ("nx",{'help':"route using NX graph",'args':[SOURCE,TARGET,OUT,VISUALIZE,BENCHMARK,GRAPH]}),
    ("cnx",{'help':"route using CNX graph",'args':[SOURCE,TARGET,OUT,VISUALIZE,BENCHMARK,GRAPH]}),
    ("gt",{'help':"route using GT graph",'args':[INDIRECT,PENALIZE,SOURCE,TARGET,OUT,VISUALIZE,GRAPH]}),
    ("direct",{'help':"route directly",'args':[
        (("-s","--source"),{'type':int,'dest':'source_id','help':"set source power tower to SOURCE (default: random)",'metavar':'SOURCE','required':True}),
        (("-t","--target"),{'type':int,'dest':'target_id','help':"set target power tower to TARGET (default: random)",'metavar':'TARGET','required':True}),
        OUT,
        (("-u","--overpass-url"),{'type':str,'dest':'overpass_url','help':"define url for Overpass API to be URL (default: http://caracal.imada.sdu.dk/)",'metavar':'URL'}),
        (("-d","--disk-cache"),{'action':'store_true','dest':'disk_cache','default':False,'help':"use disk cache (default: False)"}),
        VISUALIZE,
        CACHE
    ]})
]

def astar_path_npz(lat, long, id2edges, edges_weight, edges_neighbor, source, target):
    from itertools import count
    from heapq import heappush, heappop
    from limic.util import haversine_distance
    targetlong = long[target]
    targetlat = lat[target]
    c = count()
    queue = [(0, next(c), source, 0, None)]
    enqueued = {}
    explored = {}
    while queue:
        _, __, curnode, dist, parent = heappop(queue)
        if curnode == target:
            path = [curnode]
            node = parent
            while node is not None:
                path.append(node)
                node = explored[node]
            path.reverse()
            return path
        if curnode in explored:
            if explored[curnode] is None:
                continue
            qcost, h = enqueued[curnode]
            if qcost < dist:
                continue
        explored[curnode] = parent
        left = id2edges[curnode]
        right = id2edges[curnode+1]
        for i in range(left,right):
            w = edges_weight[i]
            neighbor = edges_neighbor[i]
            ncost = dist + w
            if neighbor in enqueued:
                qcost, h = enqueued[neighbor]
                if qcost <= ncost:
                    continue
            else:
                h = haversine_distance(long[neighbor], lat[neighbor], targetlong, targetlat)
            enqueued[neighbor] = ncost, h
            heappush(queue, (ncost + h, next(c), neighbor, ncost, curnode))
    raise ValueError("node %s not reachable from %s" % (target, source))

def astar_npz(g,source_id=None,target_id=None):
    from limic.util import locate_by_id, haversine_distance
    ids = g['ids']
    lat = g['lat']
    long = g['long']
    id2edges = g['id2edges']
    edges_weight = g['edges_weight']
    edges_neighbor = g['edges_neighbor']
    edges_air = g['edges_type']
    if isinstance(source_id,tuple) and isinstance(target_id,tuple):
        source, target = source_id[1], target_id[1]
    else:
        source, target = locate_by_id(ids,source_id,target_id)
    try:
        path = astar_path_npz(lat, long,id2edges,edges_weight,edges_neighbor,source,target)
    except ValueError as e:
        path = []
    def index2node(cost,dist,air,index):
        return (float(cost),float(dist),air,int(ids[index]),float(lat[index]),float(long[index]))
    if path:
        cost = dist = 0.0
        dpath = [index2node(cost,dist,False,path[0])]
        for i in range(1,len(path)):
            left = id2edges[path[i]]
            right = id2edges[path[i]+1]
            for j in range(left,right):
                if edges_neighbor[j] == path[i-1]:
                    dist = edges_weight[j]
                    air = edges_air[j]
                    cost += dist
                    dpath.append(index2node(cost,dist,bool(air < 0),path[i]))
                    break
        return cost,dpath
    else:
        dist = haversine_distance(long[source],lat[source],long[target],lat[target])
        return None,[index2node(0.,0.,False,source),index2node(float('inf'),dist,True,target)]

def route_npz(file_name,source_id=None,target_id=None,out_file=None,indirect=False,penalize=20,visualize=False):
    from limic.util import start, end, status, save_path, load_npz
    from limic.convert import transform_npz_nx
    from numpy import int32
    start("Loading from",file_name)
    g = load_npz(file_name)
    end()
    start("Checking whether GT graph is rescaled")
    if g['edges_weight'].dtype == int32:
        indirect = True
        status("YES (forcing routing through NX)")
    else:
        status("NO")
    if indirect:
        start("Transforming graph to NX format")
        h = transform_npz_nx(g,penalize)
        end()
        start("Routing using NX")
        path = astar_nx(h,source_id,target_id)
        end()
    else:
        start("Routing using NPZ")
        path = astar_npz(g,source_id,target_id)
        end()
    start("Saving path to",out_file)
    save_path(path,out_file,visualize)
    end()

def astar_nx(g,source_id=None,target_id=None):
    from limic.util import locate_by_id, haversine_distance
    from networkx import astar_path, NetworkXNoPath
    if isinstance(source_id,tuple) and isinstance(target_id,tuple):
        source, target = source_id[0], target_id[0]
    else:
        nodes = list(g.nodes())
        ids = list(map(lambda x:x[0],nodes))
        source, target = locate_by_id(ids,source_id,target_id)
        source, target = nodes[source], nodes[target]
    targetlat, targetlong = target[1], target[2]
    def distance(x,y):
        #assert(target==y)
        return haversine_distance(longx=x[2],latx=x[1],longy=targetlong,laty=targetlat)
    try:
        if 'paths' in g.graph and g.graph['paths']:
            path = g.graph['paths'][source][target]
        else:
            path = astar_path(g,source,target,heuristic=distance)
        cost = dist = 0.0
        dpath = [(cost,dist,False)+path[0]]
        for i in range(1,len(path)):
            ggg = g[path[i-1]][path[i]]
            dist = ggg['weight']
            cost += dist
            air = ggg['type']
            dpath.append((cost,dist,air < 0)+path[i])
        return cost,dpath
    except NetworkXNoPath as e:
        cost = dist = distance(source,target)
        path = None,[(0.,0.,False)+source,(float('inf'),dist,True)+target]
    return path

def route_nx(file_name,source_id=None,target_id=None,out_file=None,visualize=False,benchmark=None):
    from limic.util import start, end, load_pickled, save_path
    start("Loading from",file_name)
    g = load_pickled(file_name)
    end()
    start("Routing using NX")
    if benchmark:
        for source, target in load_pickled(benchmark):
            path = astar_nx(g,(source,),(target,))
    else:
        path = astar_nx(g,source_id,target_id)
    end()
    if not benchmark:
        start("Saving path to",out_file)
        save_path(path,out_file,visualize)
        end()
    
def astar_cnx(g,source_id=None,target_id=None,routes=None):
    from limic.util import locate_by_id, distance
    cs,node2closest,node2c = g.cs,g.node2closest,g.node2c
    if isinstance(source_id,tuple) and isinstance(target_id,tuple):
        source, target = source_id[0], target_id[0]
    else:
        nodes = list(node2closest.keys())
        nodes.extend(node2c.keys())
        ids = list(map(lambda x:x[0],nodes))
        source, target = locate_by_id(ids,source_id,target_id)
        source, target = nodes[source], nodes[target]
        if not routes is None:
            routes.append((source,target))
    if source not in node2closest:
        if target in node2closest or node2c[source] != node2c[target]:
            cost = dist = distance(source,target)
            path = None,[(0.,0.,False)+source,(float('inf'),dist,True)+target]
            return path
        path = astar_nx(node2c[source],(source,),(target,))
        return path
    if target not in node2closest:
        cost = dist = distance(source,target)
        path = None,[(0.,0.,False)+source,(float('inf'),dist,True)+target]
        return path
    paths = []
    def extend(cp1,cp2):
        cost = cp1[0]
        path = cp1[1]
        assert(path[-1][3:] == cp2[1][0][3:])
        path.extend(map(lambda x:((x[0]+cost,)+x[1:]),cp2[1][1:]))
        cost += cp2[0]
        return cost, path
    for ns,ps,cs in node2closest[source]:
        for nt,pt,ct in node2closest[target]:
            c = node2c[ns]
            if c != node2c[nt]:
                cost = dist = distance(source,target)
                path = None,[(0.,0.,False)+source,(float('inf'),dist,True)+target]
                return path
            cp = astar_nx(ps,(source,),(ns,))
            cpc = astar_nx(c,(ns,),(nt,))
            for u,v in zip(cpc[1],cpc[1][1:]):
                u,v = u[3:], v[3:]
                cuv = c[u][v]
                sg = cuv["path"]
                cpuv = astar_nx(sg,(u,),(v,))
                cp = extend(cp,cpuv)
            cpt = astar_nx(pt,(nt,),(target,))
            cp = extend(cp,cpt)
            paths.append(cp)
#            paths.append((cs+c.graph['lengths'][ns][nt]+ct,[]))
    return min(paths)

def route_cnx(file_name,source_id=None,target_id=None,out_file=None,visualize=False,benchmark=None):
    from limic.util import start, end, load_pickled, save_path, save_pickled
    start("Loading from",file_name)
    g = load_pickled(file_name)
    end()
    start("Routing using condensed NX")
    if benchmark and out_file:
        routes = []
        for i in range(int(benchmark)):
            path = astar_cnx(g,None,None,routes)
    elif benchmark:
        for source, target in load_pickled(benchmark):
            path = astar_cnx(g,(source,),(target,))
    else:
        path = astar_cnx(g,source_id,target_id)
    end()
    if benchmark and out_file:
        start("Saving routes to",out_file)
        save_pickled(out_file,routes)
        end()
    elif not benchmark:
        start("Saving path to",out_file)
        save_path(path,out_file,visualize)
        end()

def astar_gt(g,source_id=None,target_id=None):
    from graph_tool.search import astar_search, AStarVisitor, StopSearch
    from limic.util import locate_by_id, haversine_distance
    long = g.vp.long
    lat = g.vp.lat
    ids = list(map(lambda x:x[1],g.get_vertices([g.vp.id])))
    source, target = locate_by_id(ids,source_id,target_id)
    source, target = g.vertex(source), g.vertex(target)
    targetlong, targetlat = long[target], lat[target]
    class Visitor(AStarVisitor):
        def __init__(self, target):
            self.target = target
        def edge_relaxed(self, e):
            if e.target() == self.target:
                raise StopSearch()
    def distance(x):
        return haversine_distance(longx=long[x],latx=lat[x],longy=targetlong,laty=targetlat)
    dist, pred = astar_search(g, source, g.ep.weight, Visitor(target), heuristic=distance)
    path = []
    current = target
    total_cost = cost = dist[current]
    if g.vertex(pred[current]) == current:
        air = True
        dist = distance(source)
    else:
        e = g.edge(g.vertex(pred[current]),g.vertex(current))
        dist = g.ep.weight[e]
        air = True if g.ep.type[e] < 0 else False
    while True:
        i = int(current)
        path.append((cost,dist,air < 0,ids[i],lat[i],long[i]))
        pre = g.vertex(pred[current])
        if pre == current:
            break
        cost -= dist
        current = pre
        pre = g.vertex(pred[current])
        if pre == current:
            dist = 0.
            air = False
        else:
            e = g.edge(g.vertex(pre),g.vertex(current))
            dist = g.ep.weight[e]
            air = True if g.ep.type[e] < 0 else False
    path.reverse()
    if len(path) < 2:
        assert(len(path)==1)
        source = int(source)
        return None if source != target else 0.,[(0.,0.,False,ids[source],lat[source],long[source])]+(path if source != target else [])
    else:
        return total_cost,path

def route_gt(file_name,source_id=None,target_id=None,out_file=None,indirect=False,penalize=20,visualize=False):
    from limic.util import start, end, status, load_gt, save_path
    from limic.convert import transform_gt_npz
    start("Loading graph from",file_name)
    g = load_gt(file_name)
    end()
    start("Checking whether GT graph is rescaled")
    if g.gp.rescaled:
        indirect = True
        status("YES (forcing routing through NPZ)")
    else:
        status("NO")
    if indirect:
        start("Transforming graph to NPZ format")
        h = transform_gt_npz(g,penalize)
        end()
        start("Routing using NPZ")
        path = astar_npz(h,source_id,target_id)
        end()
    else:
        start("Routing using GT")
        path = astar_gt(g,source_id,target_id)
        end()
    start("Saving path to",out_file)
    save_path(path,out_file,visualize)
    end()

def reconstruct_path_direct(current):
    from limic.util import distance
    dist = current.g-current.origin.g if current.origin else 0.
    air = distance(current.tower.latlon,current.origin.tower.latlon) < 0.9*dist if current.origin else False
    cost = 0.
    path = [(current.g,dist,air,current.tower.id,current.tower.latlon[0],current.tower.latlon[1])]
    while current.origin:
        current = current.origin
        cost = current.g
        dist = cost-current.origin.g if current.origin else 0.
        air = distance(current.tower.latlon,current.origin.tower.latlon) < 0.9*(current.g-current.origin.g) if current.origin else False
        path.append((cost,dist,air,current.tower.id,current.tower.latlon[0],current.tower.latlon[1]))
    path.reverse()
    return cost, path

def astar_tower_direct(start,end,max_fly=1000,eps=0.01,safe_dist=100,penalty=20,prec=1):
    class node:
        def __init__(self,f,g,tower,origin):
            self.f = f
            self.g = g
            self.tower = tower
            self.origin = origin
        def __lt__(self,other):
            return self.f < other.f
        def __repr__(self):
            return "node(f="+repr(self.f)+",g="+repr(self.g)+",tower="+repr(self.tower)+",origin="+repr(self.origin.tower.id if self.origin else self.origin)+")"
    from limic.overpass import find_all_neighbours
    from heapq import heappop, heappush, heapify
    from limic.util import distance
    from math import inf
    latlon2id = {}
    minusid = [0]
    start_node = node(distance(start.latlon,end.latlon)*prec,0,start,None)
    nodes = {start.id : start_node}
    todo = [start_node]
    while todo:
        #if verbosity >= 4: print("*******************\n"+str(todo)+"\n***************")
        #if verbosity >= 4: print("*******************\n"+str(sorted(todo))+"\n***************")
        current = heappop(todo)
        #if verbosity >= 2: print("visiting",current.f,current.tower.id,current.tower.latlon)
        #if verbosity >= 2: print("full node",current)
        if current.tower.id == end.id:
            return reconstruct_path_direct(current)
        #if verbosity >=2:
        #    print("CURRENT PATH:\nnode(id:"+(",".join(map(str,reconstruct_path(current)[1])))+");out;")
        #    print("FRONT:\nnode(id:"+(",".join(map(lambda n:str(n.tower.id),todo)))+");out;")
        neighbours = find_all_neighbours(current.tower, max_fly, eps, safe_dist, minusid, latlon2id, penalty)
        for neighbour in neighbours:
            g = current.g+neighbour.dist
            neighbour_node = nodes.get(neighbour.tower.id,node(None,inf,neighbour.tower,None))
            if g < neighbour_node.g:
                if not neighbour_node.f:
                    nodes[neighbour.tower.id] = neighbour_node
                must_add = neighbour_node not in todo
                neighbour_node.origin = current
                neighbour_node.g = g
                neighbour_node.f = g+distance(neighbour.tower.latlon,end.latlon)*prec
                if must_add:
                    #if verbosity >= 3: print("added",neighbour_node)
                    heappush(todo,neighbour_node)
                #else:
                    #if verbosity >= 3: print("modified",neighbour_node)
                heapify(todo)
    return None,[(0.,0.,False,start.id,start.latlon[0],start.latlon[1]),(float('inf'),start_node.f,True,end.id,end.latlon[0],end.latlon[1])]

def astar_direct(start,end):
    from limic.overpass import tower_by_id
    start_tower = tower_by_id(start)
    end_tower = tower_by_id(end)
    return astar_tower_direct(start_tower,end_tower)
    
def route_direct(file_name,source_id=None,target_id=None,out_file=None,overpass_url=None,disk_cache=False,visualize=False):
    from limic.util import start, end, status, file_size, load_pickled, save_pickled, save_path, options, replace
    if disk_cache:
        start("Using disk cache",file_name)
        set_option('disk_cache',file_name)
    from limic.overpass import region, set_server
    if disk_cache:
        status("OK")
    from os.path import exists
    if not disk_cache and exists(file_name):
        start("Loading",file_name)
        region.backend._cache = load_pickled(file_name)
        end('')
        file_size(file_name)
    len_cache = len(region.backend._cache)
    start("Routing using direct algorithm")
    set_server(overpass_url)
    path = astar_direct(source_id,target_id)
    end()
    start("Saving path to",out_file)
    save_path(path,out_file,visualize)
    end()
    if not disk_cache and len_cache != len(region.backend._cache):
        file_name_tmp = file_name+".tmp"
        start("Saving to",file_name,"via",file_name_tmp)
        save_pickled(file_name_tmp,region.backend._cache)
        replace(file_name_tmp,file_name)
        end('')
        file_size(file_name)


"""
VEHICLE ROUTING PROBLEM
"""
# TODO (3) Maybe separate astart (pathfinding) and vehicle routing in two files?
# TODO (3) Maybe cache all found routes?

# TODO (3) Where to store transformer? Maybe limic.utils?
from pyproj import CRS, Transformer
crs_4326 = CRS("WGS 84")
crs_proj = CRS("EPSG:28992")
transformer = Transformer.from_crs(crs_4326, crs_proj)

# TODO (3) Where to put location object?
# TODO (3) Expand into Tower & Drone objects instead?
class Location():
    def __init__(self, id, coords, order='latlon'):
        self.id = id
        if order in ['latlon', 'xy']:
            self.lat, self.lon = coords
        elif order in ['lonlat', 'yx']:
            self.lon, self.lat = coords

    def get_id(self):
        return self.id

    def get_coords(self, transform=None, order='latlon'):
        lat = self.lat
        lon = self.lon
        if transform == "EPSG:28992":
            lat, lon = transformer.transform(lat, lon)
        if order in ["latlon", "yx"]:
            return lat, lon
        elif order in ["lonlat", "xy"]:
            return lon, lat


def vehicle_routing_problem(g, astar, tree, drones, towers):
    """ Solves the Vehicle Routing Problem with set starts and arbritary ends.
    Arguments:
        g: is the graph
        astar: is the astar function
        tree: is the KDTree of towers
        drones: list of drones available
        towers: list of towers to visit
    Returns:
        { drone_id: { distance: int , path: [(coords), ...] }, ...}
    """
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    from itertools import combinations
    from copy import copy

    # TODO (2) Location deduplication (drones might be at a tower already)
    # TODO (3) Look into weird behaviours, does astar overweigh line switches?
    
    def compute_distance_matrix(drones, towers):
        """ Generate distance matrix with mock depot (free return)
        Arguments:
            drones: list of drones available (Location object)
            towers: list of towers to visit (Location object)
        Returns:
            distanceMatrix: {(source, target): distance} where index-wise s <= t
        
        Note: Computation is optimized and assumes that:
            * A->B = B->A
            * A->A = 0
            * A->depot = 0 (depot is last location)
        """
        from scipy.spatial import cKDTree as KDTree
        
        locations = drones + towers
        paths = {}
        dist_dict = {}
        # Get distances and paths
        for s, t in combinations(range(len(locations)), 2):
            source = locations[s]
            source_index = tree.query(source.get_coords( 
                transform="EPSG:28992", order="latlon"))[1]
            target = locations[t] # Target coords
            target_index = tree.query(target.get_coords( 
                transform="EPSG:28992", order="latlon"))[1]

            distance, path = astar(g,(source,source_index),(target,target_index))
            paths[(s,t)] = list(map(lambda x: (x[-2], x[-1]), path))
            dist_dict[(s, t)] = int(distance)
        # Build distance matrix
        matrix = []
        for x in range(len(locations) + 1):
            row = []
            for y in range(len(locations) + 1):
                if x == y: row.append(0)# A->A = 0
                elif len(locations) in [x, y]: row.append(0) # A->depot = 0
                # A->B = B->A and dictionary only has smaller index first
                elif x < y: row.append(dist_dict[(x,y)]) 
                elif y < x: row.append(dist_dict[(y,x)])
            matrix.append(row)
        
        return matrix, paths
        
    # TODO (2) Rewrite and make nicer
    def create_data_model(drones, towers):
        data = {}
        data['distance_matrix'], data['path_cache'] =  compute_distance_matrix(drones, towers)
        data['num_vehicles'] = len(drones)
        data['num_locations'] = len(data['distance_matrix'])
        data['starts'] = list(range(data['num_vehicles'])) # Drones are first locations (change this later)
        data['ends'] = [len(data['distance_matrix'])-1] * data['num_vehicles'] # End at depot index
        return data

    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes. Uses the precomputed 
        distance matrix."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]
        
    def generate_paths(data, manager, routing, solution):
        """Prints solution on console."""
        paths = {}
        for drone_index in range(data['num_vehicles']):
            drone_id = drones[drone_index].get_id()
            index = routing.Start(drone_index)
            route_distance = 0
            path = []
            while not routing.IsEnd(index):
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                if index >= (data['num_locations'] - 1): # break at depot
                    break                
                if previous_index < index: # Same direction as cache
                    path += data['path_cache'][(previous_index, index)]
                elif previous_index > index: # Opposite direciton as cache
                    p = copy(data['path_cache'][(index, previous_index)])
                    p.reverse()
                    path += p 
                route_distance += routing.GetArcCostForVehicle(
                    previous_index, index, drone_index)
            paths[drone_id] = {
                'distance': route_distance,
                'path': path
            }
        return paths
        
    def print_solution(data, manager, routing, solution):
        """Prints solution on console."""
        max_route_distance = 0
        for vehicle_id in range(data['num_vehicles']):
            index = routing.Start(vehicle_id)
            plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
            route_distance = 0
            while not routing.IsEnd(index):
                plan_output += ' {} -> '.format(manager.IndexToNode(index))
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(
                    previous_index, index, vehicle_id)
            plan_output += '{}\n'.format(manager.IndexToNode(index))
            plan_output += 'Distance of the route: {}m\n'.format(route_distance)
            print(plan_output)
            max_route_distance = max(route_distance, max_route_distance)
        print('Maximum of the route distances: {}m'.format(max_route_distance))

    """
    Start of Vehicle Routing Problem Solver
    """
    #print(f"Finding a path to {len(towers)} towers for {len(drones)} drones.")
    
    data = create_data_model(drones, towers)
    
    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        #data['num_locations'],
        len(data['distance_matrix']),
        data['num_vehicles'],
        data['starts'],
        data['ends'])
        
    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Register the transit callback (travel distance)
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    # Define cost of each arc (travel distance equals the cost of travel)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Distance constraint, cummulative distance traveled
    # TODO (2) Investigate why excluded in BP
    dimension_name = 'Distance'
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        200000,  # vehicle maximum travel distance
        True,  # start cumul to zero
        dimension_name)
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # Setting first solution heuristic.
    # TODO (2) Investigate implementation in BP
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # TODO (3) Consider solution format
    if solution:
        #print_solution(data, manager, routing, solution) 
        return generate_paths(data, manager, routing, solution)
    return "Failed to find solution!"