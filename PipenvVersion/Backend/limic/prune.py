OVERPASS = (("-u","--overpass-url"),{'type':str,'dest':'overpass_url','help':"define url for Overpass API to be URL (default: http://caracal.imada.sdu.dk/)",'metavar':'URL'})
IN = (("file_name_in",),{'type':str,'help':"read graph data from file GRAPH",'metavar':'GRAPH'})
OUT = (("file_name_out",),{'type':str,'help':"save extracted graph to file GRAPH",'metavar':'GRAPH'})    
COORDS = (("polygon",),{'type':str,'nargs':'+','help':"coordinate pairs that describe geometry",'metavar':'LAT LON'})

CONFIG = [
    ("nx",{'help':"prune NX graph",'args':[OVERPASS,IN,OUT,COORDS]}),
    ("gt",{'help':"prune GT graph",'args':[OVERPASS,IN,OUT,COORDS]}),
    ("npz",{'help':"prune NPZ graph",'args':[OVERPASS,IN,OUT,COORDS]}),
]
import kml2geojson
import pygeoj
import geojson
import shapely.wkt


class polygon_class:
    def __init__(self, name):
        self.name=name
        self.polygon_list=[]

    def add_polygon(self, item):
        self.polygon_list.append(item)
class pylon_item:
    def __init__(self,lat,lon):
        self.lat=lat
        self.lon=lon
        

def prune_ids_nx(g,delete_ids):
    to_delete = []
    delete_ids = set(delete_ids)
    for n in g.nodes():
        if n[0] in delete_ids:
            to_delete.append(n)
    for n in to_delete:
        g.remove_node(n)
    return g

def prune_nx(file_name_in,file_name_out,polygon,overpass_url):
    from limic.util import start, end, file_size, status, save_pickled, load_pickled, check_overwrite
    if not check_overwrite(file_name_in,file_name_out):
        return
    start("Loading from",file_name_in)
    g = load_pickled(file_name_in)
    end('')
    file_size(file_name_in)
    polygon = list(map(float,polygon))
    polygon = list(zip(polygon[::2], polygon[1::2]))
    if not overpass_url:
        from limic.util import kdtree, nodes_in_geometry
        start("Building kd-tree from nodes")
        tree = kdtree(g.nodes(),get_latlon=lambda x:(x[1],x[2]))
        end()
        start("Querying tree for nodes in polygon")
        nodes = nodes_in_geometry(tree,polygon)
        end('')
        status(len(nodes))
        start("Pruning graph")
        for n in nodes:
            g.remove_node(n)
        h = g
        end()
    else:
        from limic.overpass import nodes_in_geometry, set_server
        start("Query server for nodes in polygon")
        set_server(overpass_url)
        nodes = nodes_in_geometry(polygon)
        end('')
        status(len(nodes))
        start("Pruning graph")
        h = prune_ids_nx(g,nodes)
        end()
    start("Saving to",file_name_out)
    save_pickled(file_name_out,h)
    end('')
    file_size(file_name_out)
    
def prune_ids_gt(g,delete_ids):
    to_delete = []
    ids = g.get_vertices([g.vp.id])
    for v in ids:
        if v[1] in delete_ids:
            to_delete.append(g.vertex(v[0]))
    to_delete.reverse()
    for v in to_delete:
        g.remove_vertex(v)
    return g

def prune_gt(file_name_in,file_name_out,polygon,overpass_url):
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
    start("Pruning graph")
    h = prune_ids_gt(g,nodes)
    end()
    start("Saving to",file_name_out)
    save_gt(file_name_out,h)
    end('')
    file_size(file_name_out)

def prune_ids_npz(g,delete_ids):
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
        if g_ids[g_index] in delete_ids:
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
    
    
def convertkml_Geojson():
 #convert kml file to geojson
 kml2geojson.convert('export.kml','')
 list_polygons=[]
 with open("export.geojson") as f:
     gj = geojson.load(f)
 for j in range(0,len(gj['features'])):
    features = gj['features'][j]
    name=features['properties']['name']
    coordinates=features['geometry']
    if coordinates.get('coordinates'):
       polygon_=features['geometry']['coordinates'][0]
       item=polygon_class(name)
       for i in range(0,len(polygon_)):
          item.add_polygon(polygon_[i])
       list_polygons.append(item)
    else:
        lengh=len(features['geometry']['geometries']) 
        for k in range(0,lengh):
            polygon_=features['geometry']['geometries'][k]['coordinates']
            item=polygon_class(name)
            for p in range(0,len(polygon_)):
                item.add_polygon(polygon_[p])
            list_polygons.append(item)
 outcome="["
 towerList = []
 for q in range(0, 2):
     data=list_polygons[q].polygon_list  
     for x in range(0,2):
         
         LAT=data[x][1]
         Lon=data[x][0]
         pylon_data = pylon_item(LAT,Lon)
         outcome +=str(LAT) +" "+str(Lon)+" " 
         
         towerList.append(pylon_data)

 return outcome; 
 

def prune_npz(file_name_in,file_name_out,polygon,overpass_url):
    from limic.util import start, end, file_size, status, save_npz, load_npz, check_overwrite
    if not check_overwrite(file_name_in,file_name_out):
        return
    start("Loading from",file_name_in)
    g = load_npz(file_name_in)
    end('')
    file_size(file_name_in)
    if not overpass_url:
        from limic.util import kdtree, nodes_in_geometry
        start("Building kd-tree from nodes")
        nodes = list(zip(g["ids"],g["lat"],g["lon"]))
        tree = kdtree(nodes,get_latlon=lambda x:(x[1],x[2]))
        end()
        start("Querying tree for nodes in polygon")
        nodes = nodes_in_geometry(tree,polygon)
        nodes = [n[0] for n in nodes]
    else:
        from limic.overpass import nodes_in_geometry, set_server
        start("Query server for nodes in polygon")
        set_server(overpass_url)
        nodes = nodes_in_geometry(zip(polygon[::2], polygon[1::2]))
    end('')
    status(len(nodes))
    start("Pruning graph")
    h = prune_ids_npz(g,nodes)
    end()
    start("Saving to",file_name_out)
    save_npz(file_name_out,h)
    end('')
    file_size(file_name_out)
