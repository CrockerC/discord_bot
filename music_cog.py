import discord
from discord.ext import commands
from youtube_dl import YoutubeDL
from requests import get
from misc import dlog, str_to_nums
from noise_normal import noise_normal

# todo, i wanna make a volume normalizer
# todo, so loud videos are made quieter and quiet videos are made louder
# todo, it'll have to keep a file with the url and the volume
# todo, YAY SQL
# todo, it'll search for the thing in the file and if it is not found it'll spin off a thread to do it while it plays

# todo, add voting

# todo, move youtube search into its own class
# todo, will be good for when i add noise normalization

# todo, sometimes i a "HTTP error 403 Forbidden" error when trying to stream, need to detect it and try again


class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.noise_normal = noise_normal()

        self.is_playing = False
        self.is_paused = False

        self.music_queue = []
        self.music_queue_backup = []  # for if you clear the queue but regret it
        self.YDL_OPTIONS = {"format": "bestaudio", "noplaylist": True}  # no playlist support for now
        self.FFMPEG_OPTIONS = {"before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", "options": "-vn"}

        self.vc = None

    async def search_yt(self, item, playlist=False):
        if playlist:
            self.YDL_OPTIONS["noplaylist"] = False
        else:
            self.YDL_OPTIONS["noplaylist"] = True
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                get(item)
            except:
                # results = YoutubeSearch(arg, max_results=10).to_dict()
                info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]
            else:
                info = ydl.extract_info(item, download=False)

        volume = await self.noise_normal.get_noise_normal(info['webpage_url'])
        return {'source': info['formats'][0]['url'], 'title': info['title'], 'web_url': info['webpage_url'], 'volume': volume}

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
            if index + 1 >= max_size:
                title = "... and {} more".format(len(self.music_queue) - max_size)
                message.append(title)
                break

        if len(message) == 0:
            message = ["Nothing in queue"]

        return '\n'.join(message)

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']
            volume = self.music_queue[0][0]['volume']
            self.music_queue.pop(0)
            self.vc.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), volume=volume), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            if self.vc is None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()

                if self.vc is None:
                    await ctx.send("Could not connect to the voice channel")
                    return
            else:
                # if the user is not in the bot's channel, move to it
                await self.vc.move_to(self.music_queue[0][1])

            self.is_playing = True
            m_url = self.music_queue[0][0]['source']
            volume = self.music_queue[0][0]['volume']
            self.music_queue.pop(0)
            self.vc.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), volume=volume), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    @commands.command(name='play', help="Play the song from youtube")
    async def play(self, ctx, *args):
        query = " ".join(args)
        dlog("[command] [{}] play".format(ctx.author))

        # get current user's channel
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:  # todo, if the bot is already in a channel, just play it there, but only if its in the same server
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
            else:
                await ctx.send("Added {} to queue\n".format(song['web_url']))
                self.music_queue.append([song, voice_channel])
                print(self.get_queue_list(100))

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
            await self.play_music(ctx)

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
                if len(self.music_queue) > i:
                    del self.music_queue[i-1]
                else:
                    dlog("Can't remove #{} from queue of length {}".format(i, len(self.music_queue)))

            await ctx.send("Removing \"{}\" from the queue!".format(query))
            return

        song = self.search_yt(query)
        for index, queued_song in enumerate(self.music_queue):
            if song['title'] == self.music_queue[index][0]['title']:
                del self.music_queue[index]
                await ctx.send("Removing \"{}\" from the queue!".format(song['title']))
                return

        await ctx.send("Could not find \"{}\" in the queue!".format(song['title']))
