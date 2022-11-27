import pandas as pd
from matplotlib import pyplot as plt
import json
from os.path import exists as file_exists
import datetime as dt

def read_files() -> list:
    """Reads the JSON files and returns a list of all your data"""
    file_num = 0
    complete_data = []
    while file_exists('endsong_' + str(file_num) + '.json'):
        current_file_data = json.load(open('endsong_' + str(file_num) + '.json', encoding='utf8'))
        complete_data.extend(current_file_data)
        file_num+=1
    return complete_data

def files_to_dataframe(convert_to_datetime : bool = True, sort_by : str = None) -> pd.DataFrame:
    """Uses read_files to read the JSON files and return a dataframe"""
    df = pd.json_normalize(read_files())
    if sort_by == 'ts' or convert_to_datetime:
        df['ts'] = pd.to_datetime(df['ts'], format="%Y-%m-%dT%H:%M:%SZ")
    if sort_by:
        df = df.sort_values(sort_by)
    return df

def tracks_in_daterange(df : pd.DataFrame= None, from_date : dt.datetime = None, to_date:dt.datetime=None) -> pd.DataFrame:
    """Returns a dataframe of tracks from a specified date range"""
    if type(df)==type(None):
        df = files_to_dataframe()
    if from_date==None:
        from_date = df['ts'].min()
    if to_date==None:
        to_date = df['ts'].max()
    mask = (df['ts'] >= from_date) & (df['ts'] <= to_date)
    return df.loc[mask]

def track_count_per(time_interval:dt.timedelta= dt.timedelta(weeks=1), from_date:dt.datetime = None, to_date:dt.datetime = None, df:pd.DataFrame=None) -> pd.DataFrame:
    df = tracks_in_daterange(from_date=from_date, to_date=to_date, df=df)
    if from_date==None:
        from_date = df['ts'].min()
    if to_date==None:
        to_date = df['ts'].max()
    date = from_date
    dates = []
    track_counts = []
    while (to_date - date) >= time_interval:
        dates.append(date)
        track_counts.append(len(tracks_in_daterange(df=df, from_date = date, to_date = date + time_interval)))
        date = date + time_interval
    return pd.DataFrame({'Date' : dates, 'Tracks Count' : track_counts})

def listening_time_per(df:pd.DataFrame=None, time_interval:dt.timedelta = dt.timedelta(weeks=1), from_date:dt.datetime = None, to_date:dt.datetime = None, include_skipped:bool=False, consider_complete_after:dt.timedelta=dt.timedelta(minutes=1)) -> pd.DataFrame:
    if include_skipped:
        df = tracks_in_daterange(from_date=from_date, to_date=to_date, df=df)
    else:
        df = get_not_skipped(df=df, consider_complete_after=consider_complete_after)
    if from_date==None:
        from_date = df['ts'].min()
    if to_date==None:
        to_date = df['ts'].max()
    date = from_date
    dates = []
    listing_times = []
    while (to_date - date) >= time_interval:
        dates.append(date)
        relevant_tracks = tracks_in_daterange(df=df, from_date = date, to_date = date + time_interval)
        listing_times.append(pd.to_timedelta(relevant_tracks['ms_played'].sum(), unit='ms'))
        date = date + time_interval
    return pd.DataFrame({'Date': dates, 'Time Played': listing_times})

def skipped(index, df=None, consider_complete_after = dt.timedelta(minutes=1)) -> bool:
    if type(df)==type(None):
        df = files_to_dataframe()
    skip_val = (df.loc[index]['ms_played'])/1000 < consider_complete_after.total_seconds()
    return skip_val

def get_skipped(df:pd.DataFrame = None, consider_complete_after:dt.timedelta = dt.timedelta(minutes=1)) -> pd.DataFrame:
    if type(df)==type(None):
        df = files_to_dataframe()
    mask = (df['ms_played']) / 1000 < consider_complete_after.total_seconds()
    return df.loc[mask]

def get_not_skipped(df:pd.DataFrame = None, consider_complete_after:dt.timedelta = dt.timedelta(minutes=1)) -> pd.DataFrame:
    if type(df)==type(None):
        df = files_to_dataframe()
    mask = (df['ms_played']) / 1000 >= consider_complete_after.total_seconds()
    return df.loc[mask]

def get_tracks(df:pd.DataFrame=None, song_title:str=None, artist:str=None, album:str=None, include_skipped:bool=True, consider_complete_after:dt.timedelta=dt.timedelta(minutes=1), from_date:dt.datetime=None, to_date:dt.datetime=None) -> pd.DataFrame:
    if type(df)==type(None):
        df = tracks_in_daterange(df=df, from_date=from_date, to_date=to_date)
    if not include_skipped:
        df = get_not_skipped(df=df, consider_complete_after=consider_complete_after)
    if song_title:
        mask = df['master_metadata_track_name']==song_title
        df = df.loc[mask]
    if artist:
        mask = df['master_metadata_album_artist_name'] == artist
        df = df.loc[mask]
    if album:
        mask = df['master_metadata_album_album_name'] == album
        df = df.loc[mask]
    return df

def count_tracks(df:pd.DataFrame=None, song_title:str=None, artist:str=None, album:str=None, include_skipped:bool=True, consider_complete_after:dt.timedelta=dt.timedelta(minutes=1), from_date:dt.datetime=None, to_date:dt.datetime=None) -> int:
    return len(get_tracks(df=df, song_title=song_title, artist=artist, album=album, include_skipped=include_skipped, consider_complete_after=consider_complete_after, from_date=from_date, to_date=to_date))

def get_listening_time(df:pd.DataFrame=None, song_title:str=None, artist:str=None, album:str=None, include_skipped:bool=True, consider_complete_after:dt.timedelta=dt.timedelta(minutes=1), from_date:dt.datetime=None, to_date:dt.datetime=None):
    tracks = get_tracks(df=df,
                        song_title=song_title,
                        artist=artist, album=album,
                        include_skipped=include_skipped,
                        consider_complete_after=consider_complete_after,
                        from_date=from_date,
                        to_date=to_date)
    return pd.to_timedelta(tracks['ms_played'].sum(), unit='ms')

def most_played_by_time(n :int= 10, thing:str = 'song', df:pd.DataFrame=None, artist:str=None, album:str=None, from_date:dt.datetime=None, to_date:dt.datetime=None):
    if type(df) == type(None):
        df = tracks_in_daterange(df=df, from_date=from_date, to_date=to_date)
    if thing == 'song':
        df = df[['master_metadata_track_name', 'master_metadata_album_album_name', 'master_metadata_album_artist_name', 'ms_played']]
        df = df.groupby(['master_metadata_track_name', 'master_metadata_album_artist_name', 'master_metadata_album_album_name']).sum(numeric_only=True)
    elif thing == 'album':
        df = df[['master_metadata_album_album_name', 'master_metadata_album_artist_name', 'ms_played']]
        df = df.groupby(['master_metadata_album_album_name', 'master_metadata_album_artist_name']).sum(numeric_only=True)
    elif thing == 'artist':
        df = df[['master_metadata_album_artist_name', 'ms_played']]
        df = df.groupby(['master_metadata_album_artist_name']).sum(numeric_only=True)
    df = df.reset_index()
    df['ms_played'] = pd.to_timedelta(df['ms_played'], unit='ms')
    return df.nlargest(min(n, len(df)), columns = ['ms_played'])

def most_played_by_count(n :int= 10, thing:str = 'song', df:pd.DataFrame=None, artist:str=None, album:str=None, from_date:dt.datetime=None, to_date:dt.datetime=None, include_skipped:bool=False, consider_complete_after:dt.timedelta=dt.timedelta(minutes=1)):
    if type(df) == type(None):
        df = get_tracks(artist=artist, album=album, from_date=from_date, to_date=to_date, include_skipped=include_skipped, consider_complete_after=consider_complete_after)
    if not include_skipped:
        df = get_not_skipped(df=df, consider_complete_after=consider_complete_after)
    if thing == 'song':
        df = df[['master_metadata_track_name', 'master_metadata_album_album_name', 'master_metadata_album_artist_name']]
        df = (df.groupby(['master_metadata_track_name', 'master_metadata_album_artist_name', 'master_metadata_album_album_name']).size())
    elif thing == 'album':
        df = df[['master_metadata_album_album_name', 'master_metadata_album_artist_name']]
        df = df.groupby(['master_metadata_album_album_name', 'master_metadata_album_artist_name']).size()
    elif thing == 'artist':
        df = df[['master_metadata_album_artist_name']]
        df = df.groupby(['master_metadata_album_artist_name']).size()
    df = df.reset_index()
    df = df.rename(columns = {0:'count'})
    return df.nlargest(min(n, len(df)), columns=['count'])

def most_popular_bar_chart(by :str= 't', n:int=10, thing:str = 'song', df:pd.DataFrame=None, artist:str=None, album:str=None, from_date:dt.datetime=None, to_date:dt.datetime=None, include_skipped:bool=False, consider_complete_after:dt.timedelta=dt.timedelta(minutes=1), orientation:str='h'):
    if by=='t':
        most_popular = most_played_by_time(n=n,
                                           thing=thing,
                                           df=df,
                                           artist=artist,
                                           album=album,
                                           from_date=from_date,
                                           to_date=to_date)
        y = most_popular['ms_played']/pd.Timedelta(hours=1)
    elif by=='c':
        most_popular = most_played_by_count(n=n,
                                           thing=thing,
                                           df=df,
                                           artist=artist,
                                           album=album,
                                           from_date=from_date,
                                           to_date=to_date,
                                            include_skipped=include_skipped,
                                            consider_complete_after=consider_complete_after)
        y = most_popular['count']
    if thing=='song':
        x = most_popular['master_metadata_track_name']+'\n'+most_popular['master_metadata_album_artist_name']
    elif thing=='album':
        x = most_popular['master_metadata_album_album_name'] + '\n' + most_popular['master_metadata_album_artist_name']
    elif thing == 'artist':
        x = most_popular['master_metadata_album_artist_name']
    if orientation=='v':
        plt.bar(x,y)
    elif orientation=='h':
        x = x[::-1]
        y=y[::-1]
        plt.subplots_adjust(left=0.2, bottom=0.1, right=0.9, top=0.9, wspace=0, hspace=0)
        plt.barh(x, y)
    plt.show()

def get_popularity_per(by:str='t', song_title:str=None, artist:str=None, album:str=None, df:pd.DataFrame=None, time_interval:dt.timedelta = dt.timedelta(7), include_skipped:bool=False, consider_complete_after:dt.timedelta=dt.timedelta(minutes=1), from_date:dt.datetime=None, to_date:dt.datetime=None):
    df = get_tracks(df=df, song_title=song_title, artist=artist, album=album, from_date=from_date, to_date=to_date, include_skipped=include_skipped, consider_complete_after=consider_complete_after)
    if by=='t':
        return listening_time_per(df=df, time_interval=time_interval, include_skipped=include_skipped, consider_complete_after=consider_complete_after, from_date=from_date, to_date=to_date)
    elif by=='c':
        return track_count_per(df=df, time_interval=time_interval, from_date=from_date, to_date=to_date)

def get_devices_percentage(df :pd.DataFrame= None, by:str='t', include_skipped:bool=False, consider_complete_after:dt.timedelta=dt.timedelta(minutes=1), from_date:dt.datetime=None, to_date:dt.datetime=None):
    df = get_tracks(df=df, include_skipped=include_skipped, consider_complete_after=consider_complete_after, from_date=from_date, to_date=to_date)
    df['platform'] = df['platform'].str.lower()
    smartphone_keywords = ['android', 'ios', 'iphone', 'galaxy']
    pc_keywords = ['windows', 'linux', 'mac', 'macintosh']
    smartphone_regex = '|'.join(smartphone_keywords)
    pc_regex = '|'.join(pc_keywords)
    smartphone_mask = df['platform'].str.contains(smartphone_regex)
    pc_mask = df['platform'].str.contains(pc_regex)
    smartphone_tracks = df.loc[smartphone_mask]
    pc_tracks = df.loc[pc_mask]
    if by=='c':
        smartphone_percentage = 100*len(smartphone_tracks)/(len(smartphone_tracks)+len(pc_tracks))
        pc_percentage = 100 * len(pc_tracks) / (len(smartphone_tracks) + len(pc_tracks))
    if by=='t':
        smartphone_time = smartphone_tracks['ms_played'].sum()
        pc_time = pc_tracks['ms_played'].sum()
        smartphone_percentage = 100*smartphone_time/(smartphone_time+pc_time)
        pc_percentage = 100*pc_time/(pc_time+smartphone_time)
    return {'Smartphone' : smartphone_percentage, 'PC':pc_percentage}

def usage_chart(df:pd.DataFrame=None, time_interval:dt.timedelta = dt.timedelta(7), by:str='t', include_skipped:bool=False, consider_complete_after:dt.timedelta=dt.timedelta(minutes=1), from_date:dt.datetime=None, to_date:dt.datetime=None):
    if by=='t':
        df = listening_time_per(df=df, time_interval=time_interval, from_date=from_date, to_date=to_date, include_skipped=include_skipped, consider_complete_after=consider_complete_after)
        plt.plot(df['Date'], df['Time Played']/pd.Timedelta(hours=1))
        plt.ylabel('Hours per Week', fontsize=18)
    elif by=='c':
        df = track_count_per(time_interval=time_interval, from_date=from_date, to_date=to_date, df =df)
        plt.plot(df['Date'], df['Tracks Count'])
    plt.show()

def plot_popularity_per(by:str='t', song_title:str=None, artist:str=None, album:str=None, df:pd.DataFrame=None, time_interval:dt.timedelta = dt.timedelta(7), include_skipped:bool=False, consider_complete_after:dt.timedelta=dt.timedelta(minutes=1), from_date:dt.datetime=None, to_date:dt.datetime=None):
    df = get_popularity_per(by=by, song_title=song_title, artist=artist, album=album, df=df, time_interval = time_interval, include_skipped=include_skipped, consider_complete_after=consider_complete_after, from_date=from_date, to_date=to_date)
    if by=='t':
        plt.plot(df['Date'], df['Time Played']/pd.Timedelta(hours=1))
    elif by=='c':
        plt.plot(df['Date'], df['Tracks Count'])
    plt.show()

def devices_pie_chart(df:pd.DataFrame = None, by:str='t', include_skipped:bool=False, consider_complete_after:dt.timedelta=dt.timedelta(minutes=1), from_date:dt.datetime=None, to_date:dt.datetime=None):
    perc_dict = get_devices_percentage(df=df, by=by, include_skipped=include_skipped, consider_complete_after=consider_complete_after, from_date=from_date, to_date=to_date)
    plt.pie(perc_dict.values(), labels=perc_dict.keys(), autopct='%1.0f%%')
    plt.show()

def get_guilty_pleasures(n:int=10, df:pd.DataFrame=None, include_skipped:bool=False, consider_complete_after:dt.timedelta=dt.timedelta(minutes=1), from_date:dt.datetime=None, to_date:dt.datetime=None, by:str='t', thing:str='song'):
    if type(df) == type(None):
        df = get_tracks(include_skipped=include_skipped, from_date=from_date, to_date=to_date, consider_complete_after=consider_complete_after)
    mask = df['incognito_mode'] == True
    df = df[mask]
    if thing == 'song':
        df = (df.groupby(['master_metadata_track_name', 'master_metadata_album_artist_name', 'master_metadata_album_album_name']))
    elif thing == 'album':
        df = df.groupby(['master_metadata_album_album_name', 'master_metadata_album_artist_name'])
    elif thing == 'artist':
        df = df.groupby(['master_metadata_album_artist_name'])
    if by=='t':
        df = df.sum(numeric_only=True)
        df['ms_played'] = pd.to_timedelta(df['ms_played'], unit='ms')
        df = df.reset_index()
        return df.nlargest(min(n, len(df)), columns=['ms_played'])
    elif by=='c':
        df = df.size()
        df = df.reset_index()
        df = df.rename(columns={0: 'count'})
        return df.nlargest(min(n, len(df)), columns=['count'])

def plot_guilty_pleasures(n:int=10, df:pd.DataFrame=None, include_skipped:bool=False, consider_complete_after:dt.timedelta=dt.timedelta(minutes=1), from_date:dt.datetime=None, to_date:dt.datetime=None, by:str='t', thing:str='song'):
    df = get_guilty_pleasures(n=n, df = df, include_skipped=include_skipped, consider_complete_after=consider_complete_after, from_date=from_date, to_date=to_date, by=by, thing=thing)
    if thing=='song':
        x = df['master_metadata_track_name']+'\n'+df['master_metadata_album_artist_name']
    elif thing=='album':
        x = df['master_metadata_album_album_name'] + '\n' + df['master_metadata_album_artist_name']
    elif thing == 'artist':
        x = df['master_metadata_album_artist_name']
    if by == 'c':
        y = df['count']
    elif by == 't':
        y = df['ms_played']/pd.Timedelta(minutes=1)
    x = x[::-1]
    y = y[::-1]
    plt.subplots_adjust(left=0.2, bottom=0.1, right=0.9, top=0.9, wspace=0, hspace=0)
    plt.barh(x,y)
    plt.show()
