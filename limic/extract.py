CACHE = (("file_name_in",),{'type':str,'help':"read map data from cache file CACHE",'metavar':'CACHE'})
LIM = (("file_name_in",),{'type':str,'help':"read map data from LiMiC file FILE",'metavar':'LIM'})
OSM = (("file_name_in",),{'type':str,'help':"read map data from OpenStreetMap file OSM",'metavar':'OSM'})
OUT = (("file_name_out",),{'type':str,'help':"save extracted graph to file GRAPH",'metavar':'GRAPH'})
EPS = (("-e","--epsilon"),{'type':float,'dest':'eps','default':0.01,'help':"set minimum percentage of  linear infrastructure segment to consider non-logical intersections to EPS",'metavar':'EPS'})
AROUND = (("-r","--around"),{'type':int,'dest':'around','default':1000,'help':"set maximum free flying distance in m around linear infrastructure nodes to AROUND",'metavar':'AROUND'})
SAFEDIST = (("-s","--safe-dist"),{'type':int,'dest':'safe_dist','default':100,'help':"set minimum safe distance from blacklisted areas and structures to SAFE",'metavar':'SAFE'})
PENALIZE = (("-p","--penalize"),{'type':int,'default':20,'dest':'penalize','help':"penalize free flying disrances by factor PENALTY",'metavar':'PENALTY'})
WHITE = (("--white",),{'type':str,'dest':'white','default':'{"power":"line"}','help':"linear infrastructure to include (default: {'power':'line'})",'metavar':'WHITELIST'})
BLACK = (("--black",),{'type':str,'dest':'black','default':'{"power":"substation"}','help':"areas and structures to avoid (default: {'power':'substation'})",'metavar':'BLACKLIST'})
CONSERVEMEM = (("-c","--conserve-memory"),{'action':'store_true','dest':'conserve_mem','default':False,'help':"lower memory usage but higher runtime"})

CONFIG = [
    ("cache",{'args':[
        (("-u","--overpass-url"),{'type':str,'dest':'overpass_url','help':"define url for Overpass API to be URL",'metavar':'URL'}),
        (("-a","--area"),{'type':str,'dest':'area','help':"set area to extract to AREA",'metavar':'AREA'}),
        AROUND,EPS,SAFEDIST,PENALIZE,CACHE,OUT
    ]}),
    ("osm",{'args':[BLACK,WHITE,CONSERVEMEM,AROUND,EPS,SAFEDIST,PENALIZE,OSM,OUT]}),
    ("osm_pre",{'args':[BLACK,WHITE,CONSERVEMEM,OSM,OUT]}),
    ("osm_post",{'args':[AROUND,EPS,SAFEDIST,PENALIZE,LIM,OUT]})
    #("esy",{'args':[OSM,OUT]})
]

def prune_incomplete(g):
    to_prune = set()
    for k in g.nodes():
        gk = g[k]
        for l in g.neighbors(k):
            if k < l and gk[l]['type'] < 0:
                gl = g[l]
                for m in g.neighbors(l):
                    if g.has_edge(k,m) and gk[l]['weight'] > gk[m]['weight']+gl[m]['weight']:
                        to_prune.add((k,l))
    for u,v in to_prune:
        if g.has_edge(u,v):
            g.remove_edge(u,v)

def prune_complete(g):
    from networkx import astar_path_length
    to_prune = set()
    for k in g.nodes():
        for l in g.neighbors(k):
            if k < l:
                gkl = g[k][l]
                if gkl['type'] < 0 and gkl['weight'] > astar_path_length(g,k,l):
                    to_prune.add((k,l))
    for u,v in to_prune:
        if g.has_edge(u,v):
            g.remove_edge(u,v)

def build_edges(g,find_all_neighbours,around,eps,safe_dist,penalize):
    from limic.overpass import pylon
    from limic.util import distance
    #count = 0
    neighbours2intersection = {}
    minusid = [0]
    latlon2id = {}
    for tower in list(g.nodes()):
        #count += 1
        #if verbosity >= 2: print(count,"of",total)
        for neighbour in find_all_neighbours(tower,around,eps,safe_dist,minusid,latlon2id,penalize):
            if neighbour.tower in g or neighbour.tower.id < 0:
                #if verbosity >= 2: print("adding",neighbour)
                g.add_edge(tower,pylon(neighbour.tower.id,neighbour.tower.latlon),weight=neighbour.dist,type=neighbour.air)
                if neighbour.tower.id < 0:
                    for intersection in neighbours2intersection.setdefault(neighbour.tower.neighbours,[]):
                        if intersection.latlon != neighbour.tower.latlon:
                            #if verbosity >= 2: print("double intersection:",intersection.latlon,neighbour.tower.latlon)
                            g.add_edge(intersection,neighbour.tower,weight=distance(intersection.latlon,neighbour.tower.latlon),type=False)
                    neighbours2intersection[neighbour.tower.neighbours].append(neighbour.tower)


def extract_cache(file_name_in,file_name_out,overpass_url,area=None,around=1000,eps=0.01,safe_dist=100,penalize=20):
    from limic.overpass import distance, find_all_neighbours, is_safe, set_server, pylon, region, get_towers_by_area
    from limic.util import start, end, file_size, status, load_pickled, save_pickled, replace, check_overwrite
    from networkx import Graph
    if not check_overwrite(file_name_in,file_name_out):
        return
    start("Loading",file_name_in)
    region.backend._cache = load_pickled(file_name_in)
    len_cache = len(region.backend._cache)
    end('')
    file_size(file_name_in)
    if not area:
        area = file_name_in.split(".")[1]
    start("Querying overpass for",area)
    set_server(overpass_url)
    towers = get_towers_by_area(area)
    end()
    start("Building safe nodes")
    g=Graph()
    for tower in towers:
        if is_safe(tower,safe_dist):
            g.add_node(tower)
#        else:
#        if verbosity >= 2: print("NOT safe!")
    end('')
    total = len(g.nodes())
    status(total)
    start("Building edges")
    build_edges(g,find_all_neighbours,around,eps,safe_dist,penalize)
    end('')
    status(len(g.edges()))
    if len_cache != len(region.backend._cache):
        file_name_tmp = file_name_in+".tmp"
        start("Saving to",file_name_in,"via",file_name_tmp)
        save_pickled(file_name_tmp,region.backend._cache)
        replace(file_name_tmp,file_name_in)
        end('')
        file_size(file_name_in)
    from limic.util import start, end, status, file_size, save_pickled
    from networkx import relabel_nodes
    start("Prune redundant edges (incomplete)")
    prune_incomplete(g)
    end('')
    status(len(g.edges()))
    start("Prune redundant edges (complete)")
    prune_complete(g)
    end('')
    status(len(g.edges()))
    start("Cleaning up graph")
    relabel = dict(map(lambda tower:(tower,(tower.id,tower.latlon[0],tower.latlon[1])),g.nodes()))
    relabel_nodes(g,relabel,copy=False)
    for u,v,d in g.edges(data=True):
        d['type'] = -1 if d['type'] else 0
    end()
    start("Saving graph to",file_name_out)
    save_pickled(file_name_out,g)
    end('')
    file_size(file_name_out)

def extract_osm(file_name_in,file_name_out,around=1000,eps=0.01,safe_dist=100,penalize=20,white="{'power':'line'}",black="{'power':'substation'}",conserve_mem=False):
    from setproctitle import setproctitle
    setproctitle(file_name_in)
    from limic.util import check_overwrite
    if not check_overwrite(file_name_in,file_name_out):
        return
    white,black = list(eval(white).items()), list(eval(black).items())
    lim = osm_pre(file_name_in,white,black,conserve_mem)
    osm_post(lim,file_name_out,around=1000,eps=0.01,safe_dist=100,penalize=20)

def extract_osm_pre(file_name_in,file_name_out,white="{'power':'line'}",black="{'power':'substation'}",conserve_mem=False):
    from limic.util import start, end, save_pickled, file_size, check_overwrite
    if not check_overwrite(file_name_in,file_name_out):
        return
    white,black = list(eval(white).items()), list(eval(black).items())
    lim = osm_pre(file_name_in,white,black,conserve_mem)
    start("Saving data to",file_name_out)
    save_pickled(file_name_out,lim)
    end('')
    file_size(file_name_out)

def extract_osm_post(file_name_in,file_name_out,around=1000,eps=0.01,safe_dist=100,penalize=20):
    from limic.util import start, end, file_size, load_pickled, check_overwrite
    if not check_overwrite(file_name_in,file_name_out):
        return
    start("Loading filtered OSM data from",file_name_in)
    lim = load_pickled(file_name_in)
    end('')
    file_size(file_name_in)
    osm_post(lim,file_name_out,around=1000,eps=0.01,safe_dist=100,penalize=20)

def osm_post(lim,file_name_out,around=1000,eps=0.01,safe_dist=100,penalize=20):
    from limic.util import start, end, status, file_size, load_pickled, distance, save_pickled
    from scipy.spatial import cKDTree as KDTree
    from networkx import Graph, astar_path_length
    from pyproj import CRS, Transformer
    from itertools import chain
    from limic.overpass import intersect, pylon
    lines, substations, towers, id2tower, id2node, id2lines, id2types = lim
    start("Building KD-tree from white nodes")
    from limic.util import kdtree
    towers_tree = kdtree(towers,get_latlon=lambda x:x.latlon)
    end('')
    status(len(towers))
    start("Deleting black nodes")
    to_delete = set()
    from limic.util import nodes_in_geometry
    for substation in substations:
        to_delete.update(nodes_in_geometry(towers_tree,list(map(lambda x:id2node[x],substation))))
    towers = [tower for tower in towers if tower not in to_delete]
    end('')
    status(len(towers))
    start("Building initial graph")
    g = Graph()
    g.add_nodes_from(towers)
    for line in lines:
        line_nodes = list(map(lambda x:id2tower[x],line))
        for from_node, to_node in zip(line_nodes,line_nodes[1:]):
            if from_node in to_delete or to_node in to_delete:
                continue
            w = distance(from_node.latlon,to_node.latlon)
            g.add_edge(from_node,to_node,weight=w,type=id2types[from_node.id])
    end('')
    status(len(g.nodes()),end='/')
    status(len(g.edges()))
    start("Finding neighbours within "+str(around)+"m")
    towers_tree = kdtree(towers,get_latlon=lambda x:x.latlon)
    end('')
    neighbour_indices, neighbours = towers_tree.get_neighbours(around=1000)
    end()
    start("Computing non-logical intersections")
    tower2index = {}
    for i,t in zip(range(len(towers)),towers):
        tower2index[t] = i
    for k,v in id2lines.items():
        id2lines[k] = tuple(map(tuple,v))
    end('')
    segments = set()
    for u,v in g.edges():
        this = (u,v) if u < v else (v,u)
        ui, vi = tower2index[u], tower2index[v]
        lines = set()
        lines.update(id2lines[u.id])
        lines.update(id2lines[v.id])
        for neighbour in chain(neighbours[ui],neighbours[vi]):
            if neighbour == u or neighbour == v:
                continue
            if not lines.intersection(id2lines[neighbour.id]):
                for nn in g.neighbors(neighbour):
                    other = (neighbour,nn) if neighbour < nn else (nn,neighbour)
                    segments.add(tuple(sorted((this,other))))
    end('')
    status(len(segments),end='   ')
    neighbours2intersection = {}
    minusid = 0
    latlon2id = {}
    segments2intersections = {}
    for (t1,t2),(t3,t4) in segments:
        res = intersect(t1.latlon,t2.latlon,t3.latlon,t4.latlon,eps=eps,no_tu=False)
        if res:
            intersection,(t,u) = res
            if not intersection in latlon2id:
                minusid -= 1
                latlon2id[intersection] = minusid
            segments2intersections.setdefault((t1,t2),[]).append((t,latlon2id[intersection],intersection))
            segments2intersections.setdefault((t3,t4),[]).append((u,latlon2id[intersection],intersection))
    end('')
    status(-minusid,end='   ')
    for (u,v), intersections in segments2intersections.items():
        intersections.sort()
        g.remove_edge(u,v)
        type = id2types[u.id]
        assert(type == id2types[v.id])
        seq = [u]
        for _,id,latlon in intersections:
            seq.append(pylon(id,latlon))
        seq.append(v)
        for from_node, to_node in zip(seq,seq[1:]):
            w = distance(from_node.latlon,to_node.latlon)
            g.add_edge(from_node,to_node,weight=w,type=type)
    end()
    start("Adding routing through air")
    airs = set()
    for ns in neighbours:
        n = ns[0]
        for m in ns[1:]:
            if not g.has_edge(n,m):
                airs.add((n,m))
    end('')
    for n,m in airs:
        w = penalize*distance(n.latlon,m.latlon)
        g.add_edge(n,m,weight=w,type=-1)
    end('')
    status(len(g.nodes()),end='/')
    status(len(g.edges()))
    from networkx import relabel_nodes
    start("Prune redundant edges (incomplete)")
    prune_incomplete(g)
    end('')
    status(len(g.edges()))
    start("Prune redundant edges (complete)")
    prune_complete(g)
    end('')
    status(len(g.edges()))
    start("Cleaning up graph")
    relabel = dict(map(lambda tower:(tower,(tower.id,tower.latlon[0],tower.latlon[1])),g.nodes()))
    relabel_nodes(g,relabel,copy=False)
    end()
    start("Saving graph to",file_name_out)
    save_pickled(file_name_out,g)
    end('')
    file_size(file_name_out)

def osm_pre(file_name_in,white=[("power","line")],black=[("power","substation")],conserve_mem=False):
    from limic.util import start, end, status, file_size, split, file_copy
    from bz2 import open as bopen
    from limic.overpass import pylon
    white = list(map(lambda x:(x[0],x[1][0]+'" v="'+x[1][1]+'"'),zip(range(len(white)),white)))
    black = list(map(lambda x:(-1,x[0]+'" v="'+x[1]+'"'),black))
    white_black = white+black
    if not conserve_mem:
        start("Reading map data from",file_name_in)
        from mmap import mmap
        area = mmap(-1,2**40)
        if file_name_in[-4:] == ".bz2":
            try:
                from subprocess import Popen, PIPE
                f = Popen(['lbzcat',file_name_in],stdout=PIPE).stdout
            except Exception as e:
                print(e)
                status("WARNING: lbzcat failed - falling back on Python bz2 library")
                f = bopen(file_name_in,"rb")
        else:
            f = open(file_name_in,"rb")
        file_copy(f,area)
        f.close()
        area_length = area.tell()
        end()
    start("Extracting ways for white and black")
    if conserve_mem:
        f = bopen(file_name_in,"rb") if file_name_in[-4:] == ".bz2" else open(file_name_in,"rb")
        elems = split(f,'\n  <')
    else:
        area.seek(0)
        elems = split(area,'\n  <',maxlength=area_length)
    lines = []
    substations = []
    id2types = {}
    for elem in elems:
        if elem.startswith('way id="'):
            found = False
            for i,t in white_black:
                if t in elem:
                    found = True
            if not found:
                continue
            tags = elem.split('\n    <tag k="')
            for tag in tags[1:]:
                for i,t in white_black:
                    if tag.startswith(t):
                        nds = list(map(lambda x:int(x.split('"')[0]),tags[0].split('\n    <nd ref="')[1:]))
                        if i >= 0:
                            lines.append(nds)
                            for nd in nds:
                                id2types[nd] = i
                        else:
                            substations.append(nds)
    end('')
    status(len(lines),end='   ')
    status(len(substations))
    id2lines, id2substations = {}, {}
    for line in lines:
        for node in line:
            id2lines.setdefault(node,[]).append(line)
    for substation in substations:
        for node in substation:
            id2substations.setdefault(node,[]).append(substation)
    start("Extracting nodes for white and black")
    if conserve_mem:
        f = bopen(file_name_in,"rb") if file_name_in[-4:] == ".bz2" else open(file_name_in,"rb")
        elems = split(f,'\n  <')
    else:
        area.seek(0)
        elems = split(area,'\n  <',maxlength=area_length)
    towers = []
    id2tower = {}
    id2node = {}
    ids = set()
    ids.update(map(lambda x:str(x),id2lines.keys()))
    ids.update(map(lambda x:str(x),id2substations.keys()))
    for elem in elems:
        if elem.startswith('node id="'):
            if not elem[9:elem.find('"',10)] in ids:
                continue
            parts = elem.split("\n")[0].split('"')
            assert(parts[-5]==' lat=')
            assert(parts[-3]==' lon=')
            i = int(parts[1])
            if i in id2lines:
                elem = pylon(i,(float(parts[-4]),float(parts[-2])))
                towers.append(elem)
                id2tower[i] = elem
            if i in id2substations:
                elem = (float(parts[-4]),float(parts[-2]))
                id2node[i] = elem
    end('')
    status(len(towers))
    start("Checking all nodes were extracted")
    assert(set(id2lines.keys())==set(map(lambda x:x.id,towers)))
    end()
    return lines, substations, towers, id2tower, id2node, id2lines, id2types
