from __future__ import unicode_literals

from os import path
import logging
import googlemaps

from elodie import constants
from elodie.config import load_config

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

__GOOGLEMAPS_KEY__ = None


def get_key_gmaps():
    global __GOOGLEMAPS_KEY__
    if __GOOGLEMAPS_KEY__ is not None:
        return __GOOGLEMAPS_KEY__

    config_file = '%s/config.ini' % constants.application_directory
    if not path.exists(config_file):
        return None
    config = load_config()
    if('GoogleMaps' not in config):
        return None
    try:
        apikey = config['GoogleMaps']['key']
    except KeyError:
        logger.error("GoogleMaps API Key not found.")
        return None

    if apikey and not apikey.startswith("AIza"):
        logger.error("Invalid API key provided.")
        return None

    return apikey


gmaps = googlemaps.Client(key=get_key_gmaps())


def get_address_by_latlng(lat, lng):
    try:
        resp = gmaps.reverse_geocode((lat, lng))
        return resp
    except googlemaps.exceptions.HTTPError:
        logger.error('HTTPError', exc_info=True)
        return None
    except googlemaps.exceptions.APIError:
        logger.error('APIError', exc_info=True)
        return None


def get_address_by_location(location):
    try:
        resp = gmaps.geocode(location)
        return resp
    except googlemaps.exceptions.HTTPError:
        logger.error('HTTPError', exc_info=True)
        return None
    except googlemaps.exceptions.APIError:
        logger.error('APIError', exc_info=True)
        return None


def _parse_gaddress_comps(response, gtypes):
    address_comps = response[0]['address_components']
    filter_method = lambda x: len(set(x['types']).intersection(gtypes))  # noqa
    return filter(filter_method, address_comps)


def _parse_glocation(response):
    return response[0]['geometry']['location']['lat'], \
           response[0]['geometry']['location']['lng']


def get_gaddress(resultobj):
    """ Takes latitude and longitude and returns city, state, country and
        location dict.

        We want to get sublocality_level_1 to account for cases
        where locality doesn't exist.
        if city (locality) is not there, we will assign suburb
        (sublocality_level_1) to city
    """

    gtypes = {'sublocality_level_1': 'suburb',
              'locality': 'city',
              'administrative_area_level_1': 'state',
              'country': 'country'}
    gaddress = {}  # Container dict to return matched address_components

    if not resultobj:
        return resultobj

    # get location
    gaddress['latitude'], gaddress['longitude'] = _parse_glocation(resultobj)

    # Build address dictionary
    for gaddress_iter in _parse_gaddress_comps(resultobj, gtypes.keys()):
        # Trap empty list returned from call to _parse_gaddress_comps
        if not gaddress_iter:
            break

        relevant_types = \
            set(gaddress_iter['types']).intersection(set(gtypes.keys()))

        # use values from matched gtypes['key'] as keys for gaddress dictionary
        gaddress[(gtypes[''.join(str(t) for t in relevant_types)])] = \
            gaddress_iter['long_name']

    if not gaddress:  # If empty list return empty list
        return gaddress
    # When no locality (city) is returned but sublocality_level_1 (suburb)
    # is available e.g. (Brooklyn: 40.714224, -73.961452)
    # copy suburb to city
    if 'city' not in gaddress and 'suburb' in gaddress:
            gaddress['city'] = gaddress['suburb']
    return {k: gaddress[k] for k in ('city', 'state', 'country',
                                     'latitude', 'longitude')}


def extract_place_name(lat, lon):
    lookup_place_name = {}
    geolocation_info = get_gaddress(get_address_by_latlng(lat, lon))

    if(geolocation_info is not None):
        for loc in ['city', 'state', 'country']:
            if(loc in geolocation_info):
                lookup_place_name[loc] = geolocation_info[loc]
                if('default' not in lookup_place_name):
                    lookup_place_name['default'] = geolocation_info[loc]

    return lookup_place_name


def extract_place_coordinates(name):
    if not name:
        return None

    geolocation_info = get_gaddress(get_address_by_location(name))

    if not geolocation_info:
        return None

    return {k: geolocation_info[k] for k in ('latitude', 'longitude')}
