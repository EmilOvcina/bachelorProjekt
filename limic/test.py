OVERPASS = (("-u","--overpass-url"),{'type':str,'dest':'overpass_url','help':"define url for Overpass API to be URL",'metavar':'URL'})
NOGT = (("-g","--no-graph-tool"),{'action':'store_true','dest':'no_gt','default':False,'help':"do not perform graph_tool tests"})
CONFIG = [OVERPASS,NOGT]
COUNTRIES=["Faroe Islands","Guernsey","Isle of Man"]
OSM_COUNTRIES=["andorra","azores"]
IDSS=[(5164034601,5163680824),(920411192,920412407),(2197735231,2197735192)]
POLYGON=[54.4,10.4,54.5,10.4,54.5,10.5,54.4,10.5]
PACKAGES="requests,numpy,dogpile.cache,networkx,graph_tool,dbm.gnu,shapely,folium,flask,scipy,pyproj,setproctitle"

def install(package):
    from subprocess import call
    from sys import executable
    return call([executable, "-m", "pip", "-q", "install", package])
    
def install_packages(no_gt):
    from limic.util import start,end,status
    from importlib.util import find_spec
    packages = PACKAGES.split(",")
    for package in packages:
        if no_gt and package == "graph_tool":
            continue
        start("Checking for module",package)
        if find_spec(package):
            status("OK")
        else:
            status("MISSING")
            if package == "graph_tool":
                no_gt = True
            if package in ("graph_tool","dbm.gnu"):
                status("WARNING: "+package+"is needed for some optional functionality - if needed, it has to be installed manually")
                continue
            start("Trying to install",package,"using PIP")
            if install(package) == 0:
                end()
            else:
                status("FAILED")
                raise Exception("could not install",package,"using PIP - manual install?")
    return no_gt

def test(overpass_url,no_gt):
    no_gt = install_packages(no_gt)
    import limic.util as util
    import limic.init as init
    import limic.route as route
    import limic.convert as convert
    import limic.merge as merge
    import limic.prune as prune
    import limic.select as select
    import limic.length as length
    util.set_option('overwrite',True)
    countries = COUNTRIES
    osm_countries = OSM_COUNTRIES
    idss = IDSS
    init.init_stage0(overpass_url,countries,no_gt)
    init.init_stage1_cache(overpass_url,countries,no_gt)
    init.init_stage1_osm(osm_countries,no_gt)
    init.init_stage2(countries,no_gt)
    init.init_stage3(countries,no_gt)
    merge.merge_cache(list(map(lambda x:"cache."+x,countries)),"cache.merged")
    polygon = POLYGON
    for country, ids in zip(countries,idss):
        for suffix in ("nx","gt","npz"):
            if no_gt and suffix == "gt":
                continue
            graph_name = "graph."+country+"."+suffix
            for suffix2 in ("nx","gt","npz"):
                if suffix == suffix2 or (no_gt and suffix2 == "gt"):
                    continue
                graph_name2 = "graph."+country+"."+suffix2
                vars(convert)['convert_'+suffix+"_"+suffix2](file_name_in=graph_name,file_name_out=graph_name2)
            vars(route)['route_'+suffix](file_name=graph_name,source_id=ids[0],target_id=ids[1])
            vars(prune)['prune_'+suffix](file_name_in=graph_name,file_name_out="pruned."+country+"."+suffix,polygon=polygon,overpass_url=overpass_url)
            vars(select)['select_'+suffix](file_name_in=graph_name,file_name_out="selected."+country+"."+suffix,polygon=polygon,overpass_url=overpass_url)
            if not no_gt:
                vars(length)['length_'+suffix](file_name=graph_name)
        route.route_direct(file_name="cache."+country,source_id=ids[0],target_id=ids[1])
