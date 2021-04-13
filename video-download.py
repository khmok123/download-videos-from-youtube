import re
from pytube import Playlist
from pytube import YouTube
import os
from moviepy.editor import *
import glob
import shutil
from pathlib import Path

raw_files_dir = r'.\videos\raw_files'
edited_files_dir = r'.\videos\edited_files'
video_list_file = 'video-list.txt'

if not os.path.exists(edited_files_dir):
    Path("edited_files_dir").mkdir(parents=True, exist_ok=True)

if not os.path.exists(raw_files_dir):
    Path("raw_files_dir").mkdir(parents=True, exist_ok=True)


def get_sec(time_str):
    if time_str.count(':') == 1:
        m, s = time_str.split(':')
        return int(m) * 60 + float(s)
    elif time_str.count(':') == 2:
        h, m, s = time_str.split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)

def get_sec_range(time_str_range):
    time_strs = time_str_range.split('-')
    return [get_sec(time_str) for time_str in time_strs]

def get_multiple_sec_ranges(multiple_time_str_ranges):
    time_str_ranges = multiple_time_str_ranges.split(',')
    return [get_sec_range(time_str_range.strip()) for time_str_range in time_str_ranges]

def get_type(video):
    match = re.search(r'mime_type=".*?"', str(video)).group(0).split('/')[1]
    return '.'+match.strip('\"')

def find_max_res_video(videos):
    matches = []
    for idx,video in enumerate(videos):
        match = re.search(r'res="[0-9]+p"', str(video))
        if match:
            matches.append((idx, int(match.group(0).split('=')[1].strip('\"').strip('p'))))
    unzipped = list(zip(*matches))
    max_res = max(unzipped[1])
    for idx,idx2 in enumerate(unzipped[0]):
        if unzipped[1][idx] == max_res:
            return videos[unzipped[0][idx]]    
        
def get_download_data(file_name = video_list_file):

    with open(file_name,'r', encoding='utf-8') as f:
        names = []
        urls = []
        times = []
        for idx,line in enumerate(f.readlines()):
            if idx % 4 == 0:
                names.append(line.strip())
            if idx % 4 == 1:
                urls.append(line.strip())
            if idx % 4 == 2:
                times.append(get_multiple_sec_ranges(line.strip()))

    download_data = list(zip(names, urls, times))
    return download_data

def download_videos(need_audio=True):

    download_data = get_download_data(file_name = video_list_file)

    for download in download_data:

        name, url, time_ranges = download
        output_filename = os.path.join(edited_files_dir, name+'.mp4')

        yt = YouTube(url)
        videos = yt.streams
        video = find_max_res_video(videos)
        video.download(raw_files_dir)
        extension = get_type(video)

        list_of_files = glob.glob(os.path.join(raw_files_dir,"*"))
        file_dir = max(list_of_files, key=os.path.getctime)
        
        if need_audio:
            if video not in videos.filter(progressive=True):
                tmp_dir = os.path.join(raw_files_dir, 'audio_tmp')
                os.mkdir(os.path.join(tmp_dir))
                audio = yt.streams.filter(mime_type="audio/mp4")[0]
                audio.download(tmp_dir)
                list_of_files_audio = glob.glob(os.path.join(tmp_dir,"*"))
                audio_dir = max(list_of_files_audio, key=os.path.getctime)
                original_video = VideoFileClip(file_dir)
                original_video.audio = AudioFileClip(audio_dir)
                original_video.write_videofile(os.path.join(raw_files_dir,'tmp.mp4'))
                os.remove(file_dir)
                os.rename(os.path.join(raw_files_dir,'tmp.mp4'),file_dir)
        try:
            shutil.rmtree(tmp_dir)
        except:
            pass
        
        clip = VideoFileClip(file_dir)
        clips = []

        for sec_range in time_ranges:
            clips.append(clip.subclip(sec_range[0],sec_range[1]))

        concat_clip = concatenate_videoclips(clips)
        

        
        concat_clip.write_videofile(output_filename)
        concat_clip.close()

need_audio_str = input("Need audio? (y/n)")
need_audio_bool = bool(need_audio_str)

if __name__ == '__main__':
    download_videos(need_audio = need_audio_bool)