import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
from requests import get
from misc import dlog, str_to_nums
import numpy as np
import audio2numpy as a2n
import os


class noise_normal:
    def __init__(self):
        self.file_name = 'temp_file.mp3'
        self.url = None
        self.YDL_OPTIONS = {
            'format': 'worstaudio',  # audio quality does not have to be good
            "outtmpl": self.file_name,
        }

    def download_yt(self, url):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            if (info['duration']/3600) > 3.5:
                dlog("Attempted to download {} but video is of length {:.2f} hours".format(url, info['duration']/3600))
                return False

            if os.path.exists(self.file_name):
                os.remove(self.file_name)

            ydl.download([url])
            self.url = url
            dlog("Downloaded {}, size is {:.2f}MB".format(self.url, os.path.getsize(self.file_name)/(1024*1024)))
            return True

    def get_amplitude(self):
        raw_data, sr = a2n.audio_from_file(self.file_name)
        # it takes far too long to calculate amplitude for the whole file
        # doing this then that with a reduced number of samples is much faster
        raw_data = raw_data[np.random.choice(len(raw_data), size=10000, replace=False)]
        mean_amplitude = sum(np.absolute(raw_data)) / len(raw_data)
        if len(mean_amplitude) > 1:  # for 2 (or more) channel audio
            mean_amplitude = sum(mean_amplitude) / len(mean_amplitude)
        dlog("Video {} mean amplitude {:.3f}".format(self.url, mean_amplitude))
        return mean_amplitude


if __name__ == "__main__":
    norm = noise_normal()
    norm.download_yt("https://www.youtube.com/watch?v=U06jlgpMtQs")
    norm.get_amplitude()

