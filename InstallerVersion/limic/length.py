SOURCE = (("-s","--source"),{'type':int,'dest':'source_id','help':"set source power tower to SOURCE (default: random)",'metavar':'SOURCE'})
TARGET = (("-t","--target"),{'type':int,'dest':'target_id','help':"set target power tower to TARGET (default: random)",'metavar':'TARGET'})
OUT = (("-o","--output"),{'type':str,'dest':'out_file','help':"write length to OUT (default: stdout)",'metavar':'OUT'})
BENCHMARK = (("-b","--benchmark"),{'type':str,'dest':'benchmark','help':"specify file with source target pairs to benchmark",'metavar':'ROUTES'})
GRAPH = (("file_name",),{'type':str,'help':"use graph file GRAPH",'metavar':'GRAPH'})

CONFIG = [
    ("graph",{'help':"count total length of edges in graph",'args':[
        ("nx",{'help':"count total length of edges in NX graph",'args':[GRAPH]}),
        ("gt",{'help':"count total length of edges in GT graph",'args':[GRAPH]}),
        ("npz",{'help':"count total length of edges in NPZ graph",'args':[GRAPH]})
    ]}),
    ("route",{'help':"compute short path length between two points",'args':[
        ("cnx",{'help':"shortest path using CNX graph",'args':[SOURCE,TARGET,BENCHMARK,GRAPH]}),
        ("nx",{'help':"shortest path using NX graph",'args':[SOURCE,TARGET,BENCHMARK,GRAPH]})
    ]})
]

def compute_length_gt(g):
    es = g.get_edges([g.ep.weight,g.ep.type])
    total_length = 0
    for e in es:
        if e[3] >= 0:
            total_length += e[2]/1000.
    return total_length

def length_graph_nx(file_name):
    from limic.util import start, end, status, load_pickled
    from limic.convert import transform_nx_gt
    start("Loading graph from",file_name)
    g = load_pickled(file_name)
    end()
    start("Transforming graph to rescaled GT format")
    h = transform_nx_gt(g,rescale=True)
    end()
    start("Computing length using rescaled GT")
    length = compute_length_gt(h)
    end('')
    status(length)

def length_graph_gt(file_name):
    from limic.util import start, end, status, load_gt
    from limic.convert import transform_gt_npz, transform_npz_nx, transform_nx_gt
    start("Loading graph from",file_name)
    g = load_gt(file_name)
    end()
    start("Checking whether GT graph is rescaled")
    if g.gp.rescaled:
        status("YES")
        start("Computing length using GT")
        length = compute_length_gt(g)
        end('')
        status(length)
    else:
        status("NO (forcing reconversion)")
        start("Transforming graph to NPZ format")
        h = transform_gt_npz(g,penalize=20)
        end()
        start("Transforming graph to NX format")
        i = transform_npz_nx(h)
        end()
        start("Transforming graph to rescaled GT format")
        j = transform_nx_gt(i,rescale=True)
        end()
        start("Computing length using rescaled GT")
        length = compute_length_gt(j)
        end('')
        status(length)

def length_graph_npz(file_name):
    from limic.util import start, end, status, load_npz
    from limic.convert import transform_npz_nx, transform_nx_gt
    start("Loading graph from",file_name)
    g = load_npz(file_name)
    end()
    start("Transforming graph to NX format")
    h = transform_npz_nx(g)
    end()
    start("Transforming graph to rescaled GT format")
    i = transform_nx_gt(h,rescale=True)
    end()
    start("Computing length using rescaled GT")
    length = compute_length_gt(i)
    end('')
    status(length)

def shortest_length_cnx(g,source_id=None,target_id=None):
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
    if source not in node2closest:
        if target in node2closest or node2c[source] != node2c[target]:
            return float('inf')
        c = node2c[source]
        if c.graph['lengths']:
            cost = c.graph['lengths'][source][target]
        else:
            cost = shortest_length_nx(c,(source,),(target,))
        return cost
    if target not in node2closest:
        return float('inf')
    costs = []
    for ns,ps,cs in node2closest[source]:
        for nt,pt,ct in node2closest[target]:
            c = node2c[ns]
            if c != node2c[nt]:
                return float('inf')
            if c.graph['lengths']:
                costs.append(cs+c.graph['lengths'][ns][nt]+ct)
            else:
                cc = shortest_length_nx(c,(ns,),(nt,))
                costs.append(cs+cc+ct)
    return min(costs)

def length_route_cnx(file_name,source_id=None,target_id=None,benchmark=None):
    from limic.util import start, end, load_pickled, status
    start("Loading from",file_name)
    g = load_pickled(file_name)
    end()
    start("Routing using condensed NX")
    if benchmark:
        for source, target in load_pickled(benchmark):
            length = shortest_length_cnx(g,(source,),(target,))
    else:
        length = shortest_length_cnx(g,source_id,target_id)
    end('')
    status(length)

def shortest_length_nx(g,source_id=None,target_id=None):
    from limic.util import locate_by_id, haversine_distance
    from networkx import astar_path_length, NetworkXNoPath
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
        cost = astar_path_length(g,source,target,heuristic=distance)
    except NetworkXNoPath as e:
        cost = float('inf')
    return cost    

def length_route_nx(file_name,source_id=None,target_id=None,benchmark=None):
    from limic.util import start, end, load_pickled, status
    start("Loading from",file_name)
    g = load_pickled(file_name)
    end()
    start("Routing using NX")
    if benchmark:
        for source, target in load_pickled(benchmark):
            length = shortest_length_nx(g,(source,),(target,))
    else:
        length = shortest_length_nx(g,source_id,target_id)
    end('')
    status(length)
