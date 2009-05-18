map = null;

function map_locations(locations, wms_url){
    
    if (map) {
        map.destroy();
    }  

    // this is the projection where lon, lat work
    var epsg4326 = new OpenLayers.Projection("EPSG:4326");
    
    // this is google's projection
    var googleprojection = new OpenLayers.Projection("EPSG:900913");
  
    // bounds for google's projection
    // units are in meters
    var bounds = new OpenLayers.Bounds(
                                       -2.003750834E7,-2.003750834E7,
                                       2.003750834E7,2.003750834E7);

    
    var options = { 
        //      units: "dd",  // only works in EPSG:4326
        maxExtent: bounds,
        maxResolution: 156543.03396025, // meters per pixel at maximum extent (world projection)
        projection: "EPSG:900913",  // use google's projection
    };
    
    // create a map opject with the options 
    map = new OpenLayers.Map('map', options);

    // layer for the tiles
    var wms = new OpenLayers.Layer.WMS(
                                       "WMS Layer",
                                       wms_url,
                                       {layers: 'openstreetmap',
                                        format: 'image/png',} // use PNGs because they're cached
                                       );

    // layer for the marker point of interest
    var datalayer = new OpenLayers.Layer.Vector(
                                                "Data Layer",
                                                {});

    // add the layers to the map
    map.addLayers([wms, datalayer]);

    // add the point of interest to the data layer
      
    for (i in locations) {

        var point = new OpenLayers.Geometry.Point(locations[i]['longitude'], locations[i]['latitude']);
        var marker = new OpenLayers.Feature.Vector(point.transform(epsg4326, googleprojection));
        datalayer.addFeatures([marker]);
    }

    // zoom in on the point of interest
    map.zoomToExtent(datalayer.getDataExtent());
}
