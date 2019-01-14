### Analysis of flight delays and taxiing times and its relationship to the local weather for Jan 2018
Experiments with combining data from different sources and with interactive plots (using a bokeh-server)

In this script, I am experimenting with combining data from different sources to find correlations between relevant parameters and experimenting with creating interactive plots using Bokeh.  The data and the correponding data sources used in this analysis are

* Flight details are obtained from [On-Time Flight performance database](https://www.transtats.bts.gov/DL_SelectFields.asp?DB_Short_Name=On-Time&Table_ID=236)
* Airline details are obtained from [Carrier Decode Table](https://www.transtats.bts.gov/Tables.asp?DB_ID=595&DB_Name=Aviation%20Support%20Tables&DB_Short_Name=Aviation%20Support%20Tables#)
* Airport information (including precise location) is obtained from [Master Coordinate Table](https://www.transtats.bts.gov/Tables.asp?DB_ID=595&DB_Name=Aviation%20Support%20Tables&DB_Short_Name=Aviation%20Support%20Tables#)
* Daily average weather conditions are obtained from [National Climatic Data Center (NCDC)](ftp://ftp.ncdc.noaa.gov/pub/data/gsod)
* Information (including precise location) about weather stations are obtained  from [Station list](ftp://ftp.ncdc.noaa.gov/pub/data/noaa/isd-history.txt)

All data presented here only correspond to airports within the US for the month of January 2018.  Data for other time periods (month, year) are availabe at the sites mentioned above.  Similar analysis could be applied to those other time periods by downloading the appropriate data sets.  But, that is beyond the scope of this analysis.

I used the process detailed at [binder-examples repo](https://github.com/binder-examples/bokeh) to have a bokeh-server executed from mybinder.  Click here [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/anandvl/Flight_onTime_bokehServer/master?urlpath=/proxy/5006/bokeh-app) to run this app interactively on myBinder

