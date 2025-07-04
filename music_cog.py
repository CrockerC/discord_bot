import discord
from discord.ext import commands
#from youtube_dl import YoutubeDL
from yt_dlp import YoutubeDL
from requests import get
from misc import dlog, str_to_nums
from noise_normal import noise_normal

# todo, add voting

# todo, add ability to move song to the top of queue, also put one at the top
# todo, add ability to restart song


class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.noise_normal = noise_normal()

        self.is_playing = False
        self.is_paused = False

        self.music_queue = []
        self.current_song = None
        self.music_queue_backup = []  # for if you clear the queue but regret it
        self.YDL_OPTIONS = {"format": "bestaudio", "noplaylist": True}  # no playlist support for now
        self.FFMPEG_OPTIONS = {"before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", "options": "-vn"}

        self.vc = None

    async def search_yt(self, item, playlist=False):
        if playlist:
            self.YDL_OPTIONS["noplaylist"] = False  # this doesnt seem to work
        else:
            self.YDL_OPTIONS["noplaylist"] = True
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            ydl.cache.remove()
            try:
                get(item)
            except:
                # results = YoutubeSearch(arg, max_results=10).to_dict()
                info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]
            else:
                info = ydl.extract_info(item, download=False)

        if 'entries' in info.keys():
            songs = []
            for entry in info['entries']:
                volume = await self.noise_normal.get_noise_normal(entry['webpage_url'])
                source = None
                for item in entry['formats']:
                    if 'audio only' in item['format'] and source is None:
                        source = item['url']
                    elif 'audio only' in item['format'] and source is not None:
                        if 'high' in item['format']:
                            source = item['url']
                if source is not None:
                    dict = {'source': source, 'title': entry['title'], 'web_url': entry['webpage_url'], 'volume': volume}
                    songs.append(dict)
            return songs

        else:
            volume = await self.noise_normal.get_noise_normal(info['webpage_url'])
            source = None
            for item in info['formats']:
                if 'audio only' in item['format'] and source is None:
                    source = item['url']
                elif 'audio only' in item['format'] and source is not None:
                    if 'high' in item['format']:
                        source = item['url']
            return {'source': source, 'title': info['title'], 'web_url': info['webpage_url'], 'volume': volume}

    def get_queue_list(self, max_size=10, url=False):
        message = []
        for index, song in enumerate(self.music_queue):
            title = song[0]['title']
            if url is True:
                # warning, this can cause huge messages to be shown
                title = str(index + 1) + ". " + title + ": " + song[0]['web_url']
            else:
                title = str(index + 1) + ". " + title
            message.append(title)
            if index + 1 > max_size:
                title = "... and {} more".format(len(self.music_queue) - max_size)
                message.append(title)
                break

        if len(message) == 0:
            message = ["Nothing in queue"]

        return '\n'.join(message)

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            self.current_song = self.music_queue.pop(0)
            m_url = self.current_song[0]['source']
            volume = self.current_song[0]['volume']
            self.vc.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), volume=volume), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            if self.vc is None or not self.vc.is_connected():
                print("connecting")
                self.vc = await self.music_queue[0][1].connect()
                print("connected")

                if self.vc is None:
                    await ctx.send("Could not connect to the voice channel")
                    return
            else:
                # if the user is not in the bot's channel, move to it
                await self.vc.move_to(self.music_queue[0][1])

            self.is_playing = True
            self.current_song = self.music_queue.pop(0)
            m_url = self.current_song[0]['source']
            volume = self.current_song[0]['volume']
            self.vc.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), volume=volume), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    @commands.command(name='play', help="Play the song from youtube")
    async def play(self, ctx, *args):
        query = " ".join(args)
        dlog("[command] [{}] play".format(ctx.author))

        # get current user's channel
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await ctx.send("Please connnect to a voice channel!")
        elif self.is_paused and query == "":
            self.vc.resume()
            self.is_playing = True
            self.is_paused = False
        elif query != "":
            song = await self.search_yt(query)
            # shows true if it fails?
            if type(song) is type(True):
                await ctx.send("Could not add {} to queue\n".format(song['web_url']))
            elif type(song) is list:
                await ctx.send("Use \"[playlist\" command to play playlists")
                return
            else:
                await ctx.send("Added {} to queue\n".format(song['web_url']))
                self.music_queue.append([song, voice_channel])

                if self.is_playing is False and self.is_paused is False:
                    await self.play_music(ctx)
        elif len(self.music_queue) != 0:
            await self.play_music(ctx)
        else:
            await ctx.send("Nothing to play")

    @commands.command(name="pause", help="Pauses current song")
    async def pause(self, ctx, *args):
        dlog("[command] [{}] pause".format(ctx.author))
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()
        elif self.is_paused:
            await ctx.send("Already paused!")

    @commands.command(name="resume", help="Resumes playing song")
    async def resume(self, ctx, *args):
        dlog("[command] [{}] resume".format(ctx.author))
        if self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()
        elif self.is_playing is False and len(self.music_queue) > 0:
            await self.play_music(ctx)

    @commands.command(name="skip", help="Skips current song")
    async def skip(self, ctx, *args):
        dlog("[command] [{}] skip".format(ctx.author))
        if self.vc is not None and self.vc:
            # doing this just stops the song and starts the next one in the queue
            self.vc.stop()

    @commands.command(name="queue", help="Displays all the songs in the queue")
    async def queue(self, ctx, *args):
        query = " ".join(args)
        dlog("[command] [{}] queue, args=\"{}\"".format(ctx.author, query))
        num_to_print = 10
        print_url = False

        # parse args
        if len(args) > 0:
            for arg in args:
                arg = arg.lower()
                try:
                    num_to_print = int(arg)
                except ValueError:
                    if arg in ['false']:
                        print_url = False
                    elif arg in ['true']:
                        print_url = True

        await ctx.send(self.get_queue_list(num_to_print, print_url))

    @commands.command(name="clear", help="Stops the current song and clears the queue")
    async def clear(self, ctx, *args):
        dlog("[command] [{}] clear".format(ctx.author))
        self.music_queue_backup = self.music_queue
        self.music_queue = []
        await ctx.send("{} songs cleared! Use \"[restore\" to undo".format(len(self.music_queue_backup)))

    @commands.command(name="leave", aliases=["disconnect", "exit", "quit"], help="Kick the bot from the voice channel")
    async def leave(self, ctx, *args):
        dlog("[command] [{}] leave".format(ctx.author))
        self.is_playing = False
        self.is_paused = False
        await self.vc.disconnect()

    @commands.command(name="restore", help="Restore the cleared queue from the backup")
    async def restore_queue(self, ctx, *args):
        dlog("[command] [{}] restore".format(ctx.author))
        self.music_queue.extend(self.music_queue_backup)
        await ctx.send("{} songs restored!".format(len(self.music_queue_backup)))
        self.music_queue_backup = []

    @commands.command(name="stop", help="stops the current song and clears the queue")
    async def stop(self, ctx, *args):
        self.music_queue_backup = self.music_queue
        self.music_queue = []
        if self.vc is not None and (self.is_playing or self.is_paused):
            self.vc.stop()
        await ctx.send("{} songs cleared! Use \"[restore\" to undo".format(len(self.music_queue_backup)))

    @commands.command(name="remove", help="stops the current song and clears the queue")
    async def remove(self, ctx, *args):
        query = " ".join(args)

        # check for numbers separated by a comma
        res = str_to_nums(query)
        if res is not False:
            for i in res:
                if len(self.music_queue) >= i:
                    del self.music_queue[i-1]
                else:
                    dlog("Can't remove #{} from queue of length {}".format(i, len(self.music_queue)))

            await ctx.send("Removing \"{}\" from the queue!".format(query))
            return

        song = await self.search_yt(query)
        for index, queued_song in enumerate(self.music_queue):
            if song['title'] == queued_song[0]['title']:
                del self.music_queue[index]
                await ctx.send("Removing \"{}\" from the queue!".format(song['title']))
                return

        await ctx.send("Could not find \"{}\" in the queue!".format(song['title']))

    @commands.command(name="playlist", help="lets you link a playlist for queueing")
    async def playlist(self, ctx, *args):
        query = " ".join(args)
        dlog("[command] [{}] play".format(ctx.author))

        # get current user's channel
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await ctx.send("Please connnect to a voice channel!")
        elif query != "":
            songs = await self.search_yt(query, True)
            # shows true if it fails?
            if type(songs) is type(True):
                await ctx.send("Could not add {} to queue\n".format(query))
            else:
                await ctx.send("Added playlist {} to queue\n".format(query))
                for song in songs:
                    self.music_queue.append([song, voice_channel])

                if self.is_playing is False and self.is_paused is False:
                    await self.play_music(ctx)
        elif len(self.music_queue) != 0:
            await self.play_music(ctx)
        else:
            await ctx.send("Nothing to play")

    @commands.command(name="restart", help="restarts current song")
    async def restart(self, ctx, *args):
        if self.is_playing:
            self.music_queue = [self.current_song] + self.music_queue
            self.vc.stop()