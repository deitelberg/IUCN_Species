#!/usr/bin/env python
'''########################################################################################################
Author: David Eitelberg
Date: 4 May 2016
IDE used for development: Spyder 
Description: This script automates the calculation of zonal statistics for all species range raster layers
    (obtained from IUCN Red List) located in the 'speciesDir' directory (~25,000), for each of the
    landscape statistics are located in the 'cluDir', e.g. crop area, crop production, and tree area. 'clu'
    is short for CLUMondo, the land change model I use currently. These zonal statistics are calculated
    for all world regions located in the 'masksDir'. In the CLUMondo model, there are 24 model regions,
    and we additionally calculate global statistics, resulting in 25 regions. The zonal statistics are
    output to a CSV text file.
    
    There are two two functions defined, 'readRaster' and 'writeHeader'.  All rasters are stored locally
    in TIFF format. The 'readRaster' function reads the TIFF files, and then converts them to numpy arrays.
    The 'writeHeader' function writes the first few lines of each zonal statistics CSV file, according to
    which landscape statistic rasters are present.
    
    This script was written initially using ArcGIS tools and the arcpy package. After initial tests it
    was apparent that these tools were quite slow, so I re-wrote the script using the GDAL and numpy
    packages. This resulted in an estimated 90-95% decrease in processing time.
########################################################################################################'''

import gdal, glob, re, os, time
import numpy as np

speciesDir = "C:\\PhD_DOCUMENTS\\PhD\\Literature\\My Papers\\Article_Biodiversity priority\\Data\\From Finland\\projected_ranges\\all_species\\"    #Directory containing the species range rasters
clueDir = "C:\\PhD_DOCUMENTS\\PhD\\Literature\\My Papers\\Article_Biodiversity priority\\Data\\CLUMondo\\tiff_gdal_natArea\\"       #Directory containing the landscape characteristic rasters
masksDir = "C:\\PhD_DOCUMENTS\\PhD\\Literature\\My Papers\\Article_Biodiversity priority\\Data\\CLUMondo\\Masks\\"      #Directory containing the raster masks for each world region
csvOut = "C:\\PhD_DOCUMENTS\\PhD\\Literature\\My Papers\\Article_Biodiversity priority\\Data\\From Finland\\projected_ranges\\all_species_csv_natArea\\"    #Output directory, for storing the landscape characteristics for each species, in each model region.
logFile = csvOut+"log.txt"  #Defines a log file directory and filename.

regions = glob.glob(masksDir+"*.tif")   #Creates list of CLUMondo model region rasters
speciesLayers = glob.glob(speciesDir+"*.tif")   #Creates list of all species range layers in directory
characteristicName = glob.glob(clueDir+"*.tif") #Creates list of all clue stat rasters, e.g. crop area, pasture area, etc.


"""### Define functions for repetitive tasks ###"""
def readRaster(rasName):    #Function to read tiff raster and convert to numpy array
    name = re.split("\.",os.path.basename(rasName))[0]
    ds = gdal.Open(rasName)
    band = ds.GetRasterBand(1)
    NODATA = band.GetNoDataValue()
#    print "NO DATA  " + str(NODATA)
    ds = (band.ReadAsArray().astype(np.float))
    ds[ds==NODATA] = 0
    return (ds,name)

def writeHeader(characteristic,r):  #Function to write the csv header according to which clue stat rasters are present in directory
    header = "Species,total range area,"
    outFile = csvOut+r+".txt"
#    print outFile
    for h in characteristic:
        head = re.split("\.",os.path.basename(h))[0]
        header+=head+","
    try:
        os.remove(outFile)
    except: 
        pass
    with open(outFile, 'w') as t:
        t.write(header)


"""#### Delete existing log file if exists. ###"""
try:    
    os.remove(logFile)
except:
    pass

"""##################################################"""
"""################### Start Code ###################"""
"""##################################################"""
startTime = time.time() #Begin counting time

i=1 #Initializes an index variable, i
number = "Number of species layers:  "+str(len(speciesLayers))  #Stores the number of layers to be processed as variable, for use in timing calculations later.
print number
with open(logFile,'a') as l: l.write(number+"\n")   #Writes the number of species to a log file.
    
for region in regions:  #loop to go through 25 world regions, calculating statistics for all species in each region.
    regionTime = time.time()
    midTime = time.time()
    regionMaskVect, regionName = readRaster(region) #read in region mask raster with readRaster() function
    reg = "\nRegion: "+regionName
    print reg
    with open(logFile,'a') as l: l.write(reg+"\n")
    x=1
    
    writeHeader(characteristicName,regionName) #Writes header for output csv file
    
    for ras in speciesLayers:  #Loop through all species rasters (~25,000) to calculate statistics for each species, within the model region
        speciesVect, speciesName = readRaster(ras)  #read in species raster with readRaster() function
        spNum= "   "+str(x) + ") " + speciesName    #Assign species number and name to variable (to be written to log file later)
        print spNum
        with open(logFile,'a') as l: l.write(spNum+"\n")    #Write number of species to log file
        maskedRange = np.multiply (np.multiply(speciesVect,0.01),regionMaskVect) #Mask species range to CLUMondo region
        
        if (np.any(maskedRange)): #if the raster array contains area values, then do the below, else just print a line of 0's with no calculations. Saves time compared to going through the calculations when a species doesn't exist in the region.
            isSpecies = "       ** Species exists in "+regionName+" **"
            print isSpecies
            with open(logFile,'a') as l: l.write(isSpecies+"\n")    #Write to log file is species exists
            #Calculate total species area in region (sum of full cell areas regardless of naturalness)            
            areaRange = np.multiply(maskedRange,85.5625)    #Converts raster values from proportion to area (km2)
            sumRange = np.sum(areaRange, dtype=np.float)    #Calculates the total range area of a species
            
            stats = speciesName+","+str(round(sumRange,4))+","     #string to hold zonal statistics - species name and total range area are already added
            
            for clue in characteristicName: #Loop through clue statisitc file (e.g. grassland area, crop production, tree area, etc.) to calculate zonal statistics
                clueVect, clueName = readRaster(clue)   #read in clue statistic raster with readRaster() function       
                
                multiply = np.multiply(maskedRange,clueVect)    #multiply species range (masked) with clue stat raster
                area = np.sum(multiply, dtype=np.float) #sum all cell values in (masked) raster 
                stats+=str(round(area,4))+","
                #print "      "+clueName + "     %.2f" % area    #For testing to print clue area layers and area caluclated
        else:   #prints a line of zeros if the array contains no useful information
            stats = speciesName+",0.0,"     #string to hold zonal statistics - species name and total range area are already added
            for zero in characteristicName: #write a 0 to the stats string for every clue statistic raster that existss.
                stats+=str(float(0))+","
            
        #print stats    #For testing make sure 'stats' variable is correct
        with open(csvOut+regionName+".txt", 'a') as s:  #Writes the zonal statistics (calculated above) to a text file (csv).
            s.write("\n"+stats)
        
        if (x % 100==0): #Reports epapsed time per 100 layers, total elapsed time, and estimated time remaining to complete all processing
            time100 = "     --Time this 100 ............. "+str("%.2f"%(time.time() - midTime))
            elapsedR = "     --Elapsed time - region ............. "+str("%.2f"%(time.time() - regionTime))
            elapsedT = "     --Elapsed time - total.............. "+str("%.2f"%(time.time() - startTime))
            remaining = "     --Estimated time remaining for region #"+str(i)+", "+regionName+"... "+str("%.2f"%((time.time() - regionTime)/x*(len(speciesLayers)-x)))
            allTimes= time100+"\n"+elapsedR+"\n"+elapsedT+"\n"+remaining+"\n"   #Stores time reporting strings (the 4 lines above) into one variable so the log file only has to be opened and written to once.
            print allTimes            
            with open(logFile,'a') as l:    #Write a log file to record the steps, species, and elapsed time.  
                l.write(allTimes)
            midTime = time.time()
          
        x+=1            

        #if (x>20):   #For testing purposes. To end the loop after only a few iterations
            #break
    
    regionTime = "   Final time region "+regionName+":  "+str("%.2f"%(time.time() - regionTime))    #Calculate total time elapsed for the world region
    print regionTime
    with open(logFile,'a') as l: l.write(regionTime+"\n")   #Write time to log file

    i+=1    #Increase index variable by one

    #if (i>2):   #For testing purposes. To end the loop after only a few iterations
        #break  
print "\ndone" #Lets user know the script has finished