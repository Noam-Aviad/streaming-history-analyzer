import pandas as pd
from matplotlib import pyplot as plt
import json
from os.path import exists as file_exists
import datetime as dt

def read_files():
    file_num = 0
    complete_data = []
    while file_exists('endsong_' + str(file_num) + '.json'):
        current_file_data = json.load(open('endsong_' + str(file_num) + '.json', encoding='utf8'))
        complete_data.extend(current_file_data)
        file_num+=1
    return complete_data


def files_to_dataframe(to_datetime = True, sort_by = None):
    df = pd.json_normalize(read_files())
    if sort_by == 'ts' or to_datetime:
        df['ts'] = pd.to_datetime(df['ts'], format="%Y-%m-%dT%H:%M:%SZ")
    if sort_by:
        df = df.sort_values(sort_by)
    return df

def tracks_in_daterange(df = [], from_date=None, to_date=None):
    if isinstance(df, list):
        df = files_to_dataframe()
    if from_date==None:
        from_date = df['ts'].min()
    if to_date==None:
        to_date = df['ts'].max()
    mask = (df['ts'] >= from_date) & (df['ts'] <= to_date)
    return df.loc[mask]

def track_count_per(time_interval = dt.timedelta(weeks=1), from_date = None, to_date = None, df=[]):
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

def listening_time_per(time_interval = dt.timedelta(weeks=1), from_date = None, to_date = None):
    df = tracks_in_daterange(from_date=from_date, to_date=to_date)
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


def skipped(index, df=[], consider_complete_after = dt.timedelta(minutes=1)):
    if isinstance(df, list):
        df = files_to_dataframe()
    skip_val = (df.loc[index]['ms_played'])/1000 < consider_complete_after.total_seconds()
    return skip_val


def get_skipped(df = [], consider_complete_after = dt.timedelta(minutes=1)):
    if isinstance(df, list):
        df = files_to_dataframe()
    mask = (df['ms_played']) / 1000 < consider_complete_after.total_seconds()
    return df.loc[mask]

def get_not_skipped(df = [], consider_complete_after = dt.timedelta(minutes=1)):
    if isinstance(df, list):
        df = files_to_dataframe()
    mask = (df['ms_played']) / 1000 >= consider_complete_after.total_seconds()
    return df.loc[mask]

def get_tracks(df=[], song_title=None, artist=None, album=None, include_skipped=True, consider_complete_after=dt.timedelta(minutes=1), from_date=None, to_date=None):
    if isinstance(df, list):
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


def count_tracks(df=[], song_title=None, artist=None, album=None, include_skipped=True, consider_complete_after=dt.timedelta(minutes=1), from_date=None, to_date=None):
    return len(get_tracks(df=df, song_title=song_title, artist=artist, album=album, include_skipped=include_skipped, consider_complete_after=consider_complete_after))

def get_listening_time(df=[], song_title=None, artist=None, album=None, include_skipped=True, consider_complete_after=dt.timedelta(minutes=1), from_date=None, to_date=None):
    tracks = get_tracks(df=[],
                        song_title=song_title,
                        artist=artist, album=album,
                        include_skipped=include_skipped,
                        consider_complete_after=consider_complete_after,
                        from_date=from_date,
                        to_date=to_date)
    return pd.to_timedelta(tracks['ms_played'].sum(), unit='ms')


def most_played_by_time(lim = 10, thing = 'song', df=[], artist=None, album=None, from_date=None, to_date=None):
    if isinstance(df, list):
        df = tracks_in_daterange(df=df, from_date=from_date, to_date=to_date)
    if thing == 'song':
        df['identifier'] = df['master_metadata_track_name'] + ' - ' + df['master_metadata_album_artist_name']
    elif thing == 'album':
        df['identifier'] = df['master_metadata_album_album_name'] + ' - ' + df['master_metadata_album_artist_name']
    elif thing == 'artist':
        df['identifier'] = df['master_metadata_album_artist_name']
    df = df[['identifier','ms_played']]
    df = df.groupby('identifier').sum()
    df = df.sort_values('ms_played', ascending=False)
    df['ms_played'] = pd.to_timedelta(df['ms_played'], unit='ms')
    return df.iloc[0:lim]

def most_played_by_count(lim = 10, thing = 'song', df=[], artist=None, album=None, from_date=None, to_date=None, include_skipped=False, consider_complete_after=dt.timedelta(minutes=1)):
    if isinstance(df, list):
        df = tracks_in_daterange(df=df, from_date=from_date, to_date=to_date)
    if not include_skipped:
        df = get_not_skipped(df=df, consider_complete_after=consider_complete_after)
    if thing == 'song':
        df['identifier'] = df['master_metadata_track_name'] + ' - ' + df['master_metadata_album_artist_name']
    elif thing == 'album':
        df['identifier'] = df['master_metadata_album_album_name'] + ' - ' + df['master_metadata_album_artist_name']
    elif thing == 'artist':
        df['identifier'] = df['master_metadata_album_artist_name']
    df = df.groupby('identifier').size().to_frame('count')
    df = df.sort_values('count', ascending=False)
    return df.iloc[0:lim]

# b=(listening_time_per())
# c = track_count_per()
# b.plot(x = 'Date', y='Time Played', label = 'Listening time')
# c.plot(x = 'Date', y = 'Tracks Count', label = 'Tracks Count')
# plt.show()


print(most_played_by_count())

