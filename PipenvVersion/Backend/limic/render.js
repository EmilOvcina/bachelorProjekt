{%% macro header(this, kwargs) %%}
<link rel="stylesheet" href="https://rawcdn.githack.com/marslan390/BeautifyMarker/master/leaflet-beautify-marker-icon.css"/>
<script src="https://rawcdn.githack.com/marslan390/BeautifyMarker/master/leaflet-beautify-marker-icon.js"></script>
{%% endmacro %%}
{%% macro script(this, kwargs) %%}
L.control.scale().addTo({{this._parent.get_name()}});
function rgb2hex(rgb) {
    return "#" + ((1 << 24) + (rgb[0] << 16) + (rgb[1] << 8) + rgb[2]).toString(16).slice(1);
}
const zip = (arr1, arr2) => arr1.map((k, i) => [k, arr2[i]]);
var source;
var target;
var paths = [];
var markers = [];
var sources = [];
var latlon2marker = {};
var timer = 0;
var delay = 200;
var prevent = false;
source_color = [63,255,63]
target_color = [63,63,255]
diff_color = target_color.map(function (x,i) {return x-source_color[i];})
var source_icon = new L.BeautifyIcon.icon({"backgroundColor": rgb2hex(source_color), "borderColor": rgb2hex(source_color.map(function (x) {return Math.trunc(x/2);})), "borderWidth": 3, "icon": "flash", "iconStyle": "opacity:0.8", "innerIconStyle": "", "isAlphaNumericIcon": false, "spin": false, "textColor": "#000"});
var target_icon = new L.BeautifyIcon.icon({"backgroundColor": rgb2hex(target_color), "borderColor": rgb2hex(target_color.map(function (x) {return Math.trunc(x/2);})), "borderWidth": 3, "icon": "flash", "iconStyle": "opacity:0.8", "innerIconStyle": "", "isAlphaNumericIcon": false, "spin": false, "textColor": "#000"});                            
function latLngListener(e) {
    $.getJSON( "http://%(host)s:%(port)d%(prefix)s/tower",{'lat':e.latlng.lat,'lng':e.latlng.lng})
    .done(function(data) {
        if (e.originalEvent.detail > 1) {
            return;
        }
        var marker;
        var latlon = [data.tower[1],data.tower[2]];
        if (latlon in latlon2marker) {
            marker = latlon2marker[latlon];
        } else {
            marker = L.marker([data.tower[1],data.tower[2]],{title: `id: ${data.tower[0]}, lat: ${data.tower[1]}, lon: ${data.tower[2]}`});
            latlon2marker[latlon] = marker;
        }
        marker.addTo({{this._parent.get_name()}});
        sources.push(marker);
        target = marker;
        target.setIcon(target_icon);
        if (sources.length >= 2) {
            source = sources[sources.length-2];
            source.setIcon(source_icon);
            $.getJSON( "http://%(host)s:%(port)d%(prefix)s/route",{'source[lat]':source.getLatLng().lat,'source[lng]':source.getLatLng().lng,
            'target[lat]':target.getLatLng().lat,'target[lng]':target.getLatLng().lng})
            .done(function (data) {
                var latlon = data.path[1].map(function (x) {return [x[4],x[5]];});
                {{this._parent.get_name()}}.fitBounds(L.polyline(latlon,{}).getBounds());
                var cost = data.path[1].map(function (x) {return x[0];});
                var dist = data.path[1].map(function (x) {return x[1];});
                var air = data.path[1].map(function (x) {return x[2];});
                var id = data.path[1].map(function (x) {return x[3];});
                var i;
                paths.push([]);
                markers.push([]);
                var old = source.getPopup();
                source.bindPopup((old != undefined ? old.getContent() : "")+`<h3>Route ${markers.length}</h3><p>id: ${id[0]}, cost: ${cost[0]}, dist: ${dist[0]}, air: ${air[0]}, latlon: ${latlon[0]}</p>`);
                var old = target.getPopup();
                target.bindPopup((old != undefined ? old.getContent() : "")+`<h3>Route ${markers.length}</h3><p>id: ${id[latlon.length-1]}, cost: ${cost[latlon.length-1]}, dist: ${dist[latlon.length-1]}, air: ${air[latlon.length-1]}, latlon: ${latlon[latlon.length-1]}`);
                if (air[1]) {
                    source.setIcon(new L.BeautifyIcon.icon({"backgroundColor": rgb2hex(source_color), "borderColor": "#7f1f1f", "borderWidth": 3, "icon": "plane", "iconStyle": "opacity: 0.8;", "innerIconStyle": "", "isAlphaNumericIcon": false, "spin": false, "textColor": "#000"}));
                    source.update();
                } else {
                    source.setIcon(source_icon);
                }
                if (air[air.length-1]) {
                    target.setIcon(new L.BeautifyIcon.icon({"backgroundColor": rgb2hex(target_color), "borderColor": "#7f1f1f", "borderWidth": 3, "icon": "plane", "iconStyle": "opacity: 0.8;", "innerIconStyle": "", "isAlphaNumericIcon": false, "spin": false, "textColor": "#000"}));
                } else {
                    target.setIcon(target_icon);
                }
                for (i = 0; i+1 < latlon.length; i++) {
                    bgcolor = source_color.map(function (x,j) {return Math.trunc(x+parseFloat(i)*diff_color[j]/latlon.length);});
                    bordercolor = rgb2hex(bgcolor.map(function (x) {return Math.trunc(x/2);}));
                    bgcolor = rgb2hex(bgcolor);
                    if (i > 0) {
                        if (latlon[i] in latlon2marker) {
                            marker = latlon2marker[latlon[i]];
                        } else {
                            marker = L.marker(latlon[i],{title:`id: ${id[i]}, lat: ${latlon[i][0]}, lon: ${latlon[i][1]}`});
                            latlon2marker[latlon[i]] = marker;
                        }
                        marker.addTo({{this._parent.get_name()}});
                        old = marker.getPopup();
                        marker.bindPopup((old != undefined ? old.getContent() : "")+`<h3>Route ${markers.length}</h3><p>id: ${id[i]}, cost: ${cost[i]}, dist: ${dist[i]}, air: ${air[i]}, latlon: ${latlon[i]}`);
                        markers[markers.length-1].push(marker);
                        if (air[i]||air[i+1]) {
                            marker.setIcon(new L.BeautifyIcon.icon({"backgroundColor": bgcolor, "borderColor": "#ff1f1f", "borderWidth": 3, "icon": "plane", "iconStyle": "opacity: 0.8;", "innerIconStyle": "", "isAlphaNumericIcon": false, "spin": false, "textColor": "#000"}));
                        } else if (id[i] < 0) {
                            marker.setIcon(new L.BeautifyIcon.icon({"backgroundColor": bgcolor, "borderColor": "#ff1f1f", "borderWidth": 3, "icon": "times", "iconStyle": "opacity: 0.8;", "innerIconStyle": "", "isAlphaNumericIcon": false, "spin": false, "textColor": "#000"}));
                        } else {
                            marker.setIcon(new L.BeautifyIcon.icon({"backgroundColor": bgcolor, "borderColor": bordercolor, "borderWidth": 3, "icon": "none", "iconStyle": "opacity: 0.1;", "innerIconStyle": "", "isAlphaNumericIcon": false, "spin": false, "textColor": "#000"}));
                        }
                    }
                    if (data.path[0] != undefined) {
                        paths[paths.length-1].push(L.polyline([latlon[i],latlon[i+1]],{color:(air[i+1]?'#ff3f3f' :bgcolor),opacity:0.5,weight:6}).addTo({{this._parent.get_name()}}));
                    }
                }
            })
            .fail(function () {
                alert('error');
            });
        }
    })
    .fail(function(jqxhr,textStatus,error) {
        alert(error);
    });
}
{{this._parent.get_name()}}.on('dblclick', function() {
    prevent = true;
    clearTimeout(timer);
})
.on('click', function(e) {
    time = setTimeout(function() {
        if (!prevent) {
            latLngListener(e);
        }
        prevent = false;
    }, delay);  
})
.on('contextmenu', function(e) {
    if (sources.length) {
        {{this._parent.get_name()}}.removeLayer(sources.pop());
    }
    if (sources.length) {
        for (path of paths.pop()) {
            {{this._parent.get_name()}}.removeLayer(path);
        }
        for (mark of markers.pop()) {
            {{this._parent.get_name()}}.removeLayer(mark);
        }
        coords = []
        for (marks of markers) {
            for (mark of marks) {
                coords.push(mark.getLatLng());
            }
        }
        {{this._parent.get_name()}}.fitBounds(L.polyline(coords,{}).getBounds());
    }
});

{%% endmacro %%}