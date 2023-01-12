from yt_dlp import YoutubeDL
from misc import dlog, str_to_nums
import numpy as np
import audio2numpy as a2n
import os
import asyncio

# https://stackoverflow.com/questions/66388690/music-bot-volume-only-goes-down-but-not-up


class noise_normal:
    def __init__(self, baseline=.3):
        self.baseline = baseline
        self.file_name = 'temp_file.mp3'
        self.url = None # only for logging purposes
        self.YDL_OPTIONS = {
            'format': 'worstaudio',  # audio quality does not have to be good
            "outtmpl": self.file_name,
        }

    async def download_yt(self, url):
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

    async def get_volume(self):
        raw_data, sr = a2n.audio_from_file(self.file_name)
        # it takes far too long to calculate amplitude for the whole file
        # doing this then that with a reduced number of samples is much faster
        raw_data = raw_data[np.random.choice(len(raw_data), size=20000, replace=False)]  # 20k seems to be the magic number
        raw_data = raw_data.sum(axis=1) / 2
        raw_data = np.absolute(raw_data)
        volume = np.percentile(raw_data, 90)
        dlog("Video {} volume {:.3f}, adjustment factor {}".format(self.url, volume, self.baseline/volume))
        return volume

    def calculate_factor(self, volume):
        return self.baseline/volume * self.baseline

    async def save_in_db(self, url, volume):
        return False

    async def load_vol_from_db(self, url):
        return False

    # takes url and gives back the volume adjustment
    async def get_noise_normal(self, url):
        volume = await self.load_vol_from_db(url)
        if volume:
            return volume
        # if not found in the db, do procedure
        await self.download_yt(url)
        volume = await self.get_volume()
        volume = self.calculate_factor(volume)
        await self.save_in_db(url, volume)
        return volume


async def _main():
    norm = noise_normal()
    await norm.download_yt("https://www.youtube.com/watch?v=U06jlgpMtQs")
    volume = await norm.get_volume()
    print(norm.calculate_factor(volume))


if __name__ == "__main__":
    newfeature = asyncio.run(_main())

