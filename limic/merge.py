GRAPHS = (("file_names",),{'type':str,'nargs':'+','help':"graphs to merge",'metavar':'GRAPH'})
CACHES = (("file_names",),{'type':str,'nargs':'+','help':"caches to merge",'metavar':'CACHE'})
TARGET = (("file_name_out",),{'type':str,'help':"target file for merge result",'metavar':'TARGET'})

CONFIG = [
    ("nx",{'help':"merge NX graphs",'args':[GRAPHS,TARGET]}),
    ("cache",{'help':"merge caches",'args':[CACHES,TARGET]})
]

def merge_nx(file_names,file_name_out):
    from limic.util import start, end, file_size, status, load_pickled, save_pickled, check_overwrites
    from networkx import Graph
    if not check_overwrites(file_names,file_name_out):
        return
    g = Graph()
    for file_name_in in file_names:
        start("Loading graph from",file_name_in)
        h = load_pickled(file_name_in)
        end('')
        file_size(file_name_in)
        start("Adding",h.number_of_edges(),"edges")
        for from_node, to_node, data in h.edges(data=True):
            g.add_edge(from_node,to_node,**data)
        end('')
        status(g.number_of_edges())
    start("Saving merged graph to",file_name_out)
    save_pickled(file_name_out,g)
    end('')
    file_size(file_name_out)

def merge_cache(file_names,file_name_out):
    from limic.util import start, end, file_size, status, load_pickled, save_pickled, check_overwrites
    if not check_overwrites(file_names,file_name_out):
        return
    g = {}
    for file_name_in in file_names:
        start("Loading cache from",file_name_in)
        h = load_pickled(file_name_in)
        end('')
        file_size(file_name_in)
        start("Adding",len(h),"entries")
        g.update(h)
        end('')
        status(len(g))
    start("Saving merged cache to",file_name_out)
    save_pickled(file_name_out,g)
    end('')
    file_size(file_name_out)
