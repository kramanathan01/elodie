from __future__ import unicode_literals

import requests
import urllib.request
import urllib.parse
import urllib.error

from os import path
import logging

from elodie import log
from elodie import constants
from elodie.config import load_config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

__OPENMAPS_KEY__ = None


def get_key_openmaps():
    global __OPENMAPS_KEY__
    if __OPENMAPS_KEY__ is not None:
        return __OPENMAPS_KEY__

    config_file = '%s/config.ini' % constants.application_directory
    if not path.exists(config_file):
        return None

    config = load_config()
    if('MapQuest' not in config):
        return None

    __KEY__ = config['MapQuest']['key']
    return __KEY__


def lookup(**kwargs):
    if(
        'location' not in kwargs and
        'lat' not in kwargs and
        'lon' not in kwargs
    ):
        return None

    key = get_key_openmaps()

    if(key is None):
        return None

    try:
        params = {'format': 'json', 'key': key}
        params.update(kwargs)
        path = '/geocoding/v1/address'
        if('lat' in kwargs and 'lon' in kwargs):
            path = '/nominatim/v1/reverse.php'
        url = 'http://open.mapquestapi.com%s?%s' % (
                    path,
                    urllib.parse.urlencode(params)
              )
        r = requests.get(url)
        return parse_result(r.json())
    except requests.exceptions.RequestException as e:
        log.error(e)
        return None
    except ValueError as e:
        log.error(r.text)
        log.error(e)
        return None


def parse_result(result):
    if('error' in result):
        return None

    if(
        'results' in result and
        len(result['results']) > 0 and
        'locations' in result['results'][0]
        and len(result['results'][0]['locations']) > 0 and
        'latLng' in result['results'][0]['locations'][0]
    ):
        latLng = result['results'][0]['locations'][0]['latLng']
        if(latLng['lat'] == 39.78373 and latLng['lng'] == -100.445882):
            return None

    return result


def extract_place_name(lat, lon):
    lookup_place_name = {}
    geolocation_info = lookup(lat=lat, lon=lon)
    if(geolocation_info is not None and 'address' in geolocation_info):
        address = geolocation_info['address']
        for loc in ['city', 'state', 'country']:
            if(loc in address):
                lookup_place_name[loc] = address[loc]
                # In many cases the desired key is not available so we
                #  set the most specific as the default.
                if('default' not in lookup_place_name):
                    lookup_place_name['default'] = address[loc]
    return lookup_place_name


def extract_place_coordinates(name):

    geolocation_info = lookup(location=name)

    if(geolocation_info is not None):
        if(
            'results' in geolocation_info and
            len(geolocation_info['results']) != 0 and
            'locations' in geolocation_info['results'][0] and
            len(geolocation_info['results'][0]['locations']) != 0
        ):

            # By default we use the first entry unless we find one with
            #   geocodeQuality=city.
            geolocation_result = geolocation_info['results'][0]
            use_location = geolocation_result['locations'][0]['latLng']
            # Loop over the locations to see if we come accross a
            #   geocodeQuality=city.
            # If we find a city we set that to the use_location and break
            for location in geolocation_result['locations']:
                if(
                    'latLng' in location and
                    'lat' in location['latLng'] and
                    'lng' in location['latLng'] and
                    location['geocodeQuality'].lower() == 'city'
                ):
                    use_location = location['latLng']
                    break

            return {
                'latitude': use_location['lat'],
                'longitude': use_location['lng']
            }
    return None
