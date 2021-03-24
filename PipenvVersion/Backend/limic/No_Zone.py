import kml2geojson
import pygeoj
import geojson
import re
import requests
from bs4 import BeautifulSoup
import urllib.request
import json
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

class polygon:
    def __init__(self, name):
        self.name=name
        self.polygon_list=[]

    def add_polygon(self, item):
        self.polygon_list.append(item)


def convertkml_Geojson():
 #driver = webdriver.Chrome('C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe')
 #driver.get("https://www.droneluftrum.dk")
 #button = driver.find_element_by_id('buttonID')
 #button.click()
 #driver.get("https://www.droneluftrum.dk")
 #button = driver.find_element_by_id('109')
 #button.click()
 #sess.get("https://www.droneluftrum.dk")    #replace URL with the page that blocks for content warning. This will establish cookies for this session on the website.
 #desiredPage = sess.get("http://example.com/desiredPage")    #This URL will very much depend on how the website allows access to pages with content warnings. See description below for this usecase.
 #desiredHTML = BeautifulSoup(desiredPage.text, 'html.parser')
 #req=urllib.request.Request("https://www.droneluftrum.dk")
 #response=urllib.request.urlopen(req)
 #html=response.read()
 #json_obj=json.loads(html)
 #token_string=json_obj["token"].encode("ascii","ignore")
 #testfile = urllib.request.URLopener()
 #Url="https://www.droneluftrum.dk/api/uaszones/exportKmlUasZones?Authorization=Bearer%20eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsidXNlck1hbmFnZW1lbnRTZXJ2aWNlIl0sInNjb3BlIjpbInJlYWQiXSwiZXhwIjoxNTg1ODA0NzQ3LCJhdXRob3JpdGllcyI6WyJuYXZpYWlyX2Ryb25ld2ViIl0sImp0aSI6IjFkNTVkNGUzLWJiMmEtNDA5MC04MjI1LWYyOTg0NmZkODgwNyIsImNsaWVudF9pZCI6Ik5hdmlhaXJEcm9uZVdlYiIsInVzaWQiOiI1YjNjOWE0Yi0wNzBhLTRkNmQtYTJiYi0yOWJmNGFkMjlkMjUifQ.QWF8RDBzTXq_E-aUb9dB35SHo-5flZFmsioL1IShQFw"
 #Url="https://www.droneluftrum.dk/api/uaszones/exportKmlUasZones?"
 #headers = {"Authorization": "Bearer [ACCESS TOKEN]"}
 #r = requests.get(Url, headers=headers)
 #print(r.text)
 #testfile.retrieve(Url, "export.kml")

 #convert kml file to geoson
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
       item=polygon(name)
       for i in range(0,len(polygon_)):
          item.add_polygon(polygon_[i])
       list_polygons.append(item)
    else:
        lengh=len(features['geometry']['geometries']) 
        for k in range(0,lengh):
            polygon_=features['geometry']['geometries'][k]['coordinates']
            item=polygon(name)
            for p in range(0,len(polygon_)):
                item.add_polygon(polygon_[p])
            list_polygons.append(item)
 for q in range(0, len(list_polygons)):
     d=list_polygons[q].polygon_list  ## d should be used for Prune function in LIMIC
     pylon=d[0]
 i=4
 return list_polygons; 

if __name__ == "__main__":
       mylist=convertkml_Geojson()
       for i in range(0,len(mylist)):
           data=mylist[i]
       #i=5
   
