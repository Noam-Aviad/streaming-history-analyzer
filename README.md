## Spotify Listening History Analyzer

This module uses pandas and matplotlib to provide tools for analyzing your Spotify listening history and plot charts of your listening time, favorite songs, artists and albums, your usage of different devices etc.

To use it you need to download your extended streaming history (go to Account->Privacy Settings->Download your data, the request could take a while), and place the JSON files in the same folder as the module. Below you'll find an explanation about the input parameters of the included functions and several examples.

### Input parameters:

Input parameters may differ slightly between functions, but most functions accept the following parameters:

````df```` - a dataframe of your streaming history. by default it's set to None and the functions will create a dataframe from your files, but you can change it to a loaded dataframe for efficiency or to use a specific part of your data.

````from_date```` and ````to_date```` - Datetime objects specifying the date range you're interested in. default setting is None so the functions read all avilable data.

````time_interval```` - for functions that use a time series (e.g the ````usage_chart()```` function which id demonstrated below), this is a timedelta object that determines the time intervals.

### Examples:

#### Plotting your Spotify usage history

You can specify a date range for the chart (default is all available data), choose to measure your usage by time (default) or by tracks count (in which case you can choose to ignore skipped songs)

````
usage_chart()
````

Output:

![Usage Chart](https://user-images.githubusercontent.com/76182061/201750242-8255c428-ffc0-4a9c-90b1-0f195437d67d.png)

 


#### Plotting a bar chart of your favorite artists/albums/songs

````
most_popular_bar_chart(thing='album', lim=7, from_date=dt.datetime(2022,6,1))
````

Output:

![MPBC](https://user-images.githubusercontent.com/76182061/201755251-783c2b36-e184-4750-b895-66bf65cd300f.png)



#### Plotting a pie chart of your streaming devices:

````
devices_pie_chart()
````

Output:


![Devices pie chart](https://user-images.githubusercontent.com/76182061/201867800-efcb515c-840b-4435-9893-905551736517.png)
