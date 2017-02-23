#!/c/Python27/ARcGISx6410.5/python
import sys, os
import subprocess

sys.path.append(r'C:\Users/bwilson/GDAL/bin/gdal/python')
sys.path.append(r'C:\Users/bwilson/GDAL/bin/gdal/python/osgeo')
from osgeo import gdal, gdal_array
from osgeo.gdalconst import *
from osgeo import ogr

print ogr
print gdal


interval = "100"

os.chdir("d:/TrailPeople/Marketing/Vallejo_bluff_trail")
tif = "rasterProject.tif"
shp = "contour.shp"
args = [contour_bin, "-i", interval, "-a", "Contour", tif, shp]
p = subprocess.check_output(args)

print "response", p
