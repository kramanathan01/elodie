from __future__ import absolute_import
from __future__ import division
# Project imports
import mock
import os
import sys
from mock import patch


sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))))

from . import helper
from elodie import openmapsgeo

os.environ['TZ'] = 'GMT'


def test_reverse_lookup_with_valid_key():
    res = openmapsgeo.lookup(lat=37.368, lon=-122.03)
    assert res['address']['city'] == 'Sunnyvale', res

def test_reverse_lookup_with_invalid_lat_lon():
    res = openmapsgeo.lookup(lat=999, lon=999)
    assert res is None, res

@mock.patch('elodie.openmapsgeo.__OPENMAPS_KEY__', 'invalid_key')
def test_reverse_lookup_with_invalid_key():
    res = openmapsgeo.lookup(lat=37.368, lon=-122.03)
    assert res is None, res

def test_lookup_with_valid_key():
    res = openmapsgeo.lookup(location='Sunnyvale, CA')
    latLng = res['results'][0]['locations'][0]['latLng']
    assert latLng['lat'] == 37.36883, latLng
    assert latLng['lng'] == -122.03635, latLng

def test_lookup_with_invalid_location():
    res = geolocation.lookup(location='foobar dne')
    assert res is None, res

def test_lookup_with_invalid_location():
    res = openmapsgeo.lookup(location='foobar dne')
    assert res is None, res

def test_lookup_with_valid_key():
    res = openmapsgeo.lookup(location='Sunnyvale, CA')
    latLng = res['results'][0]['locations'][0]['latLng']
    assert latLng['lat'] == 37.36883, latLng
    assert latLng['lng'] == -122.03635, latLng

@mock.patch('elodie.openmapsgeo.__OPENMAPS_KEY__', 'invalid_key')
def test_lookup_with_invalid_key():
    res = openmapsgeo.lookup(location='Sunnyvale, CA')
    assert res is None, res

@mock.patch('elodie.openmapsgeo.__OPENMAPS_KEY__', '')
def test_lookup_with_no_key():
    res = openmapsgeo.lookup(location='Sunnyvale, CA')
    assert res is None, res

def test_parse_result_with_error():
    res = openmapsgeo.parse_result({'error': 'foo'})
    assert res is None, res

def test_parse_result_with_city():
    # http://open.mapquestapi.com/nominatim/v1/reverse.php?lat=37.368&lon=-122.03&key=key_goes_here&format=json
    results = {
        "place_id": "60197412",
        "osm_type": "way",
        "osm_id": "30907961",
        "lat": "37.36746105",
        "lon": "-122.030237558742",
        "display_name": "111, East El Camino Real, Sunnyvale, Santa Clara County, California, 94087, United States of America",
        "address": {
            "house_number": "111",
            "road": "East El Camino Real",
            "city": "Sunnyvale",
            "county": "Santa Clara County",
            "state": "California",
            "postcode": "94087",
            "country": "United States of America",
            "country_code": "us"
        }
    }

    res = openmapsgeo.parse_result(results)
    assert res == results, res

def test_parse_result_with_lat_lon():
    # http://open.mapquestapi.com/geocoding/v1/address?location=abcdefghijklmnopqrstuvwxyz&key=key_goes_here&format=json
    results = {
        "results": [
            {
               "locations": [
                    {
                        "latLng": {
                            "lat": 123.00,
                            "lng": -142.99
                        }
                    }
                ]
            }
        ]
    }

    res = openmapsgeo.parse_result(results)
    assert res == results, res

def test_parse_result_with_unknown_lat_lon():
    # http://open.mapquestapi.com/geocoding/v1/address?location=abcdefghijklmnopqrstuvwxyz&key=key_goes_here&format=json
    results = {
        "results": [
            {
               "locations": [
                    {
                        "latLng": {
                            "lat": 39.78373,
                            "lng": -100.445882
                        }
                    }
                ]
            }
        ]
    }

    res = openmapsgeo.parse_result(results)
    assert res is None, res
