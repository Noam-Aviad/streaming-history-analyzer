## Spotify Listening History Analyzer

This module uses pandas and matplotlib to provide tools for analyzing your Spotify listening history and plot charts of your listening time, favorite songs, artists and albums, your usage of different devices etc.

To use it you need to download your extended streaming history (go to Account->Privacy Settings->Download your data, the request could take a while), and place the JSON files in the same folder as the module.

### Examples:

#### Plotting your Spotify usage history

You can specify a date range for the chart (default is all available data), choose to measure your usage by time (default) or by tracks count (in which case you can choose to ignore skipped songs)

````
usage_chart()
````

Output:

![Usage Chart](https://user-images.githubusercontent.com/76182061/201750242-8255c428-ffc0-4a9c-90b1-0f195437d67d.png)

