"""Look up geolocation information for media objects."""
from __future__ import print_function
from __future__ import division
from future import standard_library
from past.utils import old_div

standard_library.install_aliases()  # noqa

from os import path
import logging

from elodie.config import load_config
from elodie import constants
from elodie.localstorage import Db
from elodie import gmapsgeo
from elodie import openmapsgeo

__PROVIDER__ = None
__DEFAULT_LOCATION__ = 'Unknown Location'
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


def get_provider():
    global __PROVIDER__
    if __PROVIDER__ is not None:
        return __PROVIDER__

    config_file = '%s/config.ini' % constants.application_directory
    if not path.exists(config_file):
        return None

    config = load_config()
    if('Provider' in config):
        __PROVIDER__ = config['Provider']['name']
    else:
        __PROVIDER__ = 'MapQuest'
    return __PROVIDER__


def coordinates_by_name(name):
    # Try to get cached location first
    db = Db()
    cached_coordinates = db.get_location_coordinates(name)
    if(cached_coordinates is not None):
        return {
            'latitude': cached_coordinates[0],
            'longitude': cached_coordinates[1]
        }
    # If the name is not cached then we go ahead with an API lookup
    provider = get_provider()

    if provider == 'GoogleMaps':
        return gmapsgeo.extract_place_coordinates(name)

    return openmapsgeo.extract_place_coordinates(name)


def decimal_to_dms(decimal):
    decimal = float(decimal)
    decimal_abs = abs(decimal)
    minutes, seconds = divmod(decimal_abs*3600, 60)
    degrees, minutes = divmod(minutes, 60)
    degrees = degrees
    sign = 1 if decimal >= 0 else -1
    return (degrees, minutes, seconds, sign)


def dms_to_decimal(degrees, minutes, seconds, direction=' '):
    sign = 1
    if(direction[0] in 'WSws'):
        sign = -1
    return (
        float(degrees) + old_div(float(minutes), 60) +
        old_div(float(seconds), 3600)
    ) * sign


def dms_string(decimal, type='latitude'):
    # Example string -> 38 deg 14' 27.82" S
    dms = decimal_to_dms(decimal)
    if type == 'latitude':
        direction = 'N' if decimal >= 0 else 'S'
    elif type == 'longitude':
        direction = 'E' if decimal >= 0 else 'W'
    return '{} deg {}\' {}" {}'.format(dms[0], dms[1], dms[2], direction)


def place_name(lat, lon):
    lookup_place_name_default = {'default': __DEFAULT_LOCATION__}
    if(lat is None or lon is None):
        return lookup_place_name_default

    # Convert lat/lon to floats
    if(not isinstance(lat, float)):
        lat = float(lat)
    if(not isinstance(lon, float)):
        lon = float(lon)

    # Try to get cached location first
    db = Db()
    # 3km distace radious for a match
    cached_place_name = db.get_location_name(lat, lon, 3000)
    # We check that it's a dict to coerce an upgrade of the location
    #  db from a string location to a dictionary. See gh-160.
    if(isinstance(cached_place_name, dict)):
        return cached_place_name

    provider = get_provider()

    if provider == 'GoogleMaps':
        lookup_place_name = gmapsgeo.extract_place_name(lat, lon)
    else:
        lookup_place_name = openmapsgeo.extract_place_name(lat, lon)

    if(lookup_place_name):
        db.add_location(lat, lon, lookup_place_name)
        # TODO: Maybe this should only be done on exit and not for every write.
        db.update_location_db()

    if('default' not in lookup_place_name):
        lookup_place_name = lookup_place_name_default

    return lookup_place_name
