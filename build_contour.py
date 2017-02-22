#!/c/Python27/ARcGISx6410.5/python
#
#  Build a contour layer and annotate it.
#
from __future__ import print_function
import arcpy
import arcpy.sa
import os
from glob import glob

from utility import copy_fc, create_geodatabase, create_feature_dataset, reproject
import raster

arcpy.CheckOutExtension("3D")
arcpy.CheckOutExtension("Spatial")

class contour(object):

    sref_id = None
    sref_obj = None
    indem = None
    index_interval = interval = 40

    shortest = 20 # Shortest possible feature, little bumps and rocks should be dropped out
    bendiness = 20 # How curvy contours can be
    reference_scale = 5000 # Reference scale for annotation

    dem_path= ""
    z_factor = 1

    def __init__(self, sref_id, output_location, dem_path, z_factor):

        # Some tools will not take a string so get an object here.
        self.sref_id = sref_id
        self.sref_obj = arcpy.SpatialReference(sref_id)

        folder, gdb = os.path.split(output_location)
        self.output_location = output_location

        self.workspace = os.path.join(folder, "workspace.gdb")
        create_geodatabase(self.workspace)

        self.z_factor = z_factor
        self.dem_path = self.tune_dem(dem_path)

        return

    def tune_dem(self, dem):
        """ Set up a raster to use as the source for our contours. """

        final_dem = os.path.join(self.workspace, "raster_Smooth")
        if not arcpy.Exists(final_dem):
            print("Reprojecting %s" % dem)
            dem_projected = os.path.join(self.workspace, "raster_Project")
            raster.reproject(dem, dem_projected, self.sref_obj)

            radius = 2
            print("Smoothing raster from '%s'" % dem_projected)
            result = arcpy.sa.FocalStatistics(dem_projected, arcpy.sa.NbrCircle(radius), "MEAN", "DATA")
            result.save(final_dem)

        return final_dem

    def build_lines(self):
        """ Build the contour lines """

        print("build lines at %d" % self.interval)

        # First build a rough contour (with many tiny features)
        # then copy it less those features to the final resting place.

        arcpy.env.workspace = self.workspace

        rough_fc = "contour_%d_Rough" % self.interval
        rough_path = os.path.join(self.workspace, rough_fc)
        if arcpy.Exists(rough_path):
            print("\tAlready have '%s'\n" % rough_fc)
        else:
            # This creates a feature class that will have a field called "Type" to indicate
            # if a contour should be indexed or not

            arcpy.ContourWithBarriers_3d(self.dem_path, rough_path, 
                                         "", # barrier fc
                                         "POLYLINES",
                                         "", # values file
                                         "NO_EXPLICIT_VALUES_ONLY",
                                         0, #base
                                         self.interval, self.index_interval,
                                         "", # explicit contour list
                                         z_factor
                                         )

        interval_path = os.path.join(self.output_location, "contour_%d" % self.interval)
        if not arcpy.Exists(interval_path):
            print("\tSelecting features that are not tiny.")
            selection_layer = rough_fc + "_Layer"
            arcpy.MakeFeatureLayer_management(rough_path, selection_layer, "Shape_Length>%d" % self.shortest)
            print("Cleaned up the shapes")

        if not arcpy.Exists(interval_path):
            print("Copy contours from simplified")
            copy_fc(rough_path, interval_path)

        return

    def build_annotation(self):

        print("build annotation at %d" % self.interval)

        arcpy.env.workspace = self.workspace

        contour_fc = "contour_%d" % self.interval
        contour_path = os.path.join(self.output_location, contour_fc)
        contour_anno = contour_fc + "_Annotation"

        folder, geodatabase = os.path.split(self.output_location)

        # We break the rule here and rebuild the layer every time
        # If we don't then it will create a new class every time
        # with a number at the end 1,2,3... very annoying.
        dataset = os.path.join(self.output_location, "annotation_%d" % self.interval)
        if arcpy.Exists(dataset):
            arcpy.Delete_management(dataset)
        create_feature_dataset(dataset, self.sref_obj)

        output_layer = "Contours_%d" % self.interval
        print(contour_path, dataset, self.reference_scale, output_layer)
        arcpy.ContourAnnotation_cartography(contour_path, dataset, "Contour", str(self.reference_scale), output_layer,
                                            "BROWN", "Type", "PAGE", "ENABLE_LADDERING")

        print("Creating layer file.")
        layerfile = os.path.join(folder, "contour_%d.lyr" % self.interval)
        if arcpy.Exists(layerfile):
            try:
                arcpy.Delete_management(layerfile)
            except Exception as e:
                print ("Delete of '%s' failed, " % layerfile, e)

        arcpy.SaveToLayerFile_management(output_layer, layerfile, "RELATIVE", "CURRENT")

        return True

# ========================================================================

if __name__ == "__main__":
    # Because this script checks for existence of each object before rebuilding it, you should be able to
    # place an exit(0) ANYWHERE to test it up to that point and then re-run.
    # To get it to rebuild something you have to nuke the feature, this script WILL NOT overwrite existing things.

    # Elevation data
    source_folder = "D:\\TrailPeople\\Data_Repository\\CA\\NOAA\\Vallejo"
    src_dem = "Job343109_CA2010_coastal_DEM.tif"
    dem_path = os.path.join(source_folder, src_dem)
    z_factor = 3.28 # Convert NOAA meters to good old feet.

    # TODO Might want to do reproject and clip steps outside the class
    folder = "D:\\TrailPeople\\Marketing\\Vallejo_bluff_trail" 

    geodatabase = os.path.join(folder, "contour.gdb")
    create_geodatabase(geodatabase)

    c = contour(103239, # Nor Cal
                 geodatabase, dem_path, z_factor)

    c.index_interval = 5
    c.interval = 1
    c.reference_scale = 625
    c.build_lines()
    c.build_annotation()

    c.index_interval = 10
    c.interval = 2
    c.reference_scale = 1250
    c.build_lines()
    c.build_annotation()

    c.index_interval = 20
    c.interval = 4
    c.reference_scale = 2500
    c.build_lines()
    c.build_annotation()

    exit(0)
