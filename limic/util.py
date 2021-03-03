# arguments
def parse_config(config, parser, prefix):
    subs = None
    for a,b in config:
        if isinstance(a,str):
            if not subs:
                subs = parser.add_subparsers(dest='command',required=True)
            args = b.pop('args') if 'args' in b else None
            sub = subs.add_parser(a,**b)
            if not prefix:
                sub.set_defaults(mod="limic."+a)
            sub.set_defaults(func="_".join(prefix+[a]))
            if args:
                parse_config(args, sub, prefix+[a])
        else:
            parser.add_argument(*a, **b)

# global options
from argparse import Namespace
options = Namespace()
options.verbosity = 1
options.md5sum = False
options.overwrite = False
options.parser = None
options.disk_cache = None
options.failed = False
def set_option(k,v):
    if k is not None:
        vars(options)[k] = v

# timing and informational messages
import time
started = 0
def start(*msg):
    if options.verbosity > 0:
        global started
        if msg:
            print(" ".join(map(str,msg)).ljust(60),"... ",end='',flush=True)
        started = time.time()
def end(end='\n'):
    if options.verbosity > 0:
        global started
        print("%.3f seconds   " % (time.time()-started),end=end,flush=True)
        started = time.time()
def file_size(file_name,end='\n'):
    from os import stat
    if options.verbosity > 0:
        print("%.0fK" % (stat(file_name).st_size/1024),end=end)
def status(msg,end='\n'):
    if options.verbosity > 0:
        print(msg,end=end)


# distance between GPS positions and other geo stuff
from math import radians, cos, sin, asin, sqrt
def haversine_distance(longx,latx,longy,laty):
    lon1, lat1, lon2, lat2 = radians(longx), radians(latx), radians(longy), radians(laty)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    m = 6371008.7714*c
    return m
def distance(x,y):
    return haversine_distance(longx=x[1],latx=x[0],longy=y[1],laty=y[0])
def nodes_in_geometry(tree,polygon):
    from limic.util import distance
    from shapely.geometry import Point, Polygon
    southwest,middle,_ = bounds_center(polygon)
    radius = distance(southwest,middle)
    candidates = tree.query(middle,radius)
    get_latlon = tree.get_latlon
    return [candidate for candidate in candidates if Point(*get_latlon(candidate)).within(Polygon(polygon))]
def bounds_center(polygon):
    min_lat = min_lon = float('inf')
    max_lat = max_lon = -float('inf')
    for lat,lon in polygon:
        if lat < min_lat: min_lat = lat
        if lon < min_lon: min_lon = lon
        if lat > max_lat: max_lat = lat
        if lon > max_lon: max_lon = lon
    ctr_lat = (min_lat+max_lat)/2
    ctr_lon = (min_lon+max_lon)/2
    return (min_lat,min_lon),(ctr_lat,ctr_lon),(max_lat,max_lon)
class kdtree():
    def __init__(self,nodes,get_latlon=id,transformer=None):
        if transformer:
            self.transformer = transformer
        else:
            from pyproj import CRS, Transformer
            self.transformer = Transformer.from_crs(CRS("WGS84"),CRS("EPSG:28992"))
        if nodes:
            from scipy.spatial import cKDTree as KDTree
            self.nodes = list(nodes)
            self.tree = KDTree(list(map(lambda x:self.transformer.transform(*get_latlon(x)),self.nodes)))
        else:
            self.nodes = self.tree = None
        self.get_latlon = get_latlon
    def query(self,node,around,get_latlon=lambda x:x):
        if not self.tree:
            return []
        latlon = get_latlon(node)
        projected = self.transformer.transform(*latlon)
        indices = self.tree.query_ball_point(projected,r=around)
        results = list(map(lambda x:self.nodes[x],indices))
        return results
    def get_neighbours(self,around):
        if not self.tree:
            return []
        indicess = self.tree.query_ball_tree(self.tree,r=around)
        results = list(map(lambda indices:list(map(lambda x:self.nodes[x],indices)),indicess))
        return indicess,results

# working with different graph formats
def nx_is_equal(g,h,isomorphic=False):
    from networkx.algorithms.isomorphism import is_isomorphic
    if isomorphic:
        return is_isomorphic(g,h,lambda ga,ha:ga==ha)
    g_edges, h_edges = g.edges(), h.edges()
    return all(h_edge in g_edges for h_edge in h_edges) and all(g_edge in h_edges for g_edge in g_edges)
def locate_by_id(ids,source_id=None,target_id=None,length=None):
    if not length:
        length = len(ids)
    from random import randrange
    source = None if source_id else randrange(length)
    target = None if target_id else randrange(length)
    for i in range(length):
        if source:
            if target:
                return source,target
            if ids[i] == target_id:
                target = i
                continue
        else:
            if target:
                if ids[i] == source_id:
                    source = i
                    continue
            else:
                if ids[i] == source_id:
                    source = i
                if ids[i] == target_id:
                    target = i
    assert False, "cannot resolve all ids: %s,%s -> %s,%s" % tuple(map(str,(source_id,target_id,source,target)))

# loading and saving different formats
def check_overwrite(file_name_in,file_name_out):
    return check_overwrites([file_name_in],file_name_out)
def check_overwrites(file_names,file_name_out):
    if not options.md5sum or options.overwrite:
        return True
    from os.path import exists, getmtime
    if not exists(file_name_out):
        return True
    out_mtime = getmtime(file_name_out)
    for file_name_in in file_names:
        if getmtime(file_name_in) > out_mtime:
            return True
    if not check_md5_internal(file_name_out) is None:
        return True
    status("INFO(overwrite): SKIPPING generation of "+file_name_out+" as it is newer than "+(" ".join(file_names)))
    return False
def replace(file_name_in,file_name_out):
    from os import replace
    from os.path import exists
    replace(file_name_in,file_name_out)
    if exists(file_name_in+".md5"):
        replace(file_name_in+".md5",file_name_out+".md5")
def md5file(file_name):
    from hashlib import md5
    from os.path import exists
    if not exists(file_name):
        from sys import exit
        status("ERROR(md5file): could not find "+file_name)
        exit(-1)
    f = open(file_name,"rb")
    sum = md5(f.read()).hexdigest()
    f.close()
    return sum
def check_md5_internal(file_name):
    from os.path import exists
    if not exists(file_name+".md5"):
        return "notexists"
    f = open(file_name+".md5")
    md5_1 = f.read().split()[0]
    f.close()
    md5_2 = md5file(file_name)
    if md5_1 != md5_2:
        return "notequal"
    return None
def check_md5(file_name):
    if options.md5sum:
        res = check_md5_internal
        if res == "notexists":
            from sys import exit
            status("ERROR(md5file): could not find "+file_name+".md5")
            exit(-1)
        if res == "notequal":
            from sys import exit
            status("ERROR(md5): "+md5_1+" vs "+md5_2)
            exit(-1)
def save_md5(file_name):
    if options.md5sum:
        f = open(file_name+".md5","wt")
        f.write(md5file(file_name)+" "+file_name)
        f.close()
def save_pickled(file_name,g,compression="gzip",protocol=4):
    from pickle import dump
    if compression:
        from gzip import open as gopen
        f = gopen(file_name,"wb")
    else:
        f = open(file_name,"wb")
    dump(g,f,protocol=protocol)
    f.close()
    save_md5(file_name)
def load_pickled(file_name,compression="gzip"):
    check_md5(file_name)
    from pickle import Unpickler
    class RenameUnpickler(Unpickler):
        def find_class(self, module, name):
            renamed_module = module
            if module == "overpass":
                renamed_module = "limic.overpass"
            return super(RenameUnpickler, self).find_class(renamed_module, name)
    #from pickle import load
    def load(f):
        return RenameUnpickler(f).load()
    if compression:
        from gzip import open as gopen
        f = gopen(file_name,"rb")
    else:
        f = open(file_name,"rb")
    g = load(f)
    f.close()
    return g
def save_gt(file_name,g):
    g.save(file_name,fmt="gt")
    save_md5(file_name)
def load_gt(file_name):
    check_md5(file_name)
    from graph_tool import Graph
    g = Graph()
    g.load(file_name,fmt="gt")
    return g
def load_npz(file_name):
    check_md5(file_name)
    from numpy import load
    return load(file_name)
def save_npz(file_name,g):
    from numpy import savez
    savez(file_name,**g)
    save_md5(file_name)
def save_path(costpath,out_file=None,visualize=False):
    from sys import stdout
    if visualize and not out_file:
        status("WARNING (use --output to specify HTML file)   ",end='')
        visualize = False
    cost,path = costpath
    if visualize:
        from folium import Map, Marker, Icon, PolyLine
        from folium.plugins import BeautifyIcon
        from binascii import hexlify
        from webbrowser import open as wopen
        from pathlib import Path
        from math import log2
        min_lat = min_long = float('inf')
        max_lat = max_long = -float('inf')
        for x in path:
            if x[4] < min_lat: min_lat = x[4]
            if x[5] < min_long: min_long = x[5]
            if x[4] > max_lat: max_lat = x[4]
            if x[5] > max_long: max_long = x[5]
        m = Map()
        m.fit_bounds([(min_lat,min_long),(max_lat,max_long)])
        start_color = (63,255,63)
        end_color = (63,63,255)
        diff_color = tuple(map(lambda x:x[0]-x[1],zip(end_color,start_color)))
        length = float(len(path))
        for i in range(len(path)):
            x = path[i]
            background_color = "#"+hexlify(bytes(map(lambda x:int(x[0]+i*x[1]/length),zip(start_color,diff_color)))).decode('utf8')
            border_color = "#"+hexlify(bytes(map(
                lambda x:int((x[0]+i*x[1]/length)/2),zip(start_color,diff_color)))).decode('utf8')
            line_color = background_color
            line_weight = 6
            icon = None
            iconStyle = ""
            if x[3] < 0:
                icon = 'times'
                background_color = "#ffff3f"
                border_color = "#7f1f1f"
            elif x[2]:
                icon = 'flash'
                background_color = "#ff0000"
                border_color = "#7f0000"
                line_color = background_color
                line_weight = 10
            elif i+1 < len(path) and path[i+1][2]:
                icon = 'flash'
                background_color = "#ff0000"
                border_color = "#7f0000"
            elif i == 0 or i+1 == len(path):
                icon = 'flash'
            else:
                icon = 'none'
                iconStyle = "opacity: 0.1;"
            if i > 0 and cost is not None:
                PolyLine([path[i-1][4:6],path[i][4:6]],color=line_color,opacity=0.4,weight=line_weight).add_to(m)
            if icon:
                Marker(x[4:6],icon=BeautifyIcon(icon=icon,
                                                iconStyle=iconStyle,
                                            borderColor=border_color,
                                            backgroundColor=background_color),
                   popup=("cost: %.1fm, dist: %.1fm, air: %r, id: %d" % x[:4])).add_to(m)
        m.save(out_file)
        wopen(Path(out_file).resolve().as_uri(),new=2)
    else:
        file = open(out_file,"w") if out_file else stdout
        print("node(id:"+",".join(map(lambda x:str(x[3]),path))+");out;",file=file)
def split(file,sep=None,maxsplit=-1,chunk=2**16,maxlength=None):
    rest = ""
    total = 0
    while True:
        data = file.read(chunk).decode('latin-1')
        total += len(data)
        if maxlength and total > maxlength:
            data = data[:-(total-maxlength)]
            chunk = 0
        if not data:
            break
        if rest:
            data = rest+data            
        parts = data.split(sep=sep,maxsplit=maxsplit)
        rest = parts.pop()
        for part in parts:
            yield part
    yield rest
def file_copy(f,g,chunk=2**16):
    while True:
        data = f.read(chunk)#.encode('utf8')
        if not data:
            break
        g.write(data)
