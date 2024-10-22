var map;
var host = "http://localhost:5000";

var ControlPanelCanBeRemoved = false;
var faultOverlayCanBeRemoved = false;

var nozonerender = 1;
var towerrender = 1;
var dronerender = 1;
var routerender = 1;

var zoomThreshold = 9;
var animationSpeed = 150;

var myLayer;
var graphLayer;
var nozoneLayer;
var planRouteLayer;
var selectTowerLayer;
var faultsLayer;

var selectedTowers = [];

var drone_dict = {};
var activated_drones = [];

var routeLayer;

var lastVRP = {};

var map;
var googleHybrid;

var slider;

var active_folder = 0;
var idle_folder = 0;
var finished_folder = 0;

var selectStyle = {
    radius: 8,
    fillColor: "#00ff00",
    color: "#000",
    weight: .51,
    opacity: .5,
    fillOpacity: 0.8,
    pane: "selectedTowers"
};

var droneStyle = {
    radius: 7,
    fillColor: "#ff8000",
    color: "#000",
    weight: .51,
    opacity: 1,
    fillOpacity: 0.8,
    pane: "drones"
};

var towerStyle = {
    radius: 6,
    fillColor: "#0a00ff",
    color: "#000",
    weight: .51,
    opacity: .5,
    fillOpacity: 0.8
};

var no_zoneStyle = {
    color: "#ff0000",
    opacity: .5,
    fillOpacity: 0.8,
    pane: "nozonePane"
};

var faultStyle = {
    radius: 10,
    fillColor: "#ff0000",
    color: "#000",
    weight: .60,
    opacity: .5,
    fillOpacity: 0.8,
    pane: "faults"
};

var mapSettings = {
    maxZoom: 18,
    minZoom: 3,
    subdomains:['mt0','mt1','mt2','mt3'],
    attribution: '&copy; <a href="https://google.com">Google Maps</a> contributors',
    detectRetina: true,
    reuseTiles: true,
    unloadInvisibleTiles: true
};

/**
 * Runs when the html has loaded. Initialises the objects and datastructures used for the application.
 * Also loads and draws some of the elements on the map.
 */
$(document).ready(function() {
    map = new L.Map('map', {
        center: [55.94612, 10.48645],
        zoom: 8,
        renderer: L.canvas()
    });
    
    map.createPane("drones");
    map.getPane("drones").style.zIndex = 1000;
    
    map.createPane("faults");
    map.getPane("faults").style.zIndex = 950;

    map.createPane("nozonePane");
    map.getPane("nozonePane").style.zIndex = 999;
    
    map.createPane("routes");
    map.getPane("routes").style.zIndex = 900;
    
    map.createPane("selectedTowers");
    map.getPane("selectedTowers").style.zIndex = 920;

    googleHybrid = L.tileLayer('http://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}', mapSettings);

    googleStreets = L.tileLayer('http://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', mapSettings).addTo(map);

    myLayer = new L.GeoJSON().addTo(map);

    //Used to fix bug, where some browsers register a click twice, only seems to happen here.
    TowerCanBeSelected = true;
    // Loads in all the towers
    $.getJSON(host + "/graph", function(data) {
        graphLayer = L.geoJson(data, {
                pointToLayer: function (feature, latlng) {
                    return L.circleMarker(latlng, towerStyle);
            }
        }).on("click", function(e) {
        if(TowerCanBeSelected) {
            TowerCanBeSelected = false;
            var lat = e.layer._latlng.lat;
            var lng = e.layer._latlng.lng;

            $.getJSON(host+"/tower",{'lat':lat,'lng':lng})
                .done(function(data) {
                    selectedTowers.push([data.tower[0], data.tower[2], data.tower[1]]);
                    drawSelectedTowers(data.tower, false);
                    
                    if($("#showplanPopup").is(":visible")) {
                        animateOutFromTop($("#showplanPopup"));
                        clearSelection();
                    }
                    $("#calculateRoutePopup > p").html("Towers: " + selectedTowers.length);
                    if(!$("#calculateRoutePopup").is(":visible") && selectedTowers.length >= 1)  {
                        animateInFromTop($("#calculateRoutePopup"));
                    }
                    if($("#addplanPopup").is(":visible")) { 
                        clearRoute();
                    }
            })
        }
        setTimeout(function() {
            TowerCanBeSelected = true;
        }, 50);
        });
    }).done(d => {
        $("#map").css("margin-top", "0");
    });
    
    //Loads in the no-zones
    $.getJSON(host+"/no_zone", function(data) {
        nozoneLayer = L.geoJson(data, {
                style: no_zoneStyle
            }
        ).addTo(myLayer);
    });
    
    selectTowerLayer = new L.GeoJSON().addTo(myLayer); 
    droneLayer = new L.LayerGroup().addTo(myLayer);
    routeLayer = new L.LayerGroup().addTo(myLayer);
    planRouteLayer = new L.LayerGroup().addTo(myLayer);
    faultsLayer = new L.GeoJSON();
    
    // Loads the drones into an internal data structure.
    $.getJSON(host+"/drones", function(json) {
        json["DroneList"].forEach(function(droneEntry) {
            var drone = droneEntry["Drone"];
            drone_dict[drone["id"]] = {
                id: drone["id"],
                isWorking: drone["isWorking"],
                batteryPercentage: drone["batteryPercentage"],
                marker: new L.circleMarker([drone["coords"]["y"], drone["coords"]["x"]], droneStyle),
                coords: {
                    x: drone["coords"]["x"],
                    y: drone["coords"]["y"]
                }
            };
            drone_dict[drone["id"]].marker.addTo(droneLayer);
            drone_dict[drone["id"]].marker.on('click', droneClickFunction);
            drone_dict[drone["id"]].marker.data = drone_dict[drone["id"]];

            activated_drones.push(drone["id"])
        });
    }).done(function() {
        RefreshDronesOnInterval(3 * 1000);
    });

    /*
    * Refreshes the drone every "delay" milliseconds, using the Lodash library (seen as the underscore '_' in the code) to perform comparison of objects.
    * The marker attribute is omitted from this comparison since it does not exist on the back-end since it's added client-side and the comparison will therefore otherwise fail.
    * If the drone contains new data it is overwritten with the new data and its position, and the marker is also moved accordingly to move its position on the map.
    */
    async function RefreshDronesOnInterval(delay) { 
        setInterval(function() {
            $.getJSON(host+"/drones", function(json) {
                json["DroneList"].forEach(function(droneEntry) {
                    var drone = droneEntry["Drone"];
                    if (!_.isEqual(drone, _.omit(drone_dict[drone.id], 'marker'))) {
                        var oldmarker = drone_dict[drone["id"]].marker
                        drone_dict[drone["id"]] = {
                            id: drone["id"],
                            isWorking: drone["isWorking"],
                            batteryPercentage: drone["batteryPercentage"],
                            marker: oldmarker,
                            coords: {
                                x: drone["coords"]["x"],
                                y: drone["coords"]["y"],
                            }
                        };
                        var newLatLng = new L.LatLng(drone["coords"]["y"], drone["coords"]["x"]);
                        drone_dict[drone["id"]].marker.setLatLng(newLatLng);
                    }
                })
            })
        }, delay); // delay in milliseconds
    }

    loadPlanList();

    //Loads in the faults from the list of faulty towers.
    var fault_dict = [];
    $.getJSON( host + "/faults", function(json) {
        json["FaultList"].forEach(function(faultEntry) {
            var fault = faultEntry["Fault"];
            fault_dict[fault["id"]] = {
                id: fault["id"],
                marker: new L.circleMarker([fault["tower"]["lat"], fault["tower"]["lng"]], faultStyle),
                images: fault["images"]
            };
            fault_dict[fault["id"]].marker.addTo(faultsLayer);
            fault_dict[fault["id"]].marker.on('click', faultClickFunction);
            fault_dict[fault["id"]].marker.data = fault_dict[fault["id"]];
        });
    }).done(function() {
        // A method can be called here which would refresh all the faults on an interval and therefore load new faults as they are discovered, similarly to the drone refresh function.
        // The delay between loading new faults should likely not be small since it is assumed that it is very unlikely to find new faults and the requests are therefore unnecessary.
        //RefreshFaultsOnInterval(1800 * 1000); //amount of time in milliseconds
    });

    /*
    * The trick is that when you click a drone it will execute the drone layer function which shows the drone info panel, however the map click function
    * will also execute and immediately remove the panel (because its meant to remove the panel when you click away from the drone, but clicking ON the drone also executes this,
    * unfortunately. The solution is to have a canBeRemoved boolean set to false when the popup is displayed and changing it back to true after some delay (here 200ms) which means
    * it will change back AFTER the map function has executed, thus preventing it from removing it in the first place)
    */       
    map.on("click", function (e) { 
        if (ControlPanelCanBeRemoved) {
            stopVideoFeed();
        } 
        clearSidePanel();
    });

    //set view of Denmark initially upon launch
    map.attributionControl.setPrefix('');
    var denmark = new L.LatLng(55.94612, 10.48645); 
    map.setView(denmark, 8);
    
    //ensure that we zoom in far enough to render the towers, such that we don't get overwhelmed with tower markers that we dont care about
    map.on('zoomend' , function (e) {
        var geo = map.getCenter();
        if (map.getZoom() > zoomThreshold && towerrender) {
            $("#sidepanel ul li p").fadeOut(0);
            myLayer.addLayer(graphLayer);
            myLayer.addLayer(faultsLayer);
        }else {
            if(towerrender == 1) {
                $("#sidepanel ul li p").fadeIn(0);
            }
            myLayer.removeLayer(graphLayer);
            myLayer.removeLayer(faultsLayer);
        }
    });

    // Defines what happens when a selected tower is clicked on.
    selectTowerLayer.on("click", function(e) {
        var lat = e.layer._latlng.lat;
        var lng = e.layer._latlng.lng;
        $.getJSON( host+"/tower",{'lat':lat,'lng':lng})
            .done(function(data) {
            selectedTowers = selectedTowers.filter(function( obj ) { return obj[0] !== data.tower[0]; });
            selectTowerLayer.removeLayer(e.layer);

            if($("#calculateRoutePopup").is(":visible") && selectedTowers.length < 1)  {
                animateOutFromTop($("#calculateRoutePopup"));
            } 
            if($("#addplanPopup").is(":visible")) {
                clearRoute();
            }
            if($("#showplanPopup").is(":visible")) {
                clearSelection();
            }
            if(selectedTowers.length >= 1) {
                $("#calculateRoutePopup > p").html("Towers: " + selectedTowers.length);
            } else {
                animateOutFromTop($("#calculateRoutePopup"));
                $("#addplanPopup input").val("");
                clearSelection();
            }
        })
    });
})

//Loads the user interface with the image slider which loads the images associated with the specific fault from a URL once a fault is clicked on, on the map.
function faultClickFunction(e) { 
    clearSidePanel();
    clearSelection();
    faultOverlayCanBeRemoved = false;
    
    if(!$("#faultinfo_panel").is(":visible")) {   
        
        animateIn($("#faultinfo_panel"));
        $("#faultinfo_panel_wrapper").css("max-height",$("body").height() - 20 - $("#faultinfo_panel .popup_header").height());
    }
    if (slider != null) {
        slider.destroy()
    }
    $(".splide__list").html("")
    var imgarray = e.target.data.images
    imgarray.forEach(image => {
        $(".splide__list").append("<li class='splide__slide'><img class='splideimg' src='" + image + "' width='100%' height='100%'></li>")
    })
    slider = new Splide( '.splide', { "cover":0.5, "heightRatio":0.5} ).mount();
    
    
    //preventing the map.click function from removing the panel immediately again
    setTimeout(function() {
        faultOverlayCanBeRemoved = true;
    }, 200);
}

//Loads the user interface with the 'drone live-feed' and information regarding the drone.
function droneClickFunction(e) { 
    clearSidePanel();
    feature = e.target;
    ControlPanelCanBeRemoved = false;
    var coordx = feature.data.coords.x;
    var coordy = feature.data.coords.y;
    document.getElementById("droneinfoid").textContent = "Drone " + feature.data.id;
    document.getElementById("droneinfobattery").textContent = "Battery Level: " + feature.data.batteryPercentage + "%";
    document.getElementById("droneinfoworking").textContent = "Drone is Working Already: " + Boolean(feature.data.isWorking);
    document.getElementById("droneinfocoordinates").textContent = "Drone Coordinates: " + coordx + " , " + coordy;
    
    if(!$("#droneinfo_panel").is(":visible")) {   
        animateIn($("#droneinfo_panel"));
        $("#droneinfo_panel_wrapper").css("max-height",$("body").height() - 20 - $("#droneinfo_panel .popup_header").height());
    }
    
    startVideoFeed();
    setTimeout(function() {
        ControlPanelCanBeRemoved = true;
    }, 300);
}  

//Starts the m3u8 video. The 'type' parameter may have to been edited too if using other media formats.
function startVideoFeed() {
    videojs(document.getElementById("livefeedvideo")).src({
        type: 'application/x-mpegURL',
        src: 'https://bitdash-a.akamaihd.net/content/MI201109210084_1/m3u8s/f08e80da-bf1d-4e3d-8899-f0f6155f6efa.m3u8'
    });
    
    document.getElementById("livefeedvideo_html5_api").setAttribute("controls", ""); //enables controls so the user can view the video in fullscreen
    videojs(document.getElementById("livefeedvideo")).play();
}

/* 
* Stops the video-feed (well, it is paused in reality). 
* Important to call this when hiding the video since it would otherwise continue to be streamed and consume bandwidth depending on implementation.
*/
function stopVideoFeed() {
    videojs(document.getElementById("livefeedvideo")).pause();
}

//Clears the selected towers and removes the route on the map.
function clearSelection() { 
    if(selectedTowers.length > 0) {
        selectedTowers = [];
        myLayer.removeLayer(selectTowerLayer);
        selectTowerLayer = new L.GeoJSON().addTo(myLayer); 
        myLayer.removeLayer(routeLayer);
        routeLayer = new L.GeoJSON().addTo(myLayer); 
        animateOutFromTop($("#calculateRoutePopup"));
        if($("#addplanPopup").is(":visible")) {
            animateOutFromTop($("#addplanPopup"));
        }
        $("#addplanPopup input").val("");
        
        selectTowerLayer.on("click", function(e) {
            var lat = e.layer._latlng.lat;
            var lng = e.layer._latlng.lng;
            $.getJSON(host+"/tower",{'lat':lat,'lng':lng})
                .done(function(data) {
                selectedTowers = selectedTowers.filter(function( obj ) { return obj[0] !== data.tower[0]; });
                selectTowerLayer.removeLayer(e.layer);

                if($("#calculateRoutePopup").is(":visible") && selectedTowers.length < 1)  {
                    animateOutFromTop($("#calculateRoutePopup"));
                    clearSelection();
                }
                if($("#addplanPopup").is(":visible")) {
                    clearRoute();
                }
                if($("#showplanPopup").is(":visible")) {
                    clearSelection();
                }
                if(selectedTowers.length >= 1) {
                    $("#calculateRoutePopup > p").html("Towers: " + selectedTowers.length);
                } else {
                    clearSelection();
                    $("#addplanPopup input").val("");
                    animateOutFromTop($("#calculateRoutePopup"));
                }
            })
        });
    }
}

/**
 * Used to calculate routes from all the enabled drones to all the selected towers
 */
function route() {
    var drns = [];  
    var routePromises = [];
    myLayer.removeLayer(routeLayer);
    routeLayer = new L.GeoJSON().addTo(myLayer);
    const coordinates_array = graphLayer.getLayers().map(l => l.getLatLng());

    var length = (Object.keys(drone_dict).length);

    //Finds the tower closest to each drone
    for(var i = 0; i < length; i++) {
        let id = drone_dict[i].id;
        if(activated_drones.includes(id)) {
            var nearest = L.GeometryUtil.closest(map, coordinates_array, new L.LatLng(drone_dict[i].coords.y, drone_dict[i].coords.x));
            var request = $.getJSON(host+"/tower",{'lat':nearest.lat,'lng':nearest.lng})
                .done(function(data) {
                    drns.push([id+"", data.tower[0], data.tower[2], data.tower[1]]);
                    selectedTowers = uniq(selectedTowers);
            });
            routePromises.push(request);
        }
    }

    // Called after all the towers has been fetched from LiMiC. This calculated the route.
    $.when.apply(null, routePromises).done(data => {
        if(drns.length > 0) {
            $.getJSON( host+"/vrp",{'drones':drns,'towers':selectedTowers})
                .done(function(data) {
                    drone_amnt = 0;
                    for(drone in data) {
                        if(data[drone].distance > 0) {
                            drone_amnt += 1;
                            drawRoute(data[drone]);
                        }
                    }
                    $("#addplanPopup > #drone_amnt").html("Drones: " + drone_amnt);
                    $("#addplanPopup > #tower_amnt").html("Towers: " + selectedTowers.length);
                    animateOutFromTop($("#calculateRoutePopup"));
                    animateInFromTop($("#addplanPopup"));
                    lastVRP = data;
            });
        }
    });
} 

/**
 * Routes from one drone to a list of towers. This is used when displaying a plan, where a drone might have moved since start of plan.
 */
function routeDroneToTowers(droneID, towers)
{
    var drns = [];  
    var routePromises = [];
    myLayer.removeLayer(routeLayer);
    routeLayer = new L.GeoJSON().addTo(myLayer);
    const coordinates_array = graphLayer.getLayers().map(l => l.getLatLng());
    
    var nearest = L.GeometryUtil.closest(map, coordinates_array, new L.LatLng(drone_dict[droneID].coords.y, drone_dict[droneID].coords.x));
    var request = $.getJSON(host+"/tower",{'lat':nearest.lat,'lng':nearest.lng})
        .done(function(data) {
            drns.push([droneID+"", data.tower[0], data.tower[2], data.tower[1]]);
    });
    routePromises.push(request);

    $.when.apply(null, routePromises).done(data => {
        $.getJSON( host+"/vrp",{'drones':drns,'towers':towers})
            .done(function(data) {
                drawRoute(data[droneID]);     
        });
    });
}

/**
 * Draws the actual line corresponding to a route.
 */
function drawRoute(drone) {
    return new L.polyline(drone.path, {color: '#0ba5a5', opacity: 1, weight: 8, pane: "routes"}).addTo(routeLayer);   
}

/**
 * Draws the green circle indicating that a tower has been selected. 
 */
function drawSelectedTowers(tower, changeOrder) {
    if(changeOrder) 
        return new L.circleMarker([tower[2], tower[1]], selectStyle).addTo(selectTowerLayer);
    return new L.circleMarker([tower[1], tower[2]], selectStyle).addTo(selectTowerLayer);
}

/**
 * Loads all the plans from the JSON file, and divides them into the three categories
 */
function loadPlanList() {
    $("#active_plans_folder .plans_folder_dropdown > ul").html("");
    $("#idle_plans_folder .plans_folder_dropdown > ul").html("");
    $("#finished_plans_folder .plans_folder_dropdown > ul").html("");
    $.getJSON(host+"/plans").done(data => {
        data["PlanList"].forEach(e => {
            if(e["done"]) { //adds done plans to the correct tab
                $("#finished_plans_folder .plans_folder_dropdown > ul").append("<li onclick='show_plan(" + e["id"] + ")'>" + e["name"] + "</li>")
            } else if(!e["done"] && !e["active"]) { //adds inactive plans to the correct tab
                $("#idle_plans_folder .plans_folder_dropdown > ul").append("<li onclick='show_plan(" + e["id"] + ")'>" + e["name"] + "</li>")
            } else { //adds active plans to the correct tab
                $("#active_plans_folder .plans_folder_dropdown > ul").append("<li onclick='show_plan(" + e["id"] + ")'>" + e["name"] + "</li>")
            }                
        });
        clearSelection();
    });
}

/**
 * Changes a plan by sending a request to LiMiC, this activates a plan
 */
function activate_plan(id) {
    clearSelection();
    animateOutFromTop($("#showplanPopup"));
    $.ajax({
        method: "POST",
        url: host+"/activate_plan",
        data: {"id" : id}
    }).done(e => {
        loadPlanList();
    });
}

/**
 * Deletes a plan by sending a request to LiMiC.
 */
function remove_plan(id) {
    clearSelection();
    animateOutFromTop($("#showplanPopup"));
    $.ajax({
        method: "POST",
        url: host+"/delete_plan",
        data: {"id" : id}
    }).done(e => {
        loadPlanList();
    });
}

/**
 * Opens the pop-up displaying all the information about the plan. Also draws the plan on the map.
 */
function show_plan(id) {
    clearSelection();
    $.getJSON(host+"/get_plan", {"id" : id}).done(data => {
        droneplanshtml = "";
        droneCount = 0;
        droneCountIdle = 0;

        selectedTowers = [];
        data["plan"].forEach(droneplan => {
            routeDroneToTowers(droneplan["drone"], droneplan["towers"])
            droneplan["towers"].forEach(tw => {
                selectedTowers.push(tw)
            })
            var workingStr = drone_dict[droneplan["drone"]]["isWorking"] == 0 ? "Idle" : "Working"; 
            if(workingStr == "Idle") {droneCountIdle += 1;}
            droneCount += 1;
            droneplanshtml += "<li onclick='animateToDrone("+droneplan["drone"]+")'> <p>Drone " + droneplan["drone"]+ ": "+ workingStr +"</p><p>Battery: " + drone_dict[droneplan["drone"]]["batteryPercentage"] + "%</p> </li>";
        });

        selectedTowers.forEach(tower => {
            drawSelectedTowers(tower, true)
        })

        $("#showplanPopup h5").html(data["name"]);
        $("#showplanPopup #planpopup_towers").html("<p>Towers: " + selectedTowers.length + "</p>");
        $("#showplanPopup #planpopup_drones").html("<p>Drones: "+droneCountIdle+"/"+droneCount+"</p>");
        $("#showplanPopup ul").html(droneplanshtml);

        if(data["active"] || data["done"] || droneCountIdle != droneCount) {
            $("#showplanPopup #activate_btn").fadeOut(0);
            $("#showplanPopup #edit_btn").fadeOut(0);
            $("#showplanPopup #remove_btn").css("margin", "0 0 0.5rem 0.5rem");
        } else {
            $("#showplanPopup #edit_btn").fadeIn(0);
            $("#showplanPopup #activate_btn").fadeIn(0);
            $("#showplanPopup #remove_btn").css("margin", "");
            $("#showplanPopup #activate_btn").attr("onclick", "activate_plan("+ id +")");   
            $("#showplanPopup #edit_btn").attr("onclick", "edit_plan(\""+ data["name"] +"\", "+ selectedTowers.length +")");   
        }
        $("#showplanPopup #remove_btn").attr("onclick", "remove_plan("+ id +")");
        animateInFromTop($("#showplanPopup"));
    })
}

/**
 *  Edits a single plan. Returns the user to selection-mode with all the plan's towers selected.
 */
function edit_plan(name, towers) {
    clearRoute();
    animateOutFromTop($("#showplanPopup"));
    $("#addplanPopup input").val(name);
    if($("#plans").is(":visible")) { animateOut($("#plans")); }
    $("#calculateRoutePopup > p").html("Towers: " + towers);
}

function loadDronePanel()
{
    striOn="M5 3a5 5 0 0 0 0 10h6a5 5 0 0 0 0-10H5zm6 9a4 4 0 1 1 0-8 4 4 0 0 1 0 8z";
    striOff="M11 4a4 4 0 0 1 0 8H8a4.992 4.992 0 0 0 2-4 4.992 4.992 0 0 0-2-4h3zm-6 8a4 4 0 1 1 0-8 4 4 0 0 1 0 8zM0 8a5 5 0 0 0 5 5h6a5 5 0 0 0 0-10H5a5 5 0 0 0-5 5z";
    var html = "";
    for(var i = 0; i < Object.keys(drone_dict).length; i++) {
        svg_path = activated_drones.includes(drone_dict[i]["id"]) ? striOn : striOff;
        html += "<li><div class='d-flex bd-highlight'> <div class='p-2 flex-grow-1 bd-highlight'><p onclick='animateToDrone("+ drone_dict[i]['id'] +")'>Drone " + drone_dict[i]['id']+ "</p><small>Battery:" + drone_dict[i]["batteryPercentage"]+"%</small></div>"
        + "<div style='padding: 0 1.3rem' class='align-self-center'><svg onclick='toggleDrone(" + drone_dict[i]["id"] + ")' xmlns='http://www.w3.org/2000/svg' width='2.5rem' height='2.5rem' fill='#bbe1fa' class='bi bi-toggle-on' viewBox='0 0 16 16'>"
        +"<path d='" + svg_path + "'/></svg></div></div></li>";
    }
    $("#drone_panel_wrapper ul").html(html)
}

function toggleDrone(droneID)
{
    for(var i = 0 ; i < activated_drones.length; i++) {
        if (activated_drones[i] == droneID) { //The drones is activated
            activated_drones = activated_drones.filter(d => d != droneID)
            loadDronePanel();
            drone_dict[droneID].marker.setStyle({fillOpacity: 0.3, opacity: 0.3})
            return;
        }
    }
    activated_drones.push(droneID);
    drone_dict[droneID].marker.setStyle(droneStyle)
    loadDronePanel();
}

/**
 * Removes duplicates in an array list
 */
function uniq(a) {
    var uniID = [];
    var unArr = [];
    
    for(var i = 0; i < a.length; i++) {
        if(!uniID.includes(a[i][0])) {
            uniID.push(a[i][0]);
            unArr.push(a[i]);
        }
    }
    return unArr;
}

/* 
* Workaround for 1px lines appearing in some browsers due to fractional transforms
* and resulting anti-aliasing.
* https://github.com/Leaflet/Leaflet/issues/3575
*/
(function(){
    var originalInitTile = L.GridLayer.prototype._initTile
    L.GridLayer.include({
        _initTile: function (tile) {
            originalInitTile.call(this, tile);
            var tileSize = this.getTileSize();
            tile.style.width = tileSize.x + 1 + 'px';
            tile.style.height = tileSize.y + 1 + 'px';
        }
    });
})()     

/**
 * Uses JQuery to animate in an object from the left to the right.
 */
function animateIn(object) 
{
    object.fadeIn(0);
    object.animate({
        left: "0"
    }, animationSpeed);
}

/**
 * Uses JQuery to animate out an object from the right to the left.
 */
function animateOut(object) 
{
    object.animate({
        left: "-410px"
    }, animationSpeed, () => {
        object.fadeOut(0);
    });
}

/**
 * Uses JQuery to animate in an object from the top.
 */
function animateInFromTop(object) 
{
    object.fadeIn(0);
    object.animate({
        top: "0"
    }, animationSpeed);
}

/**
 * Uses JQuery to animate out an object, in an upwards motion.
 */
function animateOutFromTop(object) 
{
    object.fadeIn(0);
    object.animate({
        top: -(object.height())
    }, animationSpeed, () => {
        object.fadeOut(0);
    });
}

/**
 * Pans the center of the map to a drone.
 */
function animateToDrone(droneID) {

    map.panTo(new L.LatLng(drone_dict[droneID]['coords']['y'], drone_dict[droneID]['coords']['x']), {animate: true, duration: (animationSpeed/1000)});
}

/**
 * Removes the drawn route, but keeps the selected towers.
 */
function clearRoute()
{
    myLayer.removeLayer(routeLayer);
    routeLayer = new L.GeoJSON().addTo(myLayer); 
    animateOutFromTop($("#addplanPopup"));
    animateInFromTop($("#calculateRoutePopup"));  
}

/**
 * Used to remove the displaying plan.
 */
function clearSelectionPlan() {
    if($("#showplanPopup").is(":visible")) {
        animateOutFromTop($("#showplanPopup"));
        clearSelection();
    }
}

/**
 * Opens the dropdown to reveal plans under each category in the plans menu.
 */
function openPlansFolder(folder) {
    $("#plans_wrapper").css("max-height", ($("body").height() - 24 - $("#plans .popup_header").height() ));
    if(!active_folder && folder == "active") {
        animateInFromTop($("#active_plans_folder .plans_folder_dropdown"));
        $("#active_plans_folder svg path").attr("d", "M8 15a.5.5 0 0 0 .5-.5V2.707l3.146 3.147a.5.5 0 0 0 .708-.708l-4-4a.5.5 0 0 0-.708 0l-4 4a.5.5 0 1 0 .708.708L7.5 2.707V14.5a.5.5 0 0 0 .5.5z");
        active_folder = 1;
    } else if(active_folder && folder == "active") {
        animateOutFromTop($("#active_plans_folder .plans_folder_dropdown"));
        $("#active_plans_folder svg path").attr("d", "M8 1a.5.5 0 0 1 .5.5v11.793l3.146-3.147a.5.5 0 0 1 .708.708l-4 4a.5.5 0 0 1-.708 0l-4-4a.5.5 0 0 1 .708-.708L7.5 13.293V1.5A.5.5 0 0 1 8 1z");
        active_folder = 0;
    }
    if(!idle_folder && folder == "idle") {
        animateInFromTop($("#idle_plans_folder .plans_folder_dropdown"));
        $("#idle_plans_folder svg path").attr("d", "M8 15a.5.5 0 0 0 .5-.5V2.707l3.146 3.147a.5.5 0 0 0 .708-.708l-4-4a.5.5 0 0 0-.708 0l-4 4a.5.5 0 1 0 .708.708L7.5 2.707V14.5a.5.5 0 0 0 .5.5z");
        idle_folder = 1;
    } else if(idle_folder && folder == "idle") {
        animateOutFromTop($("#idle_plans_folder .plans_folder_dropdown"));
        $("#idle_plans_folder svg path").attr("d", "M8 1a.5.5 0 0 1 .5.5v11.793l3.146-3.147a.5.5 0 0 1 .708.708l-4 4a.5.5 0 0 1-.708 0l-4-4a.5.5 0 0 1 .708-.708L7.5 13.293V1.5A.5.5 0 0 1 8 1z");
        idle_folder = 0;
    }
    if(!finished_folder && folder == "finished") {
        animateInFromTop($("#finished_plans_folder .plans_folder_dropdown"));
        $("#finished_plans_folder svg path").attr("d", "M8 15a.5.5 0 0 0 .5-.5V2.707l3.146 3.147a.5.5 0 0 0 .708-.708l-4-4a.5.5 0 0 0-.708 0l-4 4a.5.5 0 1 0 .708.708L7.5 2.707V14.5a.5.5 0 0 0 .5.5z");
        finished_folder = 1;
    } else if(finished_folder && folder == "finished") {
        animateOutFromTop($("#finished_plans_folder .plans_folder_dropdown"));
        $("#finished_plans_folder svg path").attr("d", "M8 1a.5.5 0 0 1 .5.5v11.793l3.146-3.147a.5.5 0 0 1 .708.708l-4 4a.5.5 0 0 1-.708 0l-4-4a.5.5 0 0 1 .708-.708L7.5 13.293V1.5A.5.5 0 0 1 8 1z");
        finished_folder = 0;
    }
}

/**
 * Removes all menus from the left side of the screen.
 */
function clearSidePanel()
{
    let a = ControlPanelCanBeRemoved;
    let b = faultOverlayCanBeRemoved;
    if($("#layerVis").is(":visible")) { animateOut($("#layerVis")); }
    if($("#plans").is(":visible")) { animateOut($("#plans")); }
    if($("#showplanPopup").is(":visible")) { animateOutFromTop($("#showplanPopup")); clearSelection();}
    if($("#drone_panel").is(":visible")) {animateOut($("#drone_panel")); }
    if (ControlPanelCanBeRemoved) {
        if($("#droneinfo_panel").is(":visible")) {animateOut($("#droneinfo_panel")); }
    }
    if (faultOverlayCanBeRemoved) {
        if($("#faultinfo_panel").is(":visible")) {animateOut($("#faultinfo_panel")); }
    }
    $("#layerVisIcon").css("fill", "");
    $(".bi-gear").css("animation-play-state", "paused");
    $(".bi-gear").css("animation-iteration-count", "0");

    $("#droneicon .dr_g1").css("animation-play-state", "paused");
    $("#droneicon .dr_g1").css("animation-iteration-count", "0");
    $("#droneicon .dr_g2").css("animation-play-state", "paused");
    $("#droneicon .dr_g2").css("animation-iteration-count", "0");
    $("#droneicon .st0").css("stroke", "");
    $("#droneicon .st1").css("stroke", "");
    $("#droneicon .st2").css("stroke", "");
    $("#droneicon .st3").css("stroke", "");
    $("#droneicon").css("fill", "");

    $(".bi-card-checklist").css("fill", "");
    $(".bi-card-checklist path:nth-child(1n + 2)").css("animation-play-state", "paused");
    $(".bi-card-checklist path:nth-child(1n + 2)").css("animation-iteration-count", "0");
}

/**
 * Clears both the side panels and the displaying plan.
 */
function clearSidePanelPlans() {
    clearSelectionPlan();
    clearSidePanel();
}

/**
 * Loads when all the html has loaded. Used for defining animations.
 */
$(document).ready(function() {
    $("#addplanPopup").css("top", "-"+$("#addplanPopup").height())
    $("#calculateRoutePopup").css("top", "-"+$("#calculateRoutePopup").height())
    $("#showplanPopup").css("top", "-"+$("#showplanPopup").height())

    // droneicon animation
    $("#droneicon").click(()=> {
        clearSidePanel();
        if(!$("#drone_panel").is(":visible")) {   
            loadDronePanel();
            $("#droneicon .st0").css("stroke", "#3282b8");
            $("#droneicon .st1").css("stroke", "#3282b8");
            $("#droneicon .st2").css("stroke", "#3282b8");
            $("#droneicon .st3").css("stroke", "#3282b8");
            $("#droneicon").css("fill", "#3282b8");
            animateIn($("#drone_panel"));
            $("#droneicon .dr_g1").css("animation-play-state", "running");
            $("#droneicon .dr_g1").css("animation-iteration-count", "");
            $("#droneicon .dr_g2").css("animation-play-state", "running");
            $("#droneicon .dr_g2").css("animation-iteration-count", "");
            $("#drone_panel_wrapper").css("max-height",$("body").height() - 20 - $("#drone_panel .popup_header").height());
        }
    });

    //Cog animation
    $("#layerVisIcon").click(()=> {
        clearSidePanel();
        if(!$("#layerVis").is(":visible")) {
            $("#layerVisIcon").css("fill", "#3282b8");
            animateIn($("#layerVis"));
            $(".bi-gear").css("animation-play-state", "running");
            $(".bi-gear").css("animation-iteration-count", "");
        }
    });

    //Plans animation
    $(".bi-card-checklist").click(()=> {
        clearSidePanel();
        if(!$("#plans").is(":visible")) {
            $(".bi-card-checklist").css("fill", "#3282b8");
            animateIn($("#plans"));
            $(".bi-card-checklist path:nth-child(1n + 2)").css("animation-play-state", "running");
            $(".bi-card-checklist path:nth-child(1n + 2)").css("animation-iteration-count", "");
        }
        clearSelectionPlan();
    });

    //On and off buttons off the setting menu.
    striOn="M5 3a5 5 0 0 0 0 10h6a5 5 0 0 0 0-10H5zm6 9a4 4 0 1 1 0-8 4 4 0 0 1 0 8z";
    striOff="M11 4a4 4 0 0 1 0 8H8a4.992 4.992 0 0 0 2-4 4.992 4.992 0 0 0-2-4h3zm-6 8a4 4 0 1 1 0-8 4 4 0 0 1 0 8zM0 8a5 5 0 0 0 5 5h6a5 5 0 0 0 0-10H5a5 5 0 0 0-5 5z";
    $('#layerVisTower').click(function() {
        if(towerrender == 1) {
            myLayer.removeLayer(graphLayer);
            myLayer.removeLayer(selectTowerLayer);
            myLayer.removeLayer(faultsLayer);
            $("#sidepanel ul li p").fadeOut(0);
            towerrender = 0;
            $(this).find("path").attr("d", striOff);
        } else {
            if(map.getZoom() > zoomThreshold) {
                myLayer.addLayer(graphLayer);
                myLayer.addLayer(selectTowerLayer);
                myLayer.addLayer(faultsLayer);
            }
            towerrender = 1;
            $(this).find("path").attr("d", striOn);
        }
    });
    
    // Creates the toggles for each button in the settings menu.
    $('#layerVisRoute').click(function() {
        if(routerender == 1) {
            myLayer.removeLayer(routeLayer);
            routerender= 0;
            $(this).find("path").attr("d", striOff);
        } else {
            myLayer.addLayer(routeLayer);
            routerender = 1;
            $(this).find("path").attr("d", striOn);
        }
    });
        
    $('#layerVisDrone').click(function() {
        if(dronerender == 1) {
            myLayer.removeLayer(droneLayer);
            dronerender= 0;
            $(this).find("path").attr("d", striOff);
        } else {
            myLayer.addLayer(droneLayer);
            dronerender = 1;
            $(this).find("path").attr("d", striOn);
        }
    });
        
    $('#layerVisNoFly').click(function() {
        if(nozonerender == 1) {
            $(this).find("path").attr("d", striOff);
            myLayer.removeLayer(nozoneLayer);
            nozonerender = 0;
        } else {
            myLayer.addLayer(nozoneLayer);
            nozonerender = 1;
            $(this).find("path").attr("d", striOn);
        }
    });

    // Add plan button
    $("#addplanPopup button").click(function() {
        if ($('#addplanPopup input').val().length > 0) {
            $.ajax({
                type: "POST",
                url: host+"/add_plan",
                data: {"vrp": JSON.stringify(lastVRP), "name" : $('#addplanPopup input').val(), 'towers': JSON.stringify(selectedTowers) }
            }).done(function(data) {
                $('#addplanPopup input').val("");
                loadPlanList()
            })
        } else {
            alert("You must enter a name for the plan");
        }
    }); 

    /** Change to satellite view */
    var satView = 0;
    $("#satellite").click(() => {
        if(!satView) {
            googleHybrid.addTo(map);
            satView = 1;
            $("#satellite").css("fill", "#3282b8")
            $("#satellite").children().css("stroke", "#3282b8")
            $("#satellite").css("animation-play-state", "running")
            $("#satellite").css("animation-iteration-count", "")
        } else {
            map.removeLayer(googleHybrid);
            satView = 0;
            $("#satellite").css("fill", "")
            $("#satellite").children().css("stroke", "")
            $("#satellite").css("animation-iteration-count", "0")
        }
    })
})
