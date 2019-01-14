#######################################################################
# Analysis of flight delays and taxiing times and its relationship to the local weather for Jan 2018
#	Author: Anand V. Lakshmikumaran
#
# In this script, I am experimenting with combining data from different sources to find correlations 
# between relevant parameters and experimenting with creating interactive plots using Bokeh.  The data 
# and the correponding data sources used in this analysis are
#
#	Flight details are obtained from 'On-Time Flight performance database' 
#		(https://www.transtats.bts.gov/DL_SelectFields.asp?DB_Short_Name=On-Time&Table_ID=236)
#
#	Airline details are obtained from 'Carrier Decode Table' at
#		(https://www.transtats.bts.gov/Tables.asp?DB_ID=595&DB_Name=Aviation%20Support%20Tables&DB_Short_Name=Aviation%20Support%20Tables#)
#
#	Airport information (including precise location) is obtained from 'Master Coordinate Table' at 
#		(https://www.transtats.bts.gov/Tables.asp?DB_ID=595&DB_Name=Aviation%20Support%20Tables&DB_Short_Name=Aviation%20Support%20Tables#)
#
#	Daily average weather conditions are obtained from 'National Climatic Data Center (NCDC)' at 
#		(ftp://ftp.ncdc.noaa.gov/pub/data/gsod)
#
#	Information (including precise location) about weather stations are obtained from 'Station list'at 
#		(ftp://ftp.ncdc.noaa.gov/pub/data/noaa/isd-history.txt)
#
# All data presented here only correspond to airports within the US for the month of January 2018.  
# Data for other time periods (month, year) are availabe at the sites mentioned above.  Similar 
# analysis could be applied to those other time periods by downloading the appropriate data sets.  
# But, that is beyond the scope of this analysis.
#######################################################################
#  Import required libraries and Delete all pre-defined variables
#######################################################################
import numpy as Numpy
#import bokeh as Bokeh
import bokeh.plotting as BokehPlotting
import bokeh.io as BokehIO
import bokeh.palettes as BokehPalettes
import bokeh.models as BokehModels
import bokeh.layouts as BokehLayouts
import bokeh.models.widgets as BokehWidgets
import bokeh.core.properties as BokehCoreProps
import pandas as Pandas
import math as Math
import os as Os
for name in dir():
    if not name.startswith('_'):
        del name
Pandas.set_option('display.expand_frame_repr', False)
#######################################################################
# User Input
#   file names and locations
#######################################################################
baseDir = 'data/'
yyyymmOfInt = '201801'
airportInfoFile = 'Airport_locations.csv'
airlinesFile = 'Carriers.csv'
weatherStatLocFile = 'isd-history.txt'
weatherServer = 'local' # if weather files are going to be local
flightFile = 'Flights_onTime_' + yyyymmOfInt + '.pickle'
yearOfInt = yyyymmOfInt[0:4]
#TOOLS = "crosshair,hover,save,pan,wheel_zoom,box_zoom,reset,box_select,lasso_select"
TOOLS = "hover,pan,zoom_in,zoom_out,box_zoom,reset,save"
flightColsFull = ['Date', 'CAR', 'TAIL', 'FLNum', 'ORIGIN_ID', 'ORIGIN', 'DEST_ID', 'DEST', 
              'DEP_SCH', 'DEP_ACT', 'DEP_DEL', 'DEP_TAXI', 'DEP_OFF',
              'ARR_ON', 'ARR_TAXI', 'ARR_SCH', 'ARR_ACT', 'ARR_DEL',
              'CANCEL', 'CANCEL_CODE', 'DIV', 'FLY_SCH', 'FLY_ACT', 'FLY_AIR', 'FLY_DIST',
              'DEL_CAR', 'DEL_WET', 'DEL_NAS', 'DEL_SEC', 'DEL_AIR']
flightColNos = [0, 1, 4, 6, 10, 11, 14, 17]
flightCols = ['Date', 'CAR', 'AIRPORT_ID', 'DURATION']
airportInfoColNos = [0,3,4,18,23]
airportInfoCols = ['AIRPORT_ID', 'Airport', 'City', 'LAT', 'LON']
#######################################################################
# User defined functions
#######################################################################
def distance(loc1, loc2):
    # Uses the Haversine formula to compute and return the distance (in km) between 
    #   'loc1' = [lat1, lon1] and 'loc2' = [lat2, lon2]
    p = (Math.pi/180)  #Pi/180
    a = 0.5 - Math.cos((loc2[0]-loc1[0])*p)/2 + Math.cos(loc1[0]*p)*Math.cos(loc2[0]*p) * (1-Math.cos((loc2[1]-loc1[1])*p)) / 2
    return 12742 * Math.asin(Math.sqrt(a)) # 2 * R; R = 6371 km

def is_float(x):
    try:
        float(x)
        return True
    except:
        return False
    
def nearest_Station(loc):
	#######################################################################
    # given the data frame 'weatherStations' that contains 'STN' 'WBAN', and 'LOC' = [LAT, LON]
    # find the weather station that is closest to 'loc' = [LAT, LON]
    # and return the a list of 'STN', 'WBAN', and 'distance to the closest station'
	#######################################################################
    
    #weatherStations = weatherStatData
    #loc = (39.86166667, -104.67305556)
    
    localWeatherStat = weatherStatData.copy()
    localWeatherStat['dist'] = localWeatherStat['LOC'].apply(lambda x: distance([float(x[0]), float(x[1])], [loc[0], loc[1]]))
    localWeatherStat = localWeatherStat.sort_values(['dist'], ascending=['False']).iloc[0,]
    
    return [localWeatherStat['STN'], 
            format(localWeatherStat['WBAN'],'05d'), 
            round(localWeatherStat['dist'],0)]
    
def weatherData(statName):
    #######################################################################
    # given the stationName ('STAT_WBAN_YYYY.op.gz') and 'weatherServer' info,
    # read and clean the data and return a dataframe of weather data.
    #######################################################################	
    Os.system('gunzip -f ' + Os.path.join(Os.path.dirname(__file__), baseDir + statName))
    airpWet = Pandas.DataFrame()    # To ensure it returns an empty Dataframe if no data exists.
    airpWet = Pandas.read_fwf(Os.path.join(Os.path.dirname(__file__), baseDir + statName).split('.')[0] + '.op',
                            names = ['STN', 'WBAN', 'YEARMODA', 'TEMP', 'TEMP_Count', 
                                     'DEWP', 'DEWP_Count', 'SLP', 'SLP_Count', 'STP', 'STP_Count', 
                                     'VISIB', 'VISIB_Count', 'WDSP', 'WDSP_Count', 'MXSPD', 'GUST',
                                     'MAX', 'MAX_Flag', 'MIN', 'MIN_Flag', 'PRCP', 'PRCP_Flag', 
                                     'SNDP', 'FRSHTT'], 
                                     header = None,
                                     colspecs = [(0,6), (7,12), (14,22), (24,30), (31,33), (35,41),
                                                 (42,44), (46,52), (53,55), (57,63), (64,66), (68,73),
                                                 (74,76), (78,83), (84,86), (88,93), (95,100), (102,108),
                                                 (108, 109), (110,116), (116,117), (118,123), (123,124), 
                                                 (125,130), (132,138)],
                                                 delim_whitespace=True, skiprows=1)
    Os.system(f'gzip -f {statName.split(".")[0]}.{statName.split(".")[1]}')
    airpWet.drop(['STN', 'WBAN', 'TEMP_Count', 'DEWP_Count', 'SLP_Count', 'STP_Count', 'VISIB_Count', 
                  'WDSP_Count', 'MAX_Flag', 'MIN_Flag', 'PRCP_Flag'], axis=1, inplace=True)
    airpWet = airpWet.loc[airpWet['YEARMODA'].apply(lambda x: '201801' in str(x))]
    #
    # Fill up the unmeasured values with 'unexpected' values and break up the FRSHTT column
    #
    airpWet.replace({'TEMP':  {9999.9: -50}}, inplace=True)
    airpWet.replace({'DEWP':  {9999.9: -50}}, inplace=True)
    airpWet.replace({'MAX':   {9999.9: -50}}, inplace=True)
    airpWet.replace({'MIN':   {9999.9: -50}}, inplace=True)
    airpWet.replace({'SLP':   {9999.9: 0}}, inplace=True)
    airpWet.replace({'STP':   {9999.9: 0}}, inplace=True)
    airpWet.replace({'VISIB': {999.9:  -1}}, inplace=True)
    airpWet.replace({'MXSPD': {999.9:  -1}}, inplace=True)
    airpWet.replace({'WDSP':  {999.9:  -1}}, inplace=True)
    airpWet.replace({'GUST':  {999.9:  -1}}, inplace=True)
    airpWet.replace({'PRCP':  {99.99:  0}}, inplace=True)
    airpWet.replace({'SNDP':  {999.9:  0}}, inplace=True)
    airpWet['Fog'] = airpWet['FRSHTT'].apply(lambda x: int(format(x, '06d')[0]))
    airpWet['Rain'] = airpWet['FRSHTT'].apply(lambda x: int(format(x, '06d')[1]))
    airpWet['Snow'] = airpWet['FRSHTT'].apply(lambda x: int(format(x, '06d')[2]))
    airpWet['Hail'] = airpWet['FRSHTT'].apply(lambda x: int(format(x, '06d')[3]))
    airpWet['Thunder'] = airpWet['FRSHTT'].apply(lambda x: int(format(x, '06d')[4]))
    airpWet['Tornado'] = airpWet['FRSHTT'].apply(lambda x: int(format(x, '06d')[5]))
    airpWet.drop(['FRSHTT'], axis=1, inplace=True)
    airpWet = airpWet.rename(columns={'YEARMODA': 'Date'})
    #
    airpWet['Date'] = airpWet['Date'].apply(lambda x: str(x)[0:4] + '-' + str(x)[4:6] + '-' + str(x)[6:8])
    #
    return airpWet
#######################################################################
# Read in the condensed flight on time data from the pickle file
# os.path.dirname(__file__) ->  Os.path.join(Os.path.dirname(__file__), baseDir + flightFile) + '.gz')
#######################################################################
Os.system('gunzip ' + Os.path.join(Os.path.dirname(__file__), baseDir + flightFile) + '.gz')
flightData = Pandas.read_pickle(Os.path.join(Os.path.dirname(__file__), baseDir + flightFile))
#######################################################################
# Combine arrival and departure delays and arrival and departure taxi times
#######################################################################
flightDepDel = flightData[['Date', 'CAR', 'ORIGIN_ID', 'DEP_DEL']].copy()
flightArrDel = flightData[['Date', 'CAR', 'DEST_ID', 'ARR_DEL']].copy()
flightDepTaxi = flightData[['Date', 'CAR', 'ORIGIN_ID', 'DEP_TAXI']].copy()
flightArrTaxi = flightData[['Date', 'CAR', 'DEST_ID', 'ARR_TAXI']].copy()
flightDepDel.columns = flightArrDel.columns = flightDepTaxi.columns = flightArrTaxi.columns = flightCols
flightDepDel['Type'] = 'DEP_DEL'
flightArrDel['Type'] = 'ARR_DEL'
flightDepTaxi['Type'] = 'DEP_TAXI'
flightArrTaxi['Type'] = 'ARR_TAXI'
flightDur = Pandas.concat([flightDepDel, flightArrDel, flightDepTaxi, flightArrTaxi])
del flightData, flightDepDel, flightArrDel, flightDepTaxi, flightArrTaxi
#######################################################################
# Only select those airlines that have a large number of flights (at least 2 per hour on average)
# Merge this info with airline names
#######################################################################
topAirlines = flightDur.groupby(['CAR', 'Type'])['DURATION'].agg(['count']).reset_index().rename(columns={'count':'AirlMonthTotal'})
topAirlines = topAirlines.loc[topAirlines['AirlMonthTotal'] > 24*2*flightDur['Date'].nunique()]
#
airlineData = Pandas.read_csv(Os.path.join(Os.path.dirname(__file__), baseDir + airlinesFile), index_col=False)
airlineData.columns = ['CAR', 'Airline']
topAirlines = topAirlines.merge(airlineData, on=['CAR'], how='inner')
del airlineData
#######################################################################
# Only select those airports that have a large number of flights (at least 2 per hour on average)
# Merge this with airport info 
#######################################################################
topAirports = flightDur.groupby(['AIRPORT_ID', 'Type'])['DURATION'].agg(['count']).reset_index().rename(columns={'count':'AirpMonthTotal'})
topAirports = topAirports.loc[topAirports['AirpMonthTotal'] > 24*2*flightDur['Date'].nunique()]
#
airportData = Pandas.read_csv(Os.path.join(Os.path.dirname(__file__), baseDir + airportInfoFile), index_col=False)
airportData = airportData.iloc[:,airportInfoColNos].copy()
airportData.columns = airportInfoCols
airportData = airportData.dropna(subset=['LAT', 'LON'])
topAirports = topAirports.merge(airportData, on=['AIRPORT_ID'], how='inner')
del airportData
#######################################################################
# Extract the location of the weather stations that are active during the time period
# of the flight delays.  Make sure to include only those data that have valid LAT and LON
#######################################################################
weatherStatData = Pandas.read_fwf(Os.path.join(Os.path.dirname(__file__), baseDir + weatherStatLocFile), 
                                  names = ['STN', 'WBAN', 'STN_Name', 'CTRY', 'ST', 'CALL', 
                                           'LAT', 'LON', 'ELEV_M', 'BEGIN', 'END'],
                                           header = None,
                                           colspecs = [(0,6), (7,12), (13,42), (43,47), (48,50), (51,56), 
                                                       (57,64), (65,73), (74,81), (82,90), (91,99)], 
                                           delim_whitespace=True, skiprows=22)
weatherStatData = weatherStatData.loc[(weatherStatData['BEGIN'] < int(yyyymmOfInt + '01')) & 
                                      (weatherStatData['END'] > int(yyyymmOfInt + '31'))]
weatherStatData = weatherStatData.dropna(subset=['LAT', 'LON'])
weatherStatData = weatherStatData.loc[(weatherStatData['LAT'].apply(lambda x: is_float(x))) &
                                      (weatherStatData['LON'].apply(lambda x: is_float(x)))]
weatherStatData['LOC'] = list(zip(weatherStatData['LAT'], weatherStatData['LON']))
weatherStatData.drop(['CTRY', 'ST', 'CALL', 'BEGIN', 'END', 'LAT', 'LON'], axis=1, inplace=True)
#######################################################################
# For each of the airports in 'topAirports', find the nearest weather station 
#######################################################################
airpWet = topAirports.loc[topAirports['Type']=='DEP_DEL', ['AIRPORT_ID', 'LAT', 'LON']]
airpWet['LOC'] = list(zip(airpWet['LAT'], airpWet['LON']))
airpWet['LOC'] = airpWet['LOC'].apply(lambda x: nearest_Station(x))
airpWet['statName'] = airpWet['LOC'].apply(lambda x: x[0] + '-' + x[1] + '-' + yearOfInt + '.op.gz')
airpWet['dist2WetStat'] = airpWet['LOC'].apply(lambda x: x[2])
airpWet.drop(['LAT', 'LON', 'LOC'], axis=1, inplace=True)    
topAirports = topAirports.merge(airpWet, on=['AIRPORT_ID'], how='inner')
del weatherStatData, airpWet
#######################################################################
# Merge flightDur with topAirports and topAirlines
#######################################################################
flightDur = flightDur.merge(topAirports, on=['AIRPORT_ID', 'Type'], how='inner')
flightDur = flightDur.merge(topAirlines, on=['CAR', 'Type'], how='inner')
del topAirports, topAirlines
airportList = list(flightDur.sort_values(['City'], ascending=['True'])['City'].unique())
airlineList = list(flightDur.sort_values(['Airline'], ascending=['True'])['Airline'].unique())
#######################################################################
# These will be the base data for rest of the analysis
# Select a airport and airline (interactively)
# Extract the flightDelays and taxiTimes just for this airport
#######################################################################
airport = [x for x in airportList if 'Denver' in x][0]
airline = [x for x in airlineList if 'United' in x][0]
airpByDate = flightDur.loc[(flightDur['City']==airport)]
#######################################################################
statName = airpByDate.statName.unique()[0]
airpWet = weatherData(statName)
#airpByDatestats = airpByDatestats.merge(airpWet, on=['Date'], how='inner')
#
weatherParams = sorted(list(airpWet.columns)[1:len(list(airpWet.columns))])
#######################################################################
# Styling for a plot
#######################################################################
def style(p):
    # Title 
    p.title.align = 'center'
    p.title.text_font_size = '14pt'
    p.title.text_font = 'Helvetica'

    # Axis titles
    p.xaxis.axis_label_text_font_size = '14pt'
    p.xaxis.axis_label_text_font_style = 'bold'
    p.yaxis.axis_label_text_font_size = '14pt'
    p.yaxis.axis_label_text_font_style = 'bold'

    # Tick labels
    p.xaxis.major_label_text_font_size = '12pt'
    p.yaxis.major_label_text_font_size = '12pt'

    return p

#######################################################################
# Interactive plot of Expenses vs Year, all categories stacked up OR for a specific Category.
#######################################################################
def make_plot_delay(flight):

    # For debug only
    #BokehIO.output_file("tmp.html")
    #flight = flightDur
    #airline = 'United Air Lines Inc.' 
    #airport = 'Denver, CO'
    #binW = 5
    
    
    airline = airlInp.value
    airport = airpInp.value
    binW = binWid.value

    minAll, maxAll = flight['DURATION'].quantile(0.02), flight['DURATION'].quantile(0.98)
    
    monthFull = flight.loc[(flight['City']==airport) & (flight['Airline']==airline)]
    #monthFullstats = monthFull.groupby(['Type'])['DURATION'].agg(['mean', 'median', 'std', 'min', 'max', 'count']).reset_index()

    #######################################################################

    minDepDel = min(monthFull.loc[monthFull['Type']=='DEP_DEL', 'DURATION'])
    maxDepDel = max(monthFull.loc[monthFull['Type']=='DEP_DEL', 'DURATION'])
    histDepDel, edgesDepDel = Numpy.histogram(monthFull.loc[monthFull['Type']=='DEP_DEL', 'DURATION'], 
                                  density=True, bins=Numpy.arange(minDepDel, maxDepDel, binW))
    
    minArrDel = min(monthFull.loc[monthFull['Type']=='ARR_DEL', 'DURATION'])
    maxArrDel = max(monthFull.loc[monthFull['Type']=='ARR_DEL', 'DURATION'])
    histArrDel, edgesArrDel = Numpy.histogram(monthFull.loc[monthFull['Type']=='ARR_DEL', 'DURATION'], 
                                  density=True, bins=Numpy.arange(minArrDel, maxArrDel, binW))
    
    plt1 = BokehPlotting.figure(
                             title=f'Delays at {airport} for {airline}', 
                             x_axis_label='Duration (mins)', 
                             y_axis_label='Fraction of occurences',
                             plot_width=900, plot_height=500,
                             x_range = (minAll, maxAll),
                             #tooltips = [('Year', '@Year'),('Exp.', '@$category')]
                             tools = TOOLS)                                

    
    plt1.quad(top=histDepDel, bottom=0, left=edgesDepDel[:-1], right=edgesDepDel[1:],
              fill_color="red", line_color="white", alpha=0.5, legend='Departures')
    
    plt1.quad(top=histArrDel, bottom=0, left=edgesArrDel[:-1], right=edgesArrDel[1:],
          fill_color="blue", line_color="white", alpha=0.5, legend='Arrivals')
     
    plt1.legend.location = "top_right"
    plt1.legend.orientation = "vertical"       
    
    #######################################################################
    
    minDepTaxi, maxDepTaxi = min(monthFull.loc[monthFull['Type']=='DEP_TAXI', 'DURATION']), max(monthFull.loc[monthFull['Type']=='DEP_TAXI', 'DURATION'])
    histDepTaxi, edgesDepTaxi = Numpy.histogram(monthFull.loc[monthFull['Type']=='DEP_TAXI', 'DURATION'], 
                                  density=True, bins=Numpy.arange(minDepTaxi, maxDepTaxi, binW))
    
    minArrTaxi, maxArrTaxi = min(monthFull.loc[monthFull['Type']=='ARR_TAXI', 'DURATION']), max(monthFull.loc[monthFull['Type']=='ARR_TAXI', 'DURATION'])
    histArrTaxi, edgesArrTaxi = Numpy.histogram(monthFull.loc[monthFull['Type']=='ARR_TAXI', 'DURATION'], 
                                  density=True, bins=Numpy.arange(minArrTaxi, maxArrTaxi, binW))
    
    plt2 = BokehPlotting.figure(
                             title=f'Taxiing times at {airport} for {airline}', 
                             x_axis_label='Duration (mins)', 
                             y_axis_label='Fraction of occurences',
                             plot_width=900, plot_height=500,
                             x_range = (minAll, maxAll),
                             #tooltips = [('Year', '@Year'),('Exp.', '@$category')]
                             tools = TOOLS)                                
    
    plt2.quad(top=histDepTaxi, bottom=0, left=edgesDepTaxi[:-1], right=edgesDepTaxi[1:],
              fill_color="red", line_color="white", alpha=0.5, legend='Departures')
    
    plt2.quad(top=histArrTaxi, bottom=0, left=edgesArrTaxi[:-1], right=edgesArrTaxi[1:],
          fill_color="blue", line_color="white", alpha=0.5, legend='Arrivals')
    
    
    plt2.legend.location = "top_right"
    plt2.legend.orientation = "vertical"    
    
    #######################################################################
    
    plt = BokehLayouts.column(style(plt1), style(plt2))
    
    #BokehIO.save(plt)

    return plt

#######################################################################
# Interactive plot of Expenses vs month (for specific year), all categories stacked up OR for a specific Category.
#######################################################################
def make_plot_Weather(flight):
    
    # For debug only
    #BokehIO.output_file("tmp.html")
    #flight = flightDur
    #airport = 'Denver, CO'
    #param = 'TEMP'
    #binW = 5
    
    airport = airpInp.value
    param = wetInp.value
    binW = binWid.value
    
    airpByDate = flight.loc[(flight['City']==airport)].copy()
    airpByDatestats = airpByDate.groupby(['Date', 'Type', 'AirpMonthTotal'])['DURATION'].agg(['mean', 'median', 'count']).reset_index()
    statName = airpByDate.statName.unique()[0]    
    airpWet = weatherData(statName)
    airpByDatestats = airpByDatestats.merge(airpWet, on=['Date'], how='inner')
    
    airpByDate['Day'] = airpByDate['Date'].apply(lambda x: x[8:10])
    airpByDatestats['Day'] = airpByDatestats['Date'].apply(lambda x: x[8:10])
    
    #######################################################################
    
    pltTopLeft = BokehPlotting.figure(x_range = (0, airpByDatestats['Date'].nunique()),
                                 title="Delays by Day", 
                                 x_axis_label='Day of month', 
                                 y_axis_label='Delay (mins)',
                                 plot_width=400, plot_height=300,
                                 tools = TOOLS,
                                 tooltips = [('Day', '@Day'),
                                             ('Avg', '@mean'),
                                             ('Med', '@median'),
                                             ('Count', '@count')]    
                                 )
    pltTopLeft.circle(x = 'Day', y = 'mean', line_color='red' ,color = 'red', fill_alpha=1, size=5,
                      source = airpByDatestats.loc[airpByDatestats['Type']=='DEP_DEL'], legend='Dep')
    
    pltTopLeft.circle(x = 'Day', y = 'mean', line_color='blue' ,color = 'blue', fill_alpha=1, size=5,
                  source = airpByDatestats.loc[airpByDatestats['Type']=='ARR_DEL'], legend='Arr')
                                                
    #pltTopLeft.legend.location = (0, 200)
    pltTopLeft.legend.orientation = "horizontal"
    
    ######################################################################
    
    pltTopRight = BokehPlotting.figure(
                                 title=f'Delays vs {param}', 
                                 x_axis_label=f'{param}', 
                                 y_axis_label='Delay (mins)',
                                 plot_width=400, plot_height=300,
                                 tools = TOOLS,
                                 tooltips = [(f'{param}', '@x'),
                                             ('Avg delay (min)', '@y')]    
                                 )
    pltTopRight.circle(x = param, y = 'mean', line_color='red' ,color = 'red', fill_alpha=1, size=5,
                      source = airpByDatestats.loc[airpByDatestats['Type']=='DEP_DEL'], legend='Dep')
    
    pltTopRight.circle(x = param, y = 'mean', line_color='blue' ,color = 'blue', fill_alpha=1, size=5,
                  source = airpByDatestats.loc[airpByDatestats['Type']=='ARR_DEL'], legend='Arr')
                                                
    #pltTopRight.legend.location = (0, 200)
    pltTopRight.legend.orientation = "horizontal"
    
    #######################################################################
    
    pltBotLeft = BokehPlotting.figure(x_range = (0, airpByDatestats['Date'].nunique()),
                                 title=f'{param} vs Day', 
                                 x_axis_label='Day', 
                                 y_axis_label=f'{param}',
                                 plot_width=400, plot_height=300,
                                 tools = TOOLS,
                                 tooltips = [('Day', '@x'),
                                             (f'{param}', '@y')
                                             ]    
                                 )
    pltBotLeft.circle(x = 'Day', y = param, line_color='red' ,color = 'red', fill_alpha=1, size=5,
                      source = airpByDatestats.loc[airpByDatestats['Type']=='DEP_DEL'], legend='Dep')
    
    pltBotLeft.circle(x = 'Day', y = param, line_color='blue' ,color = 'blue', fill_alpha=1, size=5,
                  source = airpByDatestats.loc[airpByDatestats['Type']=='ARR_DEL'], legend='Arr')
                                                
    #pltBotLeft.legend.location = (0, 200)
    pltBotLeft.legend.orientation = "horizontal"
    
    #######################################################################
    maxDepDur = max(airpByDatestats.loc[(airpByDatestats['Type']=='DEP_DEL'), 'mean'])
    maxDepDay = airpByDatestats.loc[(airpByDatestats['Type']=='DEP_DEL') & (airpByDatestats['mean'] == maxDepDur), 'Day'].iloc[0,]
    maxArrDur = max(airpByDatestats.loc[(airpByDatestats['Type']=='ARR_DEL'), 'mean'])
    maxArrDay = airpByDatestats.loc[(airpByDatestats['Type']=='ARR_DEL') & (airpByDatestats['mean'] == maxArrDur), 'Day'].iloc[0,]
    
    minDepDel = min(airpByDate.loc[(airpByDate['Type']=='DEP_DEL') & (airpByDate['Day']==maxDepDay), 'DURATION'])
    maxDepDel = max(airpByDate.loc[(airpByDate['Type']=='DEP_DEL') & (airpByDate['Day']==maxDepDay), 'DURATION'])
    histDepDel, edgesDepDel = Numpy.histogram(airpByDate.loc[(airpByDate['Type']=='DEP_DEL') & 
                                                               (airpByDate['Day']==maxDepDay), 'DURATION'], 
                                  density=True, bins=Numpy.arange(minDepDel, maxDepDel, binW))
    
    minArrDel = min(airpByDate.loc[(airpByDate['Type']=='ARR_DEL') & (airpByDate['Day']==maxArrDay), 'DURATION'])
    maxArrDel = max(airpByDate.loc[(airpByDate['Type']=='ARR_DEL') & (airpByDate['Day']==maxArrDay), 'DURATION'])
    histArrDel, edgesArrDel = Numpy.histogram(airpByDate.loc[(airpByDate['Type']=='ARR_DEL') & 
                                                               (airpByDate['Day']==maxArrDay), 'DURATION'], 
                                  density=True, bins=Numpy.arange(minArrDel, maxArrDel, binW))
    
    xmin = min(airpByDate.loc[(airpByDate['Type']=='DEP_DEL') & (airpByDate['Day']==maxDepDay), 'DURATION'].quantile(0.05),
                              airpByDate.loc[(airpByDate['Type']=='ARR_DEL') & (airpByDate['Day']==maxArrDay), 'DURATION'].quantile(0.05))
    xmax = max(airpByDate.loc[(airpByDate['Type']=='DEP_DEL') & (airpByDate['Day']==maxDepDay), 'DURATION'].quantile(0.95),
                              airpByDate.loc[(airpByDate['Type']=='ARR_DEL') & (airpByDate['Day']==maxArrDay), 'DURATION'].quantile(0.95))

    pltBotRight = BokehPlotting.figure(x_range = (xmin, xmax),
                                 title='Delays on worst day', 
                                 x_axis_label='Duration (mins)', 
                                 y_axis_label='Fraction of occurences',
                                 plot_width=400, plot_height=300,
                                 tools = TOOLS 
                                 #tooltips = [('Day', '@x'),
                                             #(f'{param}', '@y')
                                             #]    
                                 )
    
    pltBotRight.quad(top=histDepDel, bottom=0, left=edgesDepDel[:-1], right=edgesDepDel[1:],
              fill_color="red", line_color="white", alpha=0.5, legend='Dep')
    
    pltBotRight.quad(top=histArrDel, bottom=0, left=edgesArrDel[:-1], right=edgesArrDel[1:],
          fill_color="blue", line_color="white", alpha=0.5, legend='Arr')
    
                                              
    #pltBotRight.legend.location = (0, 200)
    pltBotRight.legend.orientation = "horizontal"
    
    #######################################################################
    
    plt = BokehLayouts.row(BokehLayouts.column(style(pltTopLeft), style(pltBotLeft)),
                           BokehLayouts.column(style(pltTopRight), style(pltBotRight)))
                           
    
    #BokehIO.save(plt)

    return plt

#######################################################################
# call the plots
#######################################################################
airpInp = BokehWidgets.Select(title="Select Airport city", value=airport, options=airportList)
airlInp = BokehWidgets.Select(title="Select Airline", value=airline, options=airlineList)
wetInp = BokehWidgets.Select(title='Select Weather Param', value='TEMP', options=weatherParams)
binWid = BokehWidgets.Slider(title="Select Bin Width (mins)", value=5, start=1, end=30, step=1)

plt_month = make_plot_delay(flightDur)
plt_Weather = make_plot_Weather(flightDur)
#table_CatMM = make_table(allData)

def update_all(attribute, old, new):
    pltLayout.children[1] = make_plot_delay(flightDur)
    pltLayout.children[3] = make_plot_Weather(flightDur)
    #pltLayout.children[5] = make_table (allData)
     
for wid in [airpInp, airlInp, wetInp, binWid]:
    wid.on_change('value', update_all)
    
pltLayout = BokehLayouts.column(BokehLayouts.row(BokehLayouts.widgetbox(airpInp), 
                                                 BokehLayouts.widgetbox(airlInp),
                                                 BokehLayouts.widgetbox(binWid)),
                                plt_month,
                                BokehLayouts.widgetbox(wetInp), 
                                plt_Weather, 
                                #BokehLayouts.widgetbox(dayInp), 
                                #table_CatMM, 
                                width=900)
    
BokehIO.curdoc().add_root(pltLayout)
BokehIO.curdoc().title = f'Flight_onTime'