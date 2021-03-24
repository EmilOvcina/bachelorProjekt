OVERPASS = (("-u","--overpass-url"),{'type':str,'dest':'overpass_url','help':"define url for Overpass API to be URL (default: http://caracal.imada.sdu.dk/)",'metavar':'URL'})
IN = (("file_name_in",),{'type':str,'help':"read map data from cache file CACHE",'metavar':'CACHE'})
OUT = (("file_name_out",),{'type':str,'help':"save extracted graph to file GRAPH",'metavar':'GRAPH'})    
COORDS = (("polygon",),{'type':str,'nargs':'+','help':"coordinate pairs that describe geometry",'metavar':'LAT LON'})

CONFIG = [
    ("nx",{'help':"select area from NX graph",'args':[OVERPASS,IN,OUT,COORDS]}),
    ("gt",{'help':"select area from GT graph",'args':[OVERPASS,IN,OUT,COORDS]}),
    ("npz",{'help':"select area from NPZ graph",'args':[OVERPASS,IN,OUT,COORDS]}),
]

def select_ids_nx(g,delete_ids):
    to_delete = []
    for n in g.nodes():
        if not n[0] in delete_ids:
            to_delete.append(n)
    for n in to_delete:
        g.remove_node(n)
    return g

def select_nx(file_name_in,file_name_out,polygon,overpass_url):
    from limic.util import start, end, file_size, status, save_pickled, load_pickled, check_overwrite
    from limic.overpass import nodes_in_geometry, set_server
    if not check_overwrite(file_name_in,file_name_out):
        return
    start("Loading from",file_name_in)
    g = load_pickled(file_name_in)
    end('')
    file_size(file_name_in)
    start("Query server for nodes in polygon")
    set_server(overpass_url)
    nodes = nodes_in_geometry(zip(polygon[::2], polygon[1::2]))
    end('')
    status(len(nodes))
    start("Selecting area from graph")
    h = select_ids_nx(g,nodes)
    end()
    start("Saving to",file_name_out)
    save_pickled(file_name_out,h)
    end('')
    file_size(file_name_out)
    
def select_ids_gt(g,delete_ids):
    to_delete = []
    ids = g.get_vertices([g.vp.id])
    for v in ids:
        if not v[1] in delete_ids:
            to_delete.append(g.vertex(v[0]))
    to_delete.reverse()
    for v in to_delete:
        g.remove_vertex(v)
    return g

def select_gt(file_name_in,file_name_out,polygon,overpass_url):
    from limic.util import start, end, file_size, status, save_gt, load_gt, check_overwrite
    from limic.overpass import nodes_in_geometry, set_server
    if not check_overwrite(file_name_in,file_name_out):
        return
    start("Loading from",file_name_in)
    g = load_gt(file_name_in)
    end('')
    file_size(file_name_in)
    start("Query server for nodes in polygon")
    set_server(overpass_url)
    nodes = nodes_in_geometry(zip(polygon[::2], polygon[1::2]))
    end('')
    status(len(nodes))
    start("Selecting area from graph")
    h = select_ids_gt(g,nodes)
    end()
    start("Saving to",file_name_out)
    save_gt(file_name_out,h)
    end('')
    file_size(file_name_out)

def select_ids_npz(g,delete_ids):
    from numpy import array, int64, int32, float64, float32
    g_ids = g['ids']
    g_lat = g['lat']
    g_long = g['long']
    g_id2edges = g['id2edges']
    g_edges_weight = g['edges_weight']
    g_edges_neighbor = g['edges_neighbor']
    h_ids = []
    h_lat = []
    h_long = []
    h_id2edges = []
    h_edges_weight = []
    h_edges_neighbor = []
    g2h = {}
    h_index = 0
    for g_index in range(len(g_ids)):
        if not g_ids[g_index] in delete_ids:
            continue
        g2h[g_index] = h_index
        h_ids.append(g_ids[g_index])
        h_lat.append(g_lat[g_index])
        h_long.append(g_long[g_index])
        h_index += 1
    h_edge_index = 0
    for g_index in range(len(g_ids)):
        if g_index not in g2h:
            continue
        h_id2edges.append(h_edge_index)
        g_edge_index = g_id2edges[g_index]
        g_edge_index_next = g_id2edges[g_index+1]
        while g_edge_index < g_edge_index_next:
            neighbor = g_edges_neighbor[g_edge_index]
            if neighbor in g2h:
                h_edges_weight.append(g_edges_weight[g_edge_index])
                h_edges_neighbor.append(g2h[neighbor])
                h_edge_index += 1
            g_edge_index += 1
            assert(h_edge_index == len(h_edges_weight))
    h_id2edges.append(h_edge_index)
    h = {}
    h['ids'] = array(h_ids,dtype=int64)
    h['lat'] = array(h_lat,dtype=float64)
    h['long'] = array(h_long,dtype=float64)
    h['id2edges'] = array(h_id2edges,dtype=int32)
    h['edges_weight'] = array(h_edges_weight,dtype=float32)
    h['edges_neighbor'] = array(h_edges_neighbor,dtype=int32)
    return h

def select_npz(file_name_in,file_name_out,polygon,overpass_url):
    from limic.util import start, end, file_size, status, save_npz, load_npz, check_overwrite
    from limic.overpass import nodes_in_geometry, set_server
    if not check_overwrite(file_name_in,file_name_out):
        return
    start("Loading from",file_name_in)
    g = load_npz(file_name_in)
    end('')
    file_size(file_name_in)
    start("Query server for nodes in polygon")
    set_server(overpass_url)
    nodes = nodes_in_geometry(zip(polygon[::2], polygon[1::2]))
    end('')
    status(len(nodes))
    start("Selecting area from graph")
    h = select_ids_npz(g,nodes)
    end()
    start("Saving to",file_name_out)
    save_npz(file_name_out,h)
    end('')
    file_size(file_name_out)
