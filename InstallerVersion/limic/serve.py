COUNTRIES = (("countries",),{'type':str,'nargs':'+','help':"countries to route on",'metavar':'COUNTRY'})
GRAPH = (("graph_file",),{'type':str,'help':"use graph file GRAPH",'metavar':'GRAPH'})
HTML = (("html_file",),{'type':str,'help':"use rendered HTML file",'metavar':'HTML'})
RHOST = (("--render-host",),{'type':str,'dest':'r_host','default':'127.0.0.1','help':"render hostname (default: 127.0.0.1)",'metavar':'HOST'})
RPORT = (("--render-port",),{'type':int,'dest':'r_port','default':5000, 'help':"render port number (default: 5000)",'metavar':'PORT'})
RPREFIX = (("--render-prefix",),{'type':str,'dest':'r_prefix','default':'','help':"render URI prefix (default: '')",'metavar':'PREFIX'})
HOST = (("--host",),{'type':str,'dest':'host','default':'0.0.0.0','help':"hostname (default: 0.0.0.0)",'metavar':'HOST'})
PORT = (("--port",),{'type':int,'dest':'port','default':5000, 'help':"port number (default: 5000)",'metavar':'PORT'})
PREFIX = (("--prefix",),{'type':str,'dest':'prefix','default':'','help':"URI prefix (default: '')",'metavar':'PREFIX'})
OSM = (("--osm",),{'action':'store_true','dest':'osm','default':False,'help':"process from OSM file (SLOW)"})
NOBROWSER = (("-n","--no-browser"),{'action':'store_true','dest':'no_browser','default':False,'help':"do not open html in browser (headless)"})
URL = (("-d","--download-url"),{'type':str,'dest':'url','help':"define url for download directory to be URL",'metavar':'URL'})
SHOW = (("-l","--list"),{'action':'store_true','dest':'show','default':False,'help':"list available countries (default: False)"})
CONSERVEMEM = (("-c","--conserve-memory"),{'action':'store_true','dest':'conserve_mem','default':False,'help':"lower memory usage but higher runtime"})

CONFIG = [
    ("auto",{'help':"start HTTP server for given COUNTRY (default: Europe)",'args':[SHOW,URL,CONSERVEMEM,NOBROWSER,HOST,PORT,PREFIX,RHOST,RPORT,RPREFIX,OSM,COUNTRIES]}),
    ("nx",{'help':"start HTTP server for given GRAPH and rendered HTML file",'args':[SHOW,URL,NOBROWSER,HOST,PORT,PREFIX,RHOST,RPORT,RPREFIX,GRAPH,HTML]}),
    ("npz",{'help':"start HTTP server for given GRAPH and rendered HTML file",'args':[SHOW,URL,NOBROWSER,HOST,PORT,PREFIX,RHOST,RPORT,RPREFIX,GRAPH,HTML]})
]

import kml2geojson
import pygeoj
import geojson
import shapely.wkt
import requests
import json
overpass_url="http://caracal.imada.sdu.dk/overpass"

class polygon:
    def __init__(self, name):
        self.name=name
        self.polygon_list=[]

    def add_polygon(self, item):
        self.polygon_list.append(item)

class pylon_item:
    def __init__(self,LAT,LAN):
        self.LAT=LAT
        self.LAN=LAN

def serve_auto(countries,host="localhost",port=5000,prefix="",osm=False,url=None,show=False,no_browser=False,r_host="localhost",r_port=5000,r_prefix="",conserve_mem=False):
    from limic.download import common, download_graph, download_merged, download_osm
    from limic.init import extract_osm_all, merge_all
    from limic.render import render_nx
    graph_file = None
    if osm:
        countries, url = common(countries=countries,url=url,show=show,osm=osm,join=False)
        download_osm(countries=countries,url=url)
        extract_osm_all(countries=countries,conserve_mem=conserve_mem)
    else:
        countries, url = common(countries=countries,url=url,show=show,osm=osm,join=True)
        download_graph(suffix="npz",countries=countries,url=url,show=show,join=True)
    if len(countries) > 1 :
        merge_all(countries)
    if len(countries) == 1:
        graph_file = "graph."+countries[0]+(".nx" if osm else ".npz")
    html_file = graph_file[:-2]+"html"
    if osm:
        serve_nx(graph_file,html_file,host=host,port=port,prefix=prefix,url=url,show=show,no_browser=no_browser,r_host=r_host,r_port=r_port,r_prefix=r_prefix)
    else:
        serve_npz(graph_file,html_file,host=host,port=port,prefix=prefix,url=url,show=show,no_browser=no_browser,r_host=r_host,r_port=r_port,r_prefix=r_prefix)
        
    
def serve_nx(graph_file,html_file,host="localhost",port=5000,prefix="",url=None,show=False,no_browser=False,r_host="localhost",r_port=5000,r_prefix=""):
    from limic.render import render_nx
    from limic.route import astar_nx
    g,nodes = render_nx(graph_file,html_file,host=r_host,port=r_port,prefix=r_prefix)
    serve(g,nodes,astar_nx,html_file,host,port,prefix,url,show,no_browser,r_host,r_port,r_prefix)

def serve_npz(graph_file,html_file,host="localhost",port=5000,prefix="",url=None,show=False,no_browser=False,r_host="localhost",r_port=5000,r_prefix=""):
    from limic.render import render_npz
    from limic.route import astar_npz
    g,nodes = render_npz(graph_file,html_file,host=r_host,port=r_port,prefix=r_prefix)
    serve(g,nodes,astar_npz,html_file,host,port,prefix,url,show,no_browser,r_host,r_port,r_prefix)

def serve(g,nodes,astar,html_file,host="localhost",port=5000,prefix="",url=None,show=False,no_browser=False,r_host="localhost",r_port=5000,r_prefix=""):
    from flask import Flask, jsonify, request
    from limic.util import load_pickled, start, end, status
    from threading import Thread
    from time import sleep
    from webbrowser import open as wopen
    from scipy.spatial import cKDTree as KDTree
    from pyproj import CRS, Transformer
    from flask_cors import CORS
    start("Initializing KD-Tree")
    crs_4326 = CRS("EPSG:4326")
    crs_proj = CRS("EPSG:28992")
    transformer = Transformer.from_crs(crs_4326, crs_proj)
    tree = KDTree(list(map(lambda x:transformer.transform(x[1],x[2]),nodes)))
    end()

    start("Setting up the app")
    app = Flask("LiMiC")
    CORS(app)

    @app.route(prefix+"/")
    def hello():
        return open(html_file).read()

    
    
    @app.route(prefix+"/graph")
    def graph():
        file = open("../leaflet/data/export1.geojson","r")
        return file.read()


    def droneluftum_download(access_token=None):

        if access_token is None:
            access_token = droneluftum_auth()

        url = "https://www.droneluftrum.dk/api/uaszones/exportKmlUasZones?Authorization=Bearer" + access_token
        response = requests.request("GET", url)
            # TODO: exception of request breaks
        return response.text.encode('utf8')

    def droneluftum_auth():
        url = "https://www.droneluftrum.dk/oauth/token?grant_type=client_credentials"
        headers = {
                # Authorization value captured from browser. Utf-8 string:
                # "NaviairDroneWeb:NaviairDroneWeb" encoded to base64
                'Authorization': 'Basic TmF2aWFpckRyb25lV2ViOk5hdmlhaXJEcm9uZVdlYg=='
        }
        response = requests.request("POST", url, headers=headers)
            # access_token expires in ~12h
            # TODO: exceptions if request breaks
        return response.json()['access_token']
    def prune_ids_nx(g,delete_ids):
        to_delete = []
        delete_ids = set(delete_ids)
        for n in g.nodes():
            if n[0] in delete_ids:
                to_delete.append(n)
        for n in to_delete:
            g.remove_node(n)
        return g
    def prune_graph(towerList):
        # fill kdtree
        polygon_pairs = list(map(float,towerList))
        #print(polygon_pairs)
        polygon_pairs = list(zip(polygon_pairs[::2], polygon_pairs[1::2]))
        from limic.overpass import nodes_in_geometry, set_server
        start("Query server for nodes in polygon")
        set_server(overpass_url)
        nodes = nodes_in_geometry(polygon_pairs)
        end('')
        status(len(nodes))
        start("Pruning graph")
        pruned_graph = prune_ids_nx(g,nodes)
        end()
        return pruned_graph

    @app.route(prefix+"/prune")
    def prune():


        #counting number of pruning
        count=0
    # get body of request and make sure it is via post
        kml = droneluftum_download()
        # make a copy of original nx graph as current nx graph
        g_original=g.copy()
        #parse KML file
        with open('export.kml', 'wb') as f:
            f.write(kml)
        from pykml import parser
        with open('export.kml') as fobj:
           KLM_file = parser.parse(fobj).getroot().Document
        for pm in KLM_file.iterchildren():
              
              if hasattr(pm, 'Polygon'):
                coordinates = pm.Polygon.outerBoundaryIs.LinearRing.coordinates.pyval
                #coordinates=coordinates.replace('0.0 ','')
                coordinates=coordinates.split(',')
                 #for j in range(len(coordinates)-2, 0, -1):
                towerList = []
                lenght=len(coordinates)
                #if (lenght>=173):
                    #lenght=173
                    #print("Changed"+pm.name)
                print(lenght)
                print(pm.name)
                for p in range(0,len(coordinates)-1,2):
                        coordinates[p+1]=coordinates[p+1].strip()   
                        if p!=0:
                         coordinates[p]=coordinates[p].split()  
                         towerList.append(float(coordinates[p+1]))
                         towerList.append(float(coordinates[p][1])) 
                        else:
                            towerList.append(float(coordinates[p+1]))
                            towerList.append(float(coordinates[p]))

                count=count+1
                print("pruning"+str(count))
                      # fill kdtree
                polygon_pairs = list(map(float,towerList))
                #print(polygon_pairs)
                polygon_pairs = list(zip(polygon_pairs[::2], polygon_pairs[1::2]))
                from limic.util import kdtree, nodes_in_geometry
                start("Building kd-tree from nodes")
                tree = kdtree(g.nodes(),get_latlon=lambda x:(x[1],x[2]))
                end()
                start("Querying tree for nodes in polygon")
                nodes = nodes_in_geometry(tree,polygon_pairs)
                end('')
                status(len(nodes))
                start("Pruning graph")
                for n in nodes:
                    g.remove_node(n)
                #h = g
                end()





                #start("Query server for nodes in polygon")
                #set_server(overpass_url)
                #nodes = nodes_in_geometry(polygon_pairs)
                #end('')
                #status(len(nodes))
                #start("Pruning graph")
                #to_delete = []
                #delete_ids = set(nodes)
                #for n in g.nodes():
                #    if n[0] in delete_ids:
                 #       to_delete.append(n)
                #for n in to_delete:
                #    g.remove_node(n)
                #pruned_graph = prune_ids_nx(g,nodes)
                #print("Done")
                #end()
                #break

              #pruned_graph=prune_graph(towerList)
              
              #break
       
              

        #servve GeoJson graph
        from geojson import Feature, Point, LineString, FeatureCollection, dumps
        fs = []
        for n in g.nodes():
            f = Feature(geometry=Point((n[1],n[2])))
            fs.append(f)
        for nf,nt in g.edges():
            f = Feature(geometry=LineString([(nf[1],nf[2]),(nt[1],nt[2])]))
            fs.append(f)
        fc = FeatureCollection(fs)
        return dumps(fc)
      
        

    @app.route(prefix+"/tower")
    def tower():
        lat = float(request.args.get('lat'))
        lng = float(request.args.get('lng'))
        start("Finding tower",lat,lng)
        tower = nodes[tree.query(transformer.transform(lat,lng))[1]]
        end('')
        res = jsonify(tower=tower)
        end()
        return res

    @app.route(prefix+"/route")
    def route():
        source_lat = float(request.args.get('source[lat]'))
        source_lng = float(request.args.get('source[lng]'))
        target_lat = float(request.args.get('target[lat]'))
        target_lng = float(request.args.get('target[lng]'))
        start("Routing",source_lat,source_lng,target_lat,target_lng)
        source_index = tree.query(transformer.transform(source_lat,source_lng))[1]
        source = nodes[source_index]
        end('')
        target_index = tree.query(transformer.transform(target_lat,target_lng))[1]
        target = nodes[target_index]
        end('')
        path = astar(g,(source,source_index),(target,target_index))
        end('')
        if path[1][-1][0] == float('inf'):
            path[1][-1] = (path[1][-1][1],)+path[1][-1][1:]
        res = jsonify(path=path)
        end()
        return res
    end()

    # TODO (3) Rewrite data transfer with web interface (use POST & body)
    @app.route(prefix+"/vrp")
    def tsp():
        from limic.route import vehicle_routing_problem, Location

        allDrones = []
        i = 0
        newDrone = list(request.args.getlist('drones[' + str(i) + '][]'))
        while(newDrone != []):
            i+=1
            allDrones.append(newDrone)
            newDrone = list(request.args.getlist('drones[' + str(i) + '][]'))
        drones = list(map(lambda x: Location(x[0], (x[2], x[3]), order='lonlat'), allDrones))

        allTowers = []
        i = 0
        newTower = list(request.args.getlist('towers[' + str(i) + '][]'))
        while(newTower != []):
            i+=1
            allTowers.append(newTower)
            newTower = list(request.args.getlist('towers[' + str(i) + '][]'))
        towers = list(map(lambda x: Location(x[0], (x[1], x[2]), order='lonlat'), allTowers))

        paths = vehicle_routing_problem(g, astar, tree, drones, towers)
        res = jsonify(paths)
        return res

    # TODO (2) Evaluate if /selectAll is worth rewriting
    # TODO (2) Reimplement and remove BP2 from repository
    @app.route(prefix+"/selectAll")
    def selectAll():
        import sys
        sys.path.append("..")
        from BP2_TSP.astar import selectAllTowersOnPath, pylon  #sys path append added to use tsp solver from parent directory

        first = list(request.args.getlist('first[]'))
        second = list(request.args.getlist('second[]'))

        path = selectAllTowersOnPath(first, second)
        res = jsonify(path=path)
        return res

    @app.route(prefix+"/no_zone")
    def no_zone():
        file = open("../leaflet/data/no_zone.geojson","r")
        return file.read()


# ADDED JONAS EMIL
    @app.route(prefix+"/drones")
    def drones():
        file = open("../leaflet/data/drones.json","r")
        return file.read()

    @app.route(prefix+"/get_drone", methods=['GET'])
    def get_drone():
        uid = int(request.args.get('id'))

        filePlans = open("../leaflet/data/drones.json", "r")
        string = ""
        for lines in filePlans.readlines():
            string += lines
        allDrones = json.loads(string)
        filePlans.close()

        if len(allDrones["DroneList"]) > 0:
            for uuid in allDrones["DroneList"]:
                if int(uuid["id"]) == uid:
                    return json.dumps(uuid)
        return "404"

    @app.route(prefix+"/faults")
    def faults():
        file = open("../leaflet/data/faults.json","r")
        return file.read()

    @app.route(prefix+"/plans")
    def planlist():
        file = open("../leaflet/data/plans.json","r")
        return file.read()

    @app.route(prefix+"/add_plan", methods=['GET', 'POST'])
    def add_plan():
        vrp = json.loads(request.form.get('vrp'))
        name = request.form.get('name')
        selectedTowers = json.loads(request.form.get('towers'))
        
        filePlans = open("../leaflet/data/plans.json", "r")
        string = ""
        for lines in filePlans.readlines():
            string += lines
        allPlans = json.loads(string)
        filePlans.close()

        highestID = -1
        if len(allPlans["PlanList"]) > 0:
            for uid in allPlans["PlanList"]:
                if uid["id"] > highestID:
                    highestID = uid["id"]
                if uid["name"] == name and uid['active'] == False and uid['done'] == False:
                    allPlans["PlanList"] = list(filter(lambda x: x['id'] != uid['id'], allPlans["PlanList"]))

        plan = {"id": highestID + 1, "name": name, "active": False, "done": False, "plan" : []}
        for drone, data in vrp.items():
            if data['distance'] > 0: #the path should be added to the plan
                towers = []
                for coords in data["path"]:
                    for tw in selectedTowers:
                        if coords[0] == tw[2] and coords[1] == tw[1] and [tw[0],tw[1], tw[2]] not in towers:
                            towers.append([tw[0], tw[1], tw[2]])
                tmp_drone = {
                    "drone": int(drone),
                    "towers" : towers
                }
                plan["plan"].append(tmp_drone)

        allPlans["PlanList"].append(plan)
        filePlans = open("../leaflet/data/plans.json", "w")
        filePlans.writelines(json.dumps(allPlans))
        filePlans.close()
        return json.dumps(allPlans)

    @app.route(prefix+"/get_plan", methods=['GET'])
    def get_plan():
        uid = int(request.args.get('id'))

        filePlans = open("../leaflet/data/plans.json", "r")
        string = ""
        for lines in filePlans.readlines():
            string += lines
        allPlans = json.loads(string)
        filePlans.close()

        if len(allPlans["PlanList"]) > 0:
            for uuid in allPlans["PlanList"]:
                if int(uuid["id"]) == uid:
                    return json.dumps(uuid)
        return "404"

    @app.route(prefix+"/delete_plan", methods=['POST'])
    def delete_plan():
        uid = int(request.form.get('id'))

        filePlans = open("../leaflet/data/plans.json", "r")
        string = ""
        for lines in filePlans.readlines():
            string += lines
        allPlans = json.loads(string)
        filePlans.close()

        allPlans["PlanList"] = list(filter(lambda x: x['id'] != uid, allPlans["PlanList"]))

        filePlans = open("../leaflet/data/plans.json", "w")
        filePlans.writelines(json.dumps(allPlans))
        filePlans.close()
        return "200"

    @app.route(prefix+"/activate_plan", methods=['POST'])
    def activate_plan():
        uid = int(request.form.get('id'))

        filePlans = open("../leaflet/data/plans.json", "r")
        string = ""
        for lines in filePlans.readlines():
            string += lines
        allPlans = json.loads(string)
        filePlans.close()        

        for plan in allPlans["PlanList"]:
            if plan["id"] == uid:
                plan["active"] = True

        filePlans = open("../leaflet/data/plans.json", "w")
        filePlans.writelines(json.dumps(allPlans))
        filePlans.close()

        return "200"

    @app.route(prefix+"/favicon")
    def favicon():
        from flask import send_file
        return send_file("../leaflet/data/favicon.ico")

    @app.route(prefix+"/javascript")
    def js():
        file = open("../leaflet/script.js","r")
        return file.read()

    @app.route(prefix+"/stylesheet")
    def css():
        file = open("../leaflet/style.css","r")
        return file.read()

#END OF ADDED JONAS EMIL    

    class OpenThread(Thread):
        def run(self):
            delay = 0.5
            sleep(delay)
            url = "http://%s:%d%s/" % (r_host,r_port,r_prefix)
            start("Open",url,"in browser")
            wopen(url,new=2)
            status("DONE")
    if not no_browser:
        OpenThread().start()
    app.run(host=host,port=port)
