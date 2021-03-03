from requests import get
from limic.util import distance, options
from dogpile.cache import make_region

server = "http://caracal.imada.sdu.dk/overpass"
def set_server(base_url):
    if base_url is not None:
        global server
        server = base_url

def key_generator(namespace, fn):
    namespace = "__main__:%s" % fn.__name__
    def generate_key(*args, **kw):
        if kw: raise ValueError("dogpile.cache's default key creation function does not accept keyword arguments.")
        return namespace + "|" + " ".join(map(str, args))
    return generate_key
if options.disk_cache:
    region = make_region(function_key_generator=key_generator).configure("dogpile.cache.dbm",arguments={"filename":options.disk_cache})
else:
    region = make_region(function_key_generator=key_generator).configure("dogpile.cache.memory")

class pylon:
    def __init__(self,id,latlon,neighbours=()):
        self.id = id
        self.latlon = latlon
        self.neighbours = neighbours
    def __repr__(self):
        return "pylon(id="+repr(self.id)+",latlon="+repr(self.latlon)+", neighbours="+repr(self.neighbours)+")"
    def __lt__(self,other):
        return self.latlon < other.latlon
    def __eq__(self,other):
        return isinstance(other,pylon) and self.latlon == other.latlon
    def __hash__(self):
        return hash(self.latlon)

class dist:
    def __init__(self,dist,air,tower):
        self.dist = dist
        self.air = air
        self.tower = tower
    def __lt__(self,other):
        return self.dist < other.dist
    def __repr__(self):
        return "dist(dist="+repr(self.dist)+",air="+repr(self.air)+",tower="+repr(self.tower)+")"

def overpass(query,timeout=3600,retries=10):
    from limic.util import options, status
    url = server+"/api/interpreter?data=%5Bout:json%5D%5Btimeout:3600%5D;"+query
    #if verbosity >= 2: print(url)
    while retries:
        try:
            r = get(url,timeout=timeout)
            return r.json()
        except Exception as exc:
            retries -= 1
            #if verbosity >= 4: print(exc)
            status("WARNING(overpass): RETRYING "+url)
    options.failed = True

def tower_by_id(tower_id):
    jsonfile = overpass("node(id:"+str(tower_id)+");out;")
    for child in jsonfile['elements']:
        tower = pylon(child['id'],(float(child['lat']),float(child['lon'])))
        return tower

@region.cache_on_arguments()
def find_towers(location, around):
    #from util import verbosity
    towers = []
    #if verbosity >= 2: print("finding towers close to",location)
    jsonfile = overpass("(node(around:"+str(around)+","+str(location[0])+","+str(location[1])+")%5B%22power%22=%22tower%22%5D;);out;")
    for child in jsonfile['elements']:
        tower = pylon(child['id'],(float(child['lat']),float(child['lon'])))
        towers.append(tower)
    #if verbosity >= 2: print("found",len(towers),"towers:",towers)
    return towers

@region.cache_on_arguments()
def find_segments(location, around):
    #from util import verbosity
    segments = []
    #if verbosity >= 2: print("finding lines close to",location)
    jsonfile = overpass("(way(around:"+str(around)+","+str(location[0])+","+str(location[1])+")%5B%22power%22=%22line%22%5D;node(w););out;")
    id2pos = {}
    for child in jsonfile['elements']:
        if child['type'] == "node":
            id2pos[child['id']] = (child['lat'],child['lon'])
        if child['type'] == "way":
            nodes = child['nodes']
            for i in range(1,len(nodes)):
                segments.append((nodes[i-1],nodes[i]))
    #if verbosity >= 2: print("found",len(segments),"segments:",segments)
    segments = list(map(lambda ids:(pylon(ids[0],id2pos[ids[0]]),pylon(ids[1],id2pos[ids[1]])),segments))
    return segments

def find_neighbours(tower):
    #from util import verbosity
    if tower.id < 0:
        towers = set()
        towers.update(tower.neighbours)
        #if verbosity >= 2: print("found",len(towers),"pre-defined direct neighbours:",towers)
        return towers
    return find_neighbours_id(tower)

@region.cache_on_arguments()
def find_neighbours_id(tower):
    #from util import verbosity
    #if verbosity >= 2: print("finding neighbours for",tower)
    towers = set()
    jsonfile = overpass("(node(id:"+str(tower.id)+");way(bn)%5B%22power%22=%22line%22%5D;node(w););out;")

    id2pos = {}
    for child in jsonfile['elements']:
        if child['type'] == "node" :
            id2pos[child['id']] = (child['lat'],child['lon'])
        if child['type'] == "way":
            nodes = child['nodes']
            index = nodes.index(tower.id)
            if index > 0:
                towers.add(nodes[index-1])
            if index+1 < len(nodes):
                towers.add(nodes[index+1])
    towers = list(map(lambda id:pylon(id,id2pos[id]),towers))
    #if verbosity >= 2: print("found",len(towers),"direct neighbours:",towers)
    return towers

@region.cache_on_arguments()
def around_station(location, around):
    #from util import verbosity
    #if verbosity >= 2: print("avoiding power stations less than",around,"metres from",location)
    jsonfile = overpass("(way(around:"+str(around)+","+str(location[0])+","+str(location[1])+")%5B%22power%22=%22substation%22%5D;);out;")
    for child in jsonfile['elements']:
        if child['type'] == "way":
            return True
    return False

@region.cache_on_arguments()
def find_substations(location,around):
    #from util import verbosity
    #if verbosity >= 2: print("retrieving power station geometries",around,"around",location)
    jsonfile = overpass("way(around:"+str(around)+","+str(location[0])+","+str(location[1])+")%5B%22power%22=%22substation%22%5D;out geom;")
    substations = []
    for child in jsonfile['elements']:
        if child['type'] == "way":
            geometry = list(map(lambda loc:(loc['lat'],loc['lon']),child['geometry']))
            substations.append(geometry)
    #if verbosity >= 2: print("substations:",substations)
    return substations

@region.cache_on_arguments()
def is_in(tower,geometry):
    #from util import verbosity
    #if verbosity >= 2: print("checking whether",tower,"is enclosed by",geometry)
    if tower.id < 0:
        #if verbosity >= 2: print("tower safe (is intersection):",tower)
        return False
    if len(geometry) < 3:
        #if verbosity >= 2: print("tower safe (unusable geometry):",tower)
        return False
    if len(geometry) > 100:
        #if verbosity >= 2: print("tower NOT safe (too large geometry")
        return True
    return tower.id in nodes_in_geometry(geometry)

def is_safe(tower, around):
    if not around_station(tower.latlon,around):
        return True
    for substation in find_substations(tower.latlon, around):
        if is_in(tower,substation):
            return False
    return True

def dist_towers(towers, location):
    d_towers = []
    for tower in towers:
        d = distance(location,tower.latlon)
        d_towers.append(dist(d,False,tower))
    return d_towers

def intersect(p1,p2,p3,p4,eps,no_tu=True):
    d = (p1[0]-p2[0])*(p3[1]-p4[1])-(p1[1]-p2[1])*(p3[0]-p4[0])
    if d == 0:
        return None
    t = ((p1[0]-p3[0])*(p3[1]-p4[1])-(p1[1]-p3[1])*(p3[0]-p4[0]))/d
    if t < eps or t > 1-eps:
        return None
    u = -((p1[0]-p2[0])*(p1[1]-p3[1])-(p1[1]-p2[1])*(p1[0]-p3[0]))/d
    if u < eps or u > 1-eps:
        return None
    x = ((p1[0]*p2[1]-p1[1]*p2[0])*(p3[0]-p4[0])-(p1[0]-p2[0])*(p3[0]*p4[1]-p3[1]*p4[0]))/d
    y = ((p1[0]*p2[1]-p1[1]*p2[0])*(p3[1]-p4[1])-(p1[1]-p2[1])*(p3[0]*p4[1]-p3[1]*p4[0]))/d
    return (x,y) if no_tu else (x,y),(t,u)
        
def find_all_neighbours(tower, around, eps, safe_dist, minusid, latlon2id, penalty):
    #from util import verbosity
    direct_neighbours = find_neighbours(tower)
    neighbours = dist_towers(direct_neighbours,tower.latlon)
    direct_segments = list(map(lambda neighbour:(neighbour.tower,tower),neighbours))
    indirect_neighbours = []
    for neighbour in find_towers(tower.latlon, around):
        if not neighbour in direct_neighbours and neighbour.id != tower.id:
             neighbours.append(dist(penalty*distance(neighbour.latlon,tower.latlon),True,neighbour))
        #else:
             #if verbosity >= 3: print("skipping direct neighbour/self",neighbour)
    indirect_segments = find_segments(tower.latlon, around)
    for indirect_segment in indirect_segments:
        for direct_segment in direct_segments:
            intersection = intersect(direct_segment[0].latlon,direct_segment[1].latlon,indirect_segment[0].latlon,indirect_segment[1].latlon,eps)
            if intersection:
                #if verbosity >= 3:
                #    print("found intersection",direct_segment,indirect_segment,intersection)
                #    print("node(id:"+(",".join(map(lambda t:str(t.id),[direct_segment[0],direct_segment[1],indirect_segment[0],indirect_segment[1]])))+");out;")
                if not intersection in latlon2id:
                    minusid[0] -= 1
                    latlon2id[intersection] = minusid[0]
                neighbours.append(dist(distance(intersection,tower.latlon),False,pylon(latlon2id[intersection], intersection,neighbours=indirect_segment)))
    #if verbosity >= 2: print("found a total of ",len(neighbours),"neighbours:",neighbours)
    safe_neighbours = []
    for neighbour in neighbours:
        if is_safe(neighbour.tower, safe_dist):
            safe_neighbours.append(neighbour)
        #else:
            #if verbosity >= 4: print("unsafe and skipped:",neighbour.tower)
    return safe_neighbours

def nodes_in_geometry(geometry):
    nodes = set()
    polygon = " ".join(map(lambda loc:str(loc[0])+" "+str(loc[1]),geometry))
    jsonfile = overpass("way(poly:%22"+polygon+"%22)[%22power%22=%22line%22];node(w)(poly:%22"+polygon+"%22);out;")
    for child in jsonfile['elements']:
        if child['type'] == "node":
            nodes.add(child['id'])
    return nodes

def get_towers_by_area(area):
    area_type = "addr:country" if area.isupper() else "name:en"
    query = "(area%5B%22"+area_type+"%22=%22"+area+"%22%5D;)-%3E.a;way(area.a)%5B%22power%22=%22line%22%5D;node(w);out;"
    jsonfile = overpass(query)
    towers = []
    for child in jsonfile['elements']:
        if child['type'] == "node":
            tower = pylon(child['id'],(float(child['lat']),float(child['lon'])))
            towers.append(tower)
    return towers
