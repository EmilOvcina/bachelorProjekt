COUNTRIES = (("countries",),{'type':str,'nargs':'+','help':"countries to work on",'metavar':'COUNTRY'})
OVERPASS = (("-u","--overpass-url"),{'type':str,'dest':'overpass_url','help':"define url for Overpass API to be URL",'metavar':'URL'})
NOGT = (("-g","--no-graph-tool"),{'action':'store_true','dest':'no_gt','default':False,'help':"do not perform graph_tool tests"})
URL = (("-d","--download-url"),{'type':str,'dest':'url','help':"define url for download directory to be URL",'metavar':'URL'})
SHOW = (("-l","--list"),{'action':'store_true','dest':'show','default':False,'help':"list available countries (default: False)"})
CONSERVEMEM = (("-c","--conserve-memory"),{'action':'store_true','dest':'conserve_mem','default':False,'help':"lower memory usage but higher runtime"})
WORKERS = (("-w","--max-workers"),{'type':int,'dest':'max_workers','help':"set maximum number of parallel workers to WORKERS",'metavar':'WORKERS'})

CONFIG = [
    ("stage0",{'help':"generate map data and all graph files (VERY SLOW)",'args':[SHOW,OVERPASS,NOGT,URL,COUNTRIES]}),
    ("stage1",{'help':"download map data and generate all graph files (SLOW)",'args':[
        ("cache",{'help':"cache files from Overpass API",'args':[SHOW,OVERPASS,NOGT,URL,COUNTRIES]}),
        ("osm",{'help':"compressed XML from GeoFabrik",'args':[SHOW,CONSERVEMEM,NOGT,WORKERS,URL,COUNTRIES]})
    ]}),
    ("stage2",{'help':"download NX graph files and other graph files",'args':[SHOW,NOGT,URL,COUNTRIES]}),
    ("stage3",{'help':"download all graph files (RECOMMENDED)",'args':[SHOW,NOGT,URL,COUNTRIES]})
]

def fill_all(overpass_url,countries):
    from limic.fill import fill
    for country in countries:
        file_name = "cache."+country
        fill(overpass_url,file_name=file_name,area=None,around=1000,eps=0.01,safe_dist=100,penalize=20,max_workers=None)

def extract_cache_all(overpass_url,countries):
    from limic.extract import extract_cache
    for country in countries:
        file_name_in = "cache."+country
        file_name_out = "graph."+country+".nx"
        extract_cache(file_name_in,file_name_out,overpass_url,area=None,around=1000,eps=0.01,safe_dist=100,penalize=20)

def extract_osm_all(countries,conserve_mem=False,max_workers=None):
    from limic.extract import extract_osm
    from concurrent.futures import ProcessPoolExecutor, wait
    if max_workers:
        executor = ProcessPoolExecutor(max_workers=max_workers)
        fs = []
    for country in countries:
        file_name_in = country+"-latest.osm.bz2"
        file_name_out = "graph."+country+".nx"
        if max_workers:
            fs.append(executor.submit(extract_osm,file_name_in,file_name_out,around=1000,eps=0.01,safe_dist=100,penalize=20,conserve_mem=conserve_mem))
        else:
            extract_osm(file_name_in,file_name_out,around=1000,eps=0.01,safe_dist=100,penalize=20,conserve_mem=conserve_mem)
    if max_workers:
        running = len(fs)
        total = running
        while running:
            print("Waiting for",running,"out of",total,"processes ...")
            wait(fs,timeout=10)
            running = sum(0 if f.done() else 1 for f in fs)

def convert_nx_gt_all(countries):
    from limic.convert import convert_nx_gt
    for country in countries:
        file_name_in = "graph."+country+".nx"
        file_name_out = "graph."+country+".gt"
        convert_nx_gt(file_name_in,file_name_out)

def convert_nx_npz_all(countries):
    from limic.convert import convert_nx_npz
    for country in countries:
        file_name_in = "graph."+country+".nx"
        file_name_out = "graph."+country+".npz"
        convert_nx_npz(file_name_in,file_name_out)

def convert_gt_npz_all(countries):
    from limic.convert import convert_gt_npz
    for country in countries:
        file_name_in = "graph."+country+".gt"
        file_name_out = "graph."+country+".npz"
        convert_gt_npz(file_name_in,file_name_out)

def merge_all(countries):
    from limic.merge import merge_nx
    from limic.convert import convert_nx_npz
    file_names = list(map(lambda country:"graph."+country+".nx",countries))
    merge_nx(file_names,"merged.Europe.nx")
    convert_nx_npz("merged.Europe.nx","merged.Europe.npz")

def convert_merge_all(countries,no_gt):
    if no_gt:
        convert_nx_npz_all(countries)
    else:
        convert_nx_gt_all(countries)
        convert_gt_npz_all(countries)
    if len(countries) >= 2:
        merge_all(countries)

def init_stage0(overpass_url,countries,no_gt,url=None,show=False):
    from limic.download import common
    countries, url = common(countries,url,show)
    fill_all(overpass_url,countries)
    extract_cache_all(overpass_url,countries)
    convert_merge_all(countries,no_gt)

def init_stage1_cache(overpass_url,countries,no_gt,url=None,show=False):
    from limic.download import download_cache, common
    countries, url = common(countries,url,show)
    download_cache(countries,url=url)
    extract_cache_all(overpass_url,countries)
    convert_merge_all(countries,no_gt)

def init_stage1_osm(countries,no_gt,url=None,show=False,conserve_mem=False,max_workers=None):
    from limic.download import download_osm, common
    from limic.util import start, status
    from os import cpu_count
    if not max_workers:
        max_workers = cpu_count()*4
    start("Number of workers")
    status(max_workers)
    download_osm(countries,url=url,show=show,max_workers=max_workers)
    countries, url = common(countries,url,show,osm=True)
    extract_osm_all(countries,conserve_mem=conserve_mem,max_workers=max_workers)
    convert_merge_all(countries,no_gt)

def init_stage2(countries,no_gt,url=None,show=False):
    from limic.download import download_graph, common
    countries, url = common(countries,url,show)
    download_graph("nx",countries=countries,url=url)
    convert_merge_all(countries,no_gt)

def init_stage3(countries,no_gt,url=None,show=False):
    from limic.download import download_graph, common
    countries, url = common(countries,url,show)
    for suffix in "nx", "npz", "gt":
        download_graph(suffix,countries,url=url)
    if len(countries) >= 2:
        merge_all(countries)
