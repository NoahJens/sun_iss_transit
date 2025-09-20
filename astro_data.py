from skyfield.api import load, EarthSatellite, Angle, wgs84

ts = load.timescale()
t = ts.now()

planets = load('de421.bsp')
earth, sun = planets['earth'], planets['sun']