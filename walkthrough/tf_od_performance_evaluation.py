"""
Name: Performance evaluation for building detection
Author: Jan Pisl
Description: This module compares detections produced by 
a model with buildings from OpenStreetMap and computes
the following statistics: precision, recall and f1 score.
It is optimized for evaluating multiple files with predictions
at the same time.

Required inputs:

- Path to directory with one or more GeoJSON files with predictions
- Path to GeoJSON with OpenStreetMap data
- Path to directory with image tiles on which buildings were detected
"""

import pprint
import os
import copy
import re
import math
import json
import time
import pdb
import logging
from copy import deepcopy

from absl import flags
from absl import app
from shapely import geometry
from shapely.geometry import Polygon
import ogr
import geopandas as gpd
import pandas as pd

flags.DEFINE_string('path_to_osm', None, 'Path to GeoJSON with OSM data')
flags.DEFINE_string('test_image_path', '', 'Path to test images')
flags.DEFINE_string('predictions_path', '', 
    'Path to GeoJSON with predictions')
flags.DEFINE_list("probability_threshold", "25,30,5", 
    'Evaluate for multiple probability thresholds; min, max, step')
flags.DEFINE_boolean('results_to_file', False, 
    'If yes, results are written to file')
flags.DEFINE_boolean('geometries_to_file', False, 
    'If yes, transformed predictions and OSM geometries\
    are written to GeoJSON with a column showing TP/FP/FN/')
flags.DEFINE_string('output_file_path', '', 
    'Path to file where results will be written')
flags.DEFINE_string('geometries_output_folder', '', 
    'Path to folder where geometries will be written')
flags.DEFINE_string('iou_threshold', "0.1", 
    'Minimum IoU for predictions and OSM \
    geometries to be considered correct')
flags.DEFINE_string('intersect_over_osm_area', "0.5", 
    'Minimum intersection of prediction over \
    area of OSM geometry to be considered correct')

FLAGS = flags.FLAGS


def write_geometries(predictions_gdf, osm_by_tile, path_to_file):
        predictions_out_path = os.path.join(FLAGS.geometries_output_folder,
                                            "transformed_" + path_to_file.split("/")[-1])
        predictions_gdf.to_file(predictions_out_path, driver="GeoJSON")
        
        
        original_osm_geoms = gpd.read_file(FLAGS.path_to_osm)
        osm_bboxes = gpd.GeoDataFrame(pd.concat([value['data'] for _, value in osm_by_tile.items()]))
        
        detected_osm_geoms = original_osm_geoms.within(osm_bboxes.loc[osm_bboxes.used])
        # this is a hack;needed because geometries on tile boundaries are counted in both tiles
        detected_osm_geoms = detected_osm_geoms[~detected_osm_geoms.index.duplicated(keep='first')]
        original_osm_geoms['used'] = detected_osm_geoms
        
        geometries_out_path = os.path.join(FLAGS.geometries_output_folder,
                                            "osm_geoms_" + path_to_file.split("/")[-1])
        original_osm_geoms.to_file(geometries_out_path, driver="GeoJSON")        
        logging.info(f"Writing predictions and geometries to {FLAGS.geometries_output_folder}")


def score_filter(predictions, min_score):
    """Remove prediction bounding boxes with probability under a threshold

    Parameters
    ----------
    predictions : dict
        all predictions
    min_score : int
        threshold score

    Returns
    -------
    dict
        filtered predictions
    """

    new_pred = {}
    new_pred['type'] = predictions['type']
    new_pred['features'] = []
    for feature in predictions['features']:
        if feature['properties']['score'] >= min_score:
            new_pred['features'].append(feature)
    
    return new_pred


def pixel_coords_zoom_to_lat_lon(PixelX, PixelY, zoom):
    """Convert pixel coordinates and zoom from Bing maps to lan, lot

    Parameters
    ----------
    PixelX : int
        horizontal distance from upper left corner in pixels
    PixelY : int
        vertical distance from upper left corner in pixels
    zoom : int
        zoom of the map (essentially size of a pixel)

    Returns
    -------
    tuple of floats
        latitude, longitude
    """
    MapSize = 256 * math.pow(2, zoom)
    x = (PixelX / MapSize) - 0.5
    y = 0.5 - (PixelY / MapSize)
    lon = 360 * x
    lat = 90 - 360 * math.atan(math.exp(-y * 2 * math.pi)) / math.pi

    return lon, lat


def feature_coords_to_lat_lon(feature):
    """Compute lat, lon from a feature with geometry

    Parameters
    ----------
    feature : geopandas Series
        single prediction, containing local coordinates, tile info

    Returns
    -------
    list of floats
        lat, lon
    """
    TileX, TileY, zoom = parse_tile_name(feature['properties']['task_id'])
    PixelX = TileX * 256
    PixelY = TileY * 256

    coords = feature['geometry']['coordinates'][0]
    translated = [[PixelX+x, PixelY+255-y] for x, y in coords]
    transformed = [[i for i in pixel_coords_zoom_to_lat_lon(x, y, zoom)] for x,y in translated]

    return transformed


def load_into_geodataframe(predictions):
    """Create a GeoDataFrame from a dictionary

    Parameters
    ----------
    predictions : dict
        predictions

    Returns
    -------
    GeoPandas DataFrame
        predictions processed
    """
    features = []
    for item in predictions['features']:
        feature = {'score' : item['properties']['score'],
                   'task_id': item['properties']['task_id'],
                   'prediction_id' : item['properties']['prediction_id'],
                   'type' : item['geometry']['type'],
                   'geometry_raw' : item['geometry']['coordinates'][0]}
        features.append(feature)
    predictions_df = gpd.GeoDataFrame.from_dict(features)
    predictions_df['geometry'] = predictions_df.apply(lambda row: Polygon(row['geometry_raw']), axis=1)
    predictions_df = predictions_df.drop(['geometry_raw'], axis=1)

    return predictions_df


def geometry_from_tile_coords(TileX, TileY, zoom):
    # Calculate lat, lon of upper left corner of tile
    PixelX = TileX * 256
    PixelY = TileY * 256 
    lon_left, lat_top = pixel_coords_zoom_to_lat_lon(PixelX, PixelY, zoom)

    # Calculate lat, lon of lower right corner of tile
    PixelX = (TileX + 1) * 256
    PixelY = (TileY + 1) * 256
    lon_right, lat_bottom = pixel_coords_zoom_to_lat_lon(PixelX, PixelY, zoom)
    
    poly = geometry.Polygon([[lon_left, lat_top], 
                             [lon_right, lat_top], 
                             [lon_right, lat_bottom], 
                             [lon_left, lat_bottom]])

    return poly


def get_tile_names(directory):
    """Get all tile names from the test folder

    Parameters
    ----------
    directory : string
        path to folder with image tiles

    Returns
    -------
    list
        all tile names used for evaluation
    """
    test_tiles = []
    for f in os.listdir(directory):
        if not re.match("[0-9]+.[0-9]+.[0-9]+.png", f):
            continue
        test_tiles.append(f.rsplit(".", 1)[0])
    
    return test_tiles


def create_test_area(test_tiles):
    """Create geometry from test images

    Parameters
    ----------
    test_tiles : list
        directory with test images

    Returns
    -------
    GeoPandas DataFrame
        all test images merged into a GeoDataFrame
    """

    multipolygon = ogr.Geometry(ogr.wkbMultiPolygon)
    for name in test_tiles:
        TileX, TileY, zoom = parse_tile_name(name)
        polygon = geometry_from_tile_coords(TileX, TileY, zoom)
        multipolygon.AddGeometry(polygon)
    multipolygon.FlattenTo2D()

    test_area = gpd.read_file(multipolygon.ExportToJson())
    test_area.to_file("predictions/area_extent.geojson")
    test_area = test_area.explode()
    return test_area


def intersect_using_spatial_index(source_gdf, source_index, tile):
    """Conduct spatial intersection using spatial index 
        for candidates GeoDataFrame to make queries faster.

    Parameters
    ----------
    source_gdf : GeoDataFrame
        [description]
    source_index : geopandas.sindex.SpatialIndex
        spatial index of the source
    tile : Shapely geometry
        geometry for which intersections with the sources are found

    Returns
    -------
    GeoDataFrame
        intersections between source_gdf and tile geometry
    """
    
    possible_matches_index = []

    bounds = tile.bounds
    c = list(source_index.intersection(bounds))
    possible_matches_index += c
    # Get unique candidates
    unique_candidate_matches = list(set(possible_matches_index))
    possible_matches = source_gdf.iloc[unique_candidate_matches]

    result = possible_matches.loc[possible_matches.intersects(tile)\
         ^ possible_matches.touches(tile)]
    return result


def get_osm_building_bboxes(data_path):
    """Filter out features that are not buildings and 
    find the bounding box for each building geometry in OSM.

    Parameters
    ----------
    data_path : string
        path to OSM data

    Returns
    -------
    GeoPandas DataFrame
        contains bounding box of all buildings in OSM dataset
    """
    osm_data = gpd.read_file(data_path)
    osm_data = osm_data.filter(['index', 'building', 'geometry'])
    osm_buildings = copy.deepcopy(osm_data.loc[(osm_data['building'] == 'yes') | (osm_data['building'] == 'residential')])
    osm_buildings2 = copy.deepcopy(osm_data.loc[osm_data.building.notna()])
    assert osm_buildings.shape == osm_buildings2.shape, "check building types in OSM"

    def create_bbox(row):
        xmin, ymin, xmax, ymax = row.bounds
        return Polygon.from_bounds(xmin, ymin, xmax, ymax)        
    
    osm_buildings.loc[:, 'geometry'] = osm_buildings['geometry'].apply(lambda row: create_bbox(row))

    return osm_buildings


def calculate_iou(poly_1, poly_2):
    return poly_1.intersection(poly_2).area / poly_1.union(poly_2).area


def calculate_intersect_over_osm_area(poly_1, poly_2):
    return poly_1.intersection(poly_2).area / poly_2.area


def is_correct(row, osm_by_tile, threshold):
    """Determine whether a given prediction is correct or not

    Parameters
    ----------
    row : GeoPandas Series
        prediction
    osm_by_tile : dict
        bboxes of buildings by tile and their spatial indices
    threshold : float
        minimum IoU for prediction to be considered correct

    Returns
    -------
    bool
        return True if prediction is correct; False if not
    """
    pred_geometry = row.geometry
    tile_name = row.task_id
    try:
        osm_intersections = intersect_using_spatial_index(
            osm_by_tile[tile_name]['data'], 
            osm_by_tile[tile_name]['index'],
            pred_geometry)
    except KeyError:
        #this means there was a prediction in a tile that has no OSM geometries -> false positive
        return False
    max_iou = 0
    for osm_item in osm_intersections.loc[osm_intersections['used']==False].itertuples():
        iou = calculate_iou(pred_geometry, osm_item.geometry)
        if iou > max_iou:
            max_iou = iou
            best_fit_index = osm_item[0]
    if max_iou >= threshold:
        osm_by_tile[tile_name]['data'].at[best_fit_index, "used"] = True
        return True
    
    # if no IoU over threshold, try if there is a building that overlapping with a pred
    # if there is and the overlapping area is over a threshold, consider it tp
    inters_over_area_thresh = float(FLAGS.intersect_over_osm_area)
    max_intersect_over_area = 0
    for osm_item in osm_intersections.loc[osm_intersections['used']==False].itertuples():     
        intersect_over_area = calculate_intersect_over_osm_area(pred_geometry, osm_item.geometry)
        if intersect_over_area > max_intersect_over_area:
            max_intersect_over_area = intersect_over_area
            best_fit_index_2 = osm_item[0]
    if max_intersect_over_area >= inters_over_area_thresh:
        osm_by_tile[tile_name]['data'].at[best_fit_index_2, "used"] = True
        return True

    return False


def perform_eval(path_to_file, osm_by_tile, osm_features_in_test_area, threshold):
    """Compute statistics for a given file with predictions

    Parameters
    ----------
    path_to_file : string
        file with predictions
    osm_by_tile : dict
        bboxes of buildings by tile and their spatial indices
    osm_features_in_test_area : int
        count of OSM buildings
    threshold : float
        minimum IoU for prediction to be considered correct

    Returns
    -------
    tuple of floats
        precision, recall, f1
    """
    with open(path_to_file) as f:
        predictions_raw = json.load(f)
    predictions_dict = score_filter(predictions_raw, min_score=threshold)
    for feature in predictions_dict['features']:
        feature['geometry']['coordinates'][0] = feature_coords_to_lat_lon(feature)

    predictions_gdf = load_into_geodataframe(predictions_dict)
    
    predictions_gdf['result'] = predictions_gdf.apply(lambda row: is_correct(row, osm_by_tile, float(FLAGS.iou_threshold)), axis=1)
    
    if FLAGS.geometries_to_file:
        write_geometries(predictions_gdf, osm_by_tile, path_to_file)

    tp = predictions_gdf.loc[predictions_gdf['result']].shape[0]
    total_pred = predictions_gdf['result'].shape[0]
    precision = tp/(total_pred)
    recall = tp/(osm_features_in_test_area)
    try:
        f1 = 2*((precision*recall)/(precision+recall))  
    except ZeroDivisionError:
        raise ValueError("Precision and recall are both zero. Check your input data")

    return precision, recall, f1, total_pred



def parse_tile_name(name):
    zoom, TileX, TileY = [int(x) for x in name.split(".")]
    return TileX, TileY, zoom

def process_osm_by_tile():
    """Divide given OSM data into subsets based 
        on which tile they belong to;
        Create spatial index for each subset;
        Count number of buildings

    Returns
    -------
    dict, int
        bboxes of buildings by tile and their spatial indices; count of them
        

    Raises
    ------
    Exception
        No OSM features found in the area
    """

    building_bboxes = get_osm_building_bboxes(FLAGS.path_to_osm)
    osm_index = building_bboxes.sindex
    
    osm_by_tile = {}
    feature_count = 0
    test_tiles = get_tile_names(FLAGS.test_image_path)
    for tile_name in test_tiles:
        TileX, TileY, zoom = parse_tile_name(tile_name)
        tile_geometry = geometry_from_tile_coords(TileX, TileY, zoom)
        tile_osm = intersect_using_spatial_index(building_bboxes, 
                                                 osm_index, tile_geometry)
        if tile_osm.shape[0] == 0:
            logging.debug("Tile {} contains no OSM data".format(tile_name))
            continue
        tile_osm['used'] = False
        feature_count += tile_osm.shape[0]
        tile_index = tile_osm.sindex
        osm_by_tile[tile_name] = {'data' : tile_osm, 'index' : tile_index}


    if feature_count == 0:
        raise Exception("No OSM geometries found for test area")

    return osm_by_tile, feature_count


def main(argv):
    start = time.time()
    logging.info("Starting the program.")

    osm_by_tile, osm_features_in_test_area = process_osm_by_tile()

    logging.debug("Preprocessing OSM data took: {}".format(time.time() - start))

    min, max, step = [int(i) for i in list(FLAGS.probability_threshold)]
    probability_thresholds = range(min, max, step)

    data_points = []
    

    prediction_files = [FLAGS.predictions_path]

    for threshold in probability_thresholds:
    
        logging.debug("Threshold: {}".format(threshold))
        for file_name in prediction_files:
            eval_start = time.time()
            for key in osm_by_tile.keys():
                osm_by_tile[key]['data']['used'] = False

            precision, recall, f1, total_pred = perform_eval(
                file_name, 
                osm_by_tile, 
                osm_features_in_test_area, 
                threshold=threshold)
            data_points.append([threshold, f1, recall, precision])
            logging.info("probability threshold: {}, \
                          f1: {}, \
                          recall: {}, \
                          precision: {}, \
                          total pred: {}".format(
                              threshold, f1, 
                              recall, precision, total_pred))
            logging.debug("Time to perform this evaluation: {}"\
                .format(time.time() - eval_start))

    if FLAGS.results_to_file:
        with open(FLAGS.output_file_path, "w") as sink:
            sink.write(str(data_points))
            


if __name__ == "__main__":

    app.run(main)
