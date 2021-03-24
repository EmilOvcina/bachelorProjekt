GRAPH = (("file_name_in",),{'type':str,'help':"use graph file GRAPH",'metavar':'GRAPH'})
HTML = (("file_name_out",),{'type':str,'help':"render to file HTML",'metavar':'HTML'})
COMPONENTS = (("components",),{'type':int,'nargs':'*','help':"components to visualize (default: -1 for all)",'metavar':'COMPONENT'})
MARKERS = (("--markers",),{'action':'store_true','dest':'markers','default':False,'help':"include markers (HUGE FILE)"})
LINES = (("--lines",),{'action':'store_true','dest':'lines','default':False,'help':"include lines (HUGE FILE)"})
HOST = (("--host",),{'type':str,'dest':'host','default':'localhost','help':"hostname (default: localhost)",'metavar':'HOST'})
PORT = (("--port",),{'type':int,'dest':'port','default':5000, 'help':"port number (default: 5000)",'metavar':'PORT'})
PREFIX = (("--prefix",),{'type':str,'dest':'prefix','default':'','help':"URI prefix (default: '')",'metavar':'PREFIX'})

CONFIG = [
    ("nx",{'help':"render HTML for NX graph",'args':[HOST,PORT,PREFIX,LINES,MARKERS,GRAPH,HTML]}),
    ("cnx",{'help':"render HTML for CNX graph",'args':[HOST,PORT,PREFIX,LINES,MARKERS,GRAPH,HTML,COMPONENTS]}),
    ("npz",{'help':"render HTML for NPZ graph",'args':[HOST,PORT,PREFIX,LINES,MARKERS,GRAPH,HTML]})
]

def render_nx(file_name_in,file_name_out,markers=False,lines=False,host="localhost",port=5000,prefix=""):
    from limic.util import start, end, load_pickled, check_overwrite
    if not check_overwrite(file_name_in,file_name_out):
        return
    start("Loading NX graph",file_name_in)
    g = load_pickled(file_name_in)
    nodes = list(g.nodes())
    edges = list(g.edges.data('weight'))
    end()
    return render(g,nodes,edges,file_name_out,markers,lines,host,port,prefix)
    
def render_cnx(file_name_in,file_name_out,components=[],markers=False,lines=False,host="localhost",port=5000,prefix=""):
    from limic.util import start, end, load_pickled, check_overwrite
    if not check_overwrite(file_name_in,file_name_out):
        return
    start("Loading CNX graph",file_name_in)
    cs,_,_ = load_pickled(file_name_in)
    end()
    for i in components if components else range(len(cs)):
        nodes = list(cs[i].nodes())
        edges = list(cs[i].edges.data('weight'))
        file_out = file_name_out.split(".html")[0]+"."+str(i)+".html"
        render(cs[i],nodes,edges,file_out,markers,lines,host,port,prefix)
    
def render_npz(file_name_in,file_name_out,markers=False,lines=False,host="localhost",port=5000,prefix=""):
    from limic.util import start, end, load_npz, check_overwrite
    from numpy import column_stack
    if not check_overwrite(file_name_in,file_name_out):
        return
    start("Loading NPZ graph",file_name_in)
    g = load_npz(file_name_in)
    nodes = list(map(tuple,column_stack((g['ids'],g['lat'],g['long']))))
    edges = []
    if lines:
        id2edges = g['id2edges']
        edges_weight = g['edges_weight']
        edges_neighbor = g['edges_neighbor']
        for index in range(len(nodes)):
            left = id2edges[index]
            right = id2edges[index+1]
            me = nodes[index]
            for i in range(left,right):
                edges.append((me,nodes[edges_neighbor[i]],edges_weight[i]))
    end()
    return render(g,nodes,edges,file_name_out,markers,lines,host,port,prefix)
    
def render(g,nodes,edges,file_name_out,markers=False,lines=False,host="localhost",port=5000,prefix=""):
    from limic.util import start, end, status, file_size
    from folium import Map, Marker, Icon, PolyLine
    from folium.plugins import BeautifyIcon
    from binascii import hexlify
    from pathlib import Path
    from math import log2
    from pkg_resources import resource_string
    start("Rendering graph")
    min_lat = min_long = float('inf')
    max_lat = max_long = -float('inf')
    for n in nodes:
        if n[1] < min_lat: min_lat = n[1]
        if n[2] < min_long: min_long = n[2]
        if n[1] > max_lat: max_lat = n[1]
        if n[2] > max_long: max_long = n[2]
    m = Map()
    m.fit_bounds([(min_lat,min_long),(max_lat,max_long)])
    if markers:
        for n in nodes:
            Marker(n[1:3],icon=BeautifyIcon(icon='none',                                       iconStyle="opacity: 0.1;",borderColor='#7f7f00',backgroundColor='#ffff00'),
               tooltip=("id: %d" % n[0])).add_to(m)
    if lines:
        for u,v,weight in edges:
            PolyLine([u[1:3],v[1:3]],color="#3f3f00",opacity=0.4,weight=6,tooltip=("weight: %.1f" % weight)).add_to(m)
    TEMPLATE = resource_string("limic","render.js").decode('utf8')
    from branca.element import MacroElement, Template
    class LatLngListener(MacroElement):
        _template = Template(TEMPLATE % {'host':host,'port':port,'prefix':prefix})
        def __init__(self):
            super(MacroElement, self).__init__()
            self._name = 'LatLngListener'
    LatLngListener().add_to(m)
    end()
    start("Saving result to HTML file",file_name_out)
    # m.save(file_name_out)
    end('')
    file_size(file_name_out)
    return g,nodes
