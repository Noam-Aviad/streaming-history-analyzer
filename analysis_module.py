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

def files_to_dataframe(convert_to_datetime = True, sort_by = None) -> pd.DataFrame:
    """Uses read_files to read the JSON files and return a dataframe"""
    df = pd.json_normalize(read_files())
    if sort_by == 'ts' or convert_to_datetime:
        df['ts'] = pd.to_datetime(df['ts'], format="%Y-%m-%dT%H:%M:%SZ")
    if sort_by:
        df = df.sort_values(sort_by)
    return df

def tracks_in_daterange(df = None, from_date=None, to_date=None) -> pd.DataFrame:
    """Returns a dataframe of tracks from a specified date range"""
    if type(df)==type(None):
        df = files_to_dataframe()
    if from_date==None:
        from_date = df['ts'].min()
    if to_date==None:
        to_date = df['ts'].max()
    mask = (df['ts'] >= from_date) & (df['ts'] <= to_date)
    return df.loc[mask]

def track_count_per(time_interval = dt.timedelta(weeks=1), from_date = None, to_date = None, df=None) -> pd.DataFrame:
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

def listening_time_per(df=None, time_interval = dt.timedelta(weeks=1), from_date = None, to_date = None, include_skipped=False, consider_complete_after=dt.timedelta(minutes=1)) -> pd.DataFrame:
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

def get_skipped(df = None, consider_complete_after = dt.timedelta(minutes=1)) -> pd.DataFrame:
    if type(df)==type(None):
        df = files_to_dataframe()
    mask = (df['ms_played']) / 1000 < consider_complete_after.total_seconds()
    return df.loc[mask]

def get_not_skipped(df = None, consider_complete_after = dt.timedelta(minutes=1)) -> pd.DataFrame:
    if type(df)==type(None):
        df = files_to_dataframe()
    mask = (df['ms_played']) / 1000 >= consider_complete_after.total_seconds()
    return df.loc[mask]

def get_tracks(df=None, song_title=None, artist=None, album=None, include_skipped=True, consider_complete_after=dt.timedelta(minutes=1), from_date=None, to_date=None) -> pd.DataFrame:
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

def count_tracks(df=None, song_title=None, artist=None, album=None, include_skipped=True, consider_complete_after=dt.timedelta(minutes=1), from_date=None, to_date=None) -> int:
    return len(get_tracks(df=df, song_title=song_title, artist=artist, album=album, include_skipped=include_skipped, consider_complete_after=consider_complete_after))

def get_listening_time(df=None, song_title=None, artist=None, album=None, include_skipped=True, consider_complete_after=dt.timedelta(minutes=1), from_date=None, to_date=None):
    tracks = get_tracks(df=df,
                        song_title=song_title,
                        artist=artist, album=album,
                        include_skipped=include_skipped,
                        consider_complete_after=consider_complete_after,
                        from_date=from_date,
                        to_date=to_date)
    return pd.to_timedelta(tracks['ms_played'].sum(), unit='ms')

def most_played_by_time(lim = 10, thing = 'song', df=None, artist=None, album=None, from_date=None, to_date=None):
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
    return df.nlargest(min(lim, len(df)), columns = ['ms_played'])

def most_played_by_count(lim = 10, thing = 'song', df=None, artist=None, album=None, from_date=None, to_date=None, include_skipped=False, consider_complete_after=dt.timedelta(minutes=1)):
    if type(df) == type(None):
        df = tracks_in_daterange(df=df, from_date=from_date, to_date=to_date)
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
    return df.nlargest(min(lim, len(df)), columns=['count'])

def most_popular_bar_chart(by = 't', lim=10, thing = 'song', df=None, artist=None, album=None, from_date=None, to_date=None, include_skipped=False, consider_complete_after=dt.timedelta(minutes=1), orientation='h'):
    if by=='t':
        most_popular = most_played_by_time(lim=lim,
                                           thing=thing,
                                           df=df,
                                           artist=artist,
                                           album=album,
                                           from_date=from_date,
                                           to_date=to_date)
        y = most_popular['ms_played']/pd.Timedelta(hours=1)
    elif by=='c':
        most_popular = most_played_by_count(lim=lim,
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

def get_popularity_per(by='t', song_title=None, artist=None, album=None, df=None, time_interval = dt.timedelta(7), include_skipped=False, consider_complete_after=dt.timedelta(minutes=1), from_date=None, to_date=None):
    df = get_tracks(df=df, song_title=song_title, artist=artist, album=album, from_date=from_date, to_date=to_date, include_skipped=include_skipped, consider_complete_after=consider_complete_after)
    if by=='t':
        return listening_time_per(df=df, time_interval=time_interval, include_skipped=include_skipped, consider_complete_after=consider_complete_after, from_date=from_date, to_date=to_date)
    elif by=='c':
        return track_count_per(df=df, time_interval=time_interval, from_date=from_date, to_date=to_date)

def get_devices_percentage(df = None, by='t', include_skipped=False, consider_complete_after=dt.timedelta(minutes=1), from_date=None, to_date=None):
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


    return  (df['platform'].str.contains('Android'))
    df = df.groupby(['platform'])
    if by=='c':
        df = df.size()
    return  (df.str.contains('Android'))

def usage_chart(df=None, time_interval = dt.timedelta(7), by='t', include_skipped=False, consider_complete_after=dt.timedelta(minutes=1), from_date=None, to_date=None):
    if by=='t':
        df = listening_time_per(df=df, time_interval=time_interval, from_date=from_date, to_date=to_date, include_skipped=include_skipped, consider_complete_after=consider_complete_after)
        plt.plot(df['Date'], df['Time Played']/pd.Timedelta(hours=1))
    elif by=='c':
        df = track_count_per(time_interval=time_interval, from_date=from_date, to_date=to_date, df =df)
        plt.plot(df['Date'], df['Tracks Count'])
    plt.show()

def plot_popularity_per(by='t', song_title=None, artist=None, album=None, df=None, time_interval = dt.timedelta(7), include_skipped=False, consider_complete_after=dt.timedelta(minutes=1), from_date=None, to_date=None):
    df = get_popularity_per(by=by, song_title=song_title, artist=artist, album=album, df=df, time_interval = time_interval, include_skipped=include_skipped, consider_complete_after=consider_complete_after, from_date=from_date, to_date=to_date)
    if by=='t':
        plt.plot(df['Date'], df['Time Played']/pd.Timedelta(hours=1))
    elif by=='c':
        plt.plot(df['Date'], df['Tracks Count'])
    plt.show()

def devices_pie_chart(df = None, by='t', include_skipped=False, consider_complete_after=dt.timedelta(minutes=1), from_date=None, to_date=None):
    perc_dict = get_devices_percentage(df=df, by=by, include_skipped=include_skipped, consider_complete_after=consider_complete_after, from_date=from_date, to_date=to_date)
    plt.pie(perc_dict.values(), labels=perc_dict.keys(), autopct='%1.0f%%')
    plt.show()
