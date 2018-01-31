from __future__ import absolute_import
from __future__ import division
from builtins import range
from past.utils import old_div
# Project imports
import mock
import os
import random
import re
import sys
from mock import patch
from tempfile import gettempdir

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))))

from . import helper
from elodie import geolocation

os.environ['TZ'] = 'GMT'


def test_decimal_to_dms():

    for x in range(0, 1000):
        target_decimal_value = random.uniform(0.0, 180.0)
        if(x % 2 == 1):
            target_decimal_value = target_decimal_value * -1

        dms = geolocation.decimal_to_dms(target_decimal_value)

        check_value = (dms[0] + dms[1] / 60 + dms[2] / 3600) * dms[3]

        target_decimal_value = round(target_decimal_value, 8)
        check_value = round(check_value, 8)

        assert target_decimal_value == check_value, '%s does not match %s' % (check_value, target_decimal_value)

def test_dms_to_decimal_positive_sign():
    decimal = geolocation.dms_to_decimal(10, 20, 100, 'NE')
    assert helper.isclose(decimal, 10.3611111111)

    decimal = geolocation.dms_to_decimal(10, 20, 100, 'ne')
    assert helper.isclose(decimal, 10.3611111111)

def test_dms_to_decimal_negative_sign():
    decimal = geolocation.dms_to_decimal(10, 20, 100, 'SW')
    assert helper.isclose(decimal, -10.3611111111)

    decimal = geolocation.dms_to_decimal(10, 20, 100, 'sw')
    assert helper.isclose(decimal, -10.3611111111)

def test_dms_string_latitude():

    for x in range(0, 5):
        target_decimal_value = random.uniform(0.0, 180.0)
        if(x % 2 == 1):
            target_decimal_value = target_decimal_value * -1

        dms = geolocation.decimal_to_dms(target_decimal_value)
        dms_string = geolocation.dms_string(target_decimal_value, 'latitude')

        check_value = 'N' if target_decimal_value >= 0 else 'S'

        assert check_value in dms_string, '%s not in %s' % (check_value, dms_string)
        assert str(dms[0]) in dms_string, '%s not in %s' % (dms[0], dms_string)

def test_dms_string_longitude():

    for x in range(0, 5):
        target_decimal_value = random.uniform(0.0, 180.0)
        if(x % 2 == 1):
            target_decimal_value = target_decimal_value * -1

        dms = geolocation.decimal_to_dms(target_decimal_value)
        dms_string = geolocation.dms_string(target_decimal_value, 'longitude')

        check_value = 'E' if target_decimal_value >= 0 else 'W'

        assert check_value in dms_string, '%s not in %s' % (check_value, dms_string)
        assert str(dms[0]) in dms_string, '%s not in %s' % (dms[0], dms_string)


@mock.patch('elodie.constants.location_db', '%s/location.json-cached' % gettempdir())
def test_place_name_deprecated_string_cached():
    # See gh-160 for backwards compatability needed when a string is stored instead of a dict
    helper.reset_dbs()
    with open('%s/location.json-cached' % gettempdir(), 'w') as f:
        f.write("""
[{"lat": 37.3667027222222, "long": -122.033383611111, "name": "OLDVALUE"}]
"""
    )
    place_name = geolocation.place_name(37.3667027222222, -122.033383611111)
    helper.restore_dbs()

    assert place_name['city'] == 'Sunnyvale', place_name

@mock.patch('elodie.constants.location_db', '%s/location.json-cached' % gettempdir())
def test_place_name_cached():
    helper.reset_dbs()
    with open('%s/location.json-cached' % gettempdir(), 'w') as f:
        f.write("""
[{"lat": 37.3667027222222, "long": -122.033383611111, "name": {"city": "UNITTEST"}}]
"""
    )
    place_name = geolocation.place_name(37.3667027222222, -122.033383611111)
    helper.restore_dbs()

    assert place_name['city'] == 'UNITTEST', place_name

def test_place_name_no_default():
    # See gh-160 for backwards compatability needed when a string is stored instead of a dict
    helper.reset_dbs()
    place_name = geolocation.place_name(123456.000, 123456.000)
    helper.restore_dbs()

    assert place_name['default'] == 'Unknown Location', place_name
