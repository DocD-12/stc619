from datetime import timedelta
from skyfield.api import load
from skyfield.toposlib import wgs84

def get_satellite_coordinates(number):
    ts = load.timescale()
    t = ts.now()
    t1 = t + timedelta(minutes=5)
    stations_url = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle'
    satellites = load.tle_file(stations_url)
    print('Loaded', len(satellites), 'satellites')
    by_number = {sat.model.satnum: sat for sat in satellites}
    satellite = by_number[number]
    # by_name = {sat.name: sat for sat in satellites}
    # satellite = by_name['POLYTECH-UNIVERSE 3 (R*)']
    c = []
    for i in range(25):
        t1 += timedelta(minutes=5)
        geocentric = satellite.at(t1)
        lat_satellite, lon_satellite = wgs84.latlon_of(geocentric)
        c.append([lat_satellite.degrees, lon_satellite.degrees])
    return c

print(get_satellite_coordinates(57191))