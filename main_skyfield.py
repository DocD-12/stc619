from skyfield.api import load
from skyfield.sgp4lib import EarthSatellite
from skyfield.toposlib import wgs84
from datetime import timedelta
from pytz import timezone


ts = load.timescale()
t = ts.now()
t0 = t
t1 = t0 + timedelta(days=7)

l1 = '1 57202U 23091AN  25031.15474867  .00008229  00000+0  47874-3 0  9997'
l2 = '2 57202  97.5855  87.8579 0011980  52.4663 307.7654 15.12253614 87902'
sl = EarthSatellite(l1, l2, 'CSTP 1.1 (STC 1.1)', ts)

lat, lon = 59.983833, 30.394778
stp = wgs84.latlon(lat, lon)
dif = sl - stp

t2, ev = sl.find_events(stp, t0, t1, altitude_degrees=30)

for ti, event in zip(t2, ev):
    if event == 1:
        tm = ti.astimezone(timezone('Europe/Moscow')).strftime('%Y_%b_%d %H:%M:%S')
        top = dif.at(ti)
        alt, az, dist = top.altaz()
#        alt, az = alt.degrees, az.degrees
        print(f'Время кульминации (UTC+3): {tm}\n\tУгол над горизонтом: {alt}\n\tАзимут: \t\t\t{az}')
