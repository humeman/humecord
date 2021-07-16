import time
import discord
import json
import youtube_dlc
import math
import concurrent.futures
import os
import asyncio
from aiohttp import TCPConnector, ClientSession

import humecord

from humecord.utils import discordutils, miscutils, exceptions, logger

class VoiceController:
    def __init__(
            self, 
            gid: int,
            settings: dict
        ):
        """
        Constructs a VoiceController object.

        Parameters:
            bot (Bot)
            gid (int) - Guild ID
            settings (dict) - Settings
                loop (bool) - Loop the queue
                shuffle (bool) - Shuffle the queue
                autodisconnect (int [1, 60]) - Auto-disconnect time
                filters (dict) - Filter settings
                speed (float [0.1, 10]) - Playback speed
        """

        # Bot
        global bot
        from humecord import bot

        self.bot = humecord.bot

        # Discord guild
        self.gid = gid
        self.guild = bot.client.get_guild(gid)

        # Settings
        self.loop = settings.get("loop") if "loop" in settings else False
        self.shuffle = settings.get("shuffle") if "shuffle" in settings else False
        self.autodisconnect = settings.get("autodisconnect") if "autodisconnect" in settings else 5

        # Queue
        self.queue = []

        # Playing
        self.playing = None

        # Makes sure we don't double skip a queue object
        # since it'll call the process_queue function
        # regardless of a manual stop or not
        self.processing_skip = False

        # Another skip hack: Because of painful bugs
        # that I'm too lazy to fully diagnose, we'll just
        # forward the send_feedback variable between
        # self.process_queue_next calls
        self.force_send_feedback = False
        
        # Same deal. Round 3
        self.skipping = False

        # Voice client
        self.client = None
        self.channel = None

        # Feedback channel
        self.feedback_channel = None
        self.message_type = "embed"
        self.use_persistent_message = False
        self.persistent_message = None

        # Downloader
        self.downloader = youtube_dlc.YoutubeDL()

        # Filters
        self.filters = {
            "volume": {
                "enabled": False,
                "value": ["volume=%volume%"],
                "settings": {
                    "volume": 1
                }
            },
            "bassboost": {
                "enabled": False,
                "filter": ["bass=g=%gain%:f=110:w=110"],
                "settings": {
                    "gain": 5
                }
            },
            "deepfry": {
                "enabled": False,
                "filter": ["acrusher=.1:1:64:0:log", "equalizer=f=200:width_type=o:width=200:g=5", "crystalizer=10", "dcshift=shift=1"]
            },
            "eq": {
                "enabled": False,
                "filter": ["equalizer=f=125:width_type=h:width=125:g=%bass%", "equalizer=f=2125:width_type=h:width=1875:g=%mid%", "equalizer=f=10000:width_type=h:width=6000:g=%high%"],
                "settings": {
                    "bass": 1,
                    "mid": 1,
                    "high": 1
                }
            },
            "pitch": {
                "enabled": False,
                "filter": ["asetrate=44100*%multiplier%", "aresample=44100", "atempo=%tempo%"],
                "settings": {
                    "multiplier": 1.5,
                    "tempo": 1 / 1.5
                }
            }
        }

        # TODO: Put filters from settings into filters & speed

        # Speed
        self.speed = 1
        self.enable_speed = False

        # Downloader options
        self.dl_opts = {"format": "worstaudio/worst", "title": True, "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]}

    def get_profile(
            self
        ):
        """
        Generates a profile list that can be funneled
        to DiscordUtils.create_embed(raw_profile =)
        that represents this voice client.
        
        Returns:
            profile (list)
        """
        return [f"🔉{self.client.channel.name}", self.client.channel.guild.icon_url]

    async def join(
            self,
            channel: discord.VoiceChannel,
            feedback_channel: discord.TextChannel,
            send_feedback: bool = True,
            send_error_feedback: bool = True
        ):
        """
        Connects to a voice channel.

        Parameters:
            self (botlib.musicutils.VoiceController)
            channel (discord.VoiceChannel)
            feedback_channel (discord.TextChannel)
            send_feedback (bool) - Send feedback on success
            send_error_feedback (bool) - Send feedback on error

        Returns:
            success (bool) - Whether or not the operation was
                successful
            reason (str) - If unsuccessful, the reason why
        """

        # Check permissions
        # Join channel
        # Set internal values
        # Return feedback

        # Need to check channel permissions first. If I can't send messages,
        # I also can't send feedback if I can't join a VC.
        permitted, reason = await AsyncHelpers.verify_feedback_permissions(self.bot, channel.guild, feedback_channel)

        if not permitted:
            return False, reason # Generic error. Since we can't send feedback, let the
                # parent function handle that. Maybe DM the author?

        # Store
        self.feedback_channel = feedback_channel

        # Make sure the voice channel is valid now
        permitted, reason = await AsyncHelpers.verify_channel_permissions(self.bot, channel.guild, channel)

        if not permitted:
            # We can send feedback, if that's requested.
            if send_error_feedback:
                await DiscordUtils.error(self.bot, feedback_channel, title = "Can't join!", description = f"I don't have permission to join the voice channel 🔉{channel.name}!")

            return False, reason

        # Store
        self.channel = channel

        if self.client.is_connected():
            if self.client.channel != channel:
                self.client.disconnect()

        # Join & store discord.VoiceClient object
        try:
            if not self.client.is_connected():
                self.client = channel.connect()

        except: # TODO: Check individual exceptions. Come on, me...
            if send_error_feedback:
                await DiscordUtils.error(self.bot, feedback_channel, title = "Can't join!", description = f"An unexpected error occured while attempting to join 🔉{channel.name}!")

            return False, "An unexpected error occured."

        # Send feedback
        if send_feedback:
            await feedback_channel.send(
                embed = DiscordUtils.create_embed(
                    self.bot,
                    description = f"Joined 🔉{channel.name} and sending feedback to <#{feedback_channel.id}>!",
                    color = "green"
                )
            )

        # Return success & no error message.
        return True, None

    async def add_to_queue(
            self,
            item_type: str,
            item_details: dict,
            send_feedback: bool
        ):
        """
        Adds an item to the queue. Pass an item type as a string
        and its arguments as a dict.

        Parameters:
            self (VoiceController)
            item_type (str)
            item_details (dict)
            send_feedback (bool)

        Item types:
            youtube_video:
                url: (str) - URL
            tts:
                voice: (str) - Voice to use
                content: (str) - Message to play

        Returns:
            success (bool): Whether or not the operation was 
                successful
        """

        # Initialize song object
        song = Song(item_type, item_details, self.bot.config.audio_directory, self)

        # Get its context so we can get details & verify validity
        await song.get_context()

        # Make sure it's valid
        valid, reason = await song.verify_validity()

        if not valid:
            if send_feedback:
                await DiscordUtils.error(self.bot, self.feedback_channel, title = "Invalid video!", description = reason)

            return False

        self.queue.append(song)

        if send_feedback:
            if self.playing == None and len(self.queue) == 1:
                # Nothing is playing and nothing is in the queue.
                # Normally, we would want to put the song into the
                # "playing" slot, but process_queue will do that for 
                # us. This is only here to decide if the add message
                # will say "added to queue" or "now playing".

                embed = DiscordUtils.create_embed(
                        self.bot,
                        title = f"Now playing '{song.video['title']}'",
                        description = song.generate_details(),
                        color = "green",
                        raw_profile = self.get_profile()
                    )

                if song.video['thumbnail']:
                    embed.set_thumbnail(url = song.video['thumbnail'])

                await self.feedback_channel.send(
                    embed = embed
                )

            else:
                # The song is being added to the queue.

                embed = DiscordUtils.create_embed(
                        self.bot,
                        title = f"Added '{song.video['title']}' to 🔉{self.channel.name}'s queue",
                        description = song.generate_details(),
                        color = "green"
                    )

                if song.video['thumbnail']:
                    embed.set_thumbnail(url = song.video['thumbnail'])

                await self.feedback_channel.send(
                    embed = embed
                )

        return True
    
    async def verify_connection(
            self,
            check_playback: bool,
            require_playing: bool,
            send_feedback: bool = False,
            feedback_channel = None
        ):
        """
        Verifies that a bot is connected and/or playing.

        Parameters:
            check_playback (bool) - If True, this will
                make sure the bot is either playing or
                not playing something (based on the next
                parameter)
            require_playing (bool) - If True, something
                must be playing. If False, nothing should
                be playing.
            send_feedback (bool) - Whether or not error
                feedback will be sent
        """

        if not feedback_channel:
            feedback_channel = self.feedback_channel
            
        if not self.client:
            if send_feedback:
                await DiscordUtils.error(self.bot, feedback_channel, title = "Not connected!", description = "In order to use this command, the bot must be connected.")

            raise exceptions.NotConnected

        if not self.feedback_channel:
            if send_feedback:
                await DiscordUtils.error(self.bot, feedback_channel, title = "Not connected!", description = "In order to use this command, the bot must be connected.")
                
            raise exceptions.NoFeedback

        if not self.client.channel:
            if send_feedback:
                await DiscordUtils.error(self.bot, feedback_channel, title = "Not connected!", description = "In order to use this command, the bot must be connected.")
                
            raise exceptions.NotBound

        if not self.client.is_connected():
            if send_feedback:
                await DiscordUtils.error(self.bot, feedback_channel, title = "Not connected!", description = "In order to use this command, the bot must be connected.")
                
            raise exceptions.NotBound

        if check_playback:
            if require_playing != self.client.is_playing():
                if send_feedback:
                    await DiscordUtils.error(self.bot, feedback_channel, title = "Not connected!", description = f"In order to use this command, the bot must {'not' if not require_playing else ''} be playing music.")
                    
                raise exceptions.NoPlaybackMatch

    async def pause(
            self,
            send_feedback: bool,
            feedback_channel = None
        ):

        if not feedback_channel:
            feedback_channel = self.feedback_channel

        # Verify connection
        # Pause
        # Return feedback

        try:
            await self.verify_connection(True, True, send_feedback, feedback_channel) # Check playback & require that something is playing

        except Exception as e:
            return False

        self.client.pause()

        if send_feedback:
            await feedback_channel.send(
                embed = DiscordUtils.create_embed(
                    self.bot,
                    title = f"Paused playback.",
                    raw_profile = self.get_profile()
                )
            )


    async def unpause(
            self,
            send_feedback: bool,
            feedback_channel = None
        ):

        if not feedback_channel:
            feedback_channel = self.feedback_channel

        # Verify connection
        # Pause
        # Return feedback

        try:
            await self.verify_connection(False, False, send_feedback, feedback_channel) # Don't check playback

        except:
            return False

        if not self.client.is_paused():
            if send_feedback:
                await DiscordUtils.error(self.bot, feedback_channel, title = "Not paused!", description = "Playback is not currently paused.")
            
            return

        self.client.resume()

        if send_feedback:
            await feedback_channel.send(
                embed = DiscordUtils.create_embed(
                    self.bot,
                    title = f"Unpaused playback.",
                    raw_profile = self.get_profile()
                )
            )

    async def set_filter(
            self,
            filter_name: str,
            filter_opts: dict,
            auto_refresh: bool,
            send_feedback: bool,
            feedback_channel = None
        ):

        if not feedback_channel:
            feedback_channel = self.feedback_channel

        # Verify connection
        # Pause
        # Return feedback

        try:
            await self.verify_connection(False, False, send_feedback, feedback_channel) # Don't check playback

        except:
            return False

        # Set enabled status
        self.filters[filter_name]["enabled"] = filter_opts["enabled"]
        
        # Set any settings that are specified
        for setting, value in filter_opts["settings"].items():
            self.filters[filter_name]["settings"][setting] = value

        # If the audio stream should be refreshed, do so
        if auto_refresh and self.client.is_playing():
            self.client.source = self.playing.get_opus_obj(self.playing.get_time())

        if send_feedback:
            await feedback_channel.send(
                embed = DiscordUtils.create_embed(
                    self.bot,
                    title = f"Unpaused playback in 🔉{self.client.channel.name}.",
                    raw_profile = self.get_profile()
                )
            )

    async def set_volume(
            self,
            volume: int,
            send_feedback: bool,
            feedback_channel = None,
            auto_refresh: bool = True
        ):

        if not feedback_channel:
            feedback_channel = self.feedback_channel

        try:
            await self.verify_connection(False, False, send_feedback, feedback_channel) # Don't check playback

        except:
            return False

        self.volume = volume

        # If the audio stream should be refreshed, do so
        if auto_refresh and self.client.is_playing():
            self.client.source = self.playing.get_opus_obj(self.playing.get_time())

        if send_feedback:
            await feedback_channel.send(
                embed = DiscordUtils.create_embed(
                    self.bot,
                    title = f"Set volume to {math.trunc(volume * 100)}%.",
                    raw_profile = self.get_profile()
                )
            )

        # Verify connection
        # Make sure volume is between 1 and 200
        # Set volume
        # If something playing:
            # Seek to current time
        # Send feedback

    async def set_speed(
            self,
            speed: int,
            auto_refresh: bool = True,
            send_feedback: bool = False,
            feedback_channel = None
        ):

        if not feedback_channel:
            feedback_channel = self.feedback_channel

        try:
            await self.verify_connection(False, False, send_feedback, feedback_channel) # Don't check playback

        except:
            return False

        self.speed = speed
        self.enable_speed = self.speed != 1

        # If the audio stream should be refreshed, do so
        if auto_refresh and self.client.is_playing():
            self.client.source = self.playing.get_opus_obj(self.playing.get_time())

        if send_feedback:
            await feedback_channel.send(
                embed = DiscordUtils.create_embed(
                    self.bot,
                    title = f"Set speed to {speed}x.",
                    raw_profile = self.get_profile()
                )
            )

        
        
        # Verify connection
        # Make sure speed is between 0.1 and 10
        # Set speed
        # If something playing:
            # Set time tracking
            # Seek to current time
        # Send feedback

    async def leave(
            self,
            send_feedback: bool,
            feedback_channel = None
        ):

        if not feedback_channel:
            feedback_channel = self.feedback_channel

        try:
            await self.verify_connection(False, False, send_feedback, feedback_channel) # Don't check playback

        except:
            return False

        await self.client.disconnect()

        if send_feedback:
            await feedback_channel.send(
                embed = DiscordUtils.create_embed(
                    self.bot,
                    title = f"Disconnected.",
                    raw_profile = self.get_profile()
                )
            )

        # Verify connection
        # Stop playing
        # Leave
        # Send feedback

    async def process_queue_next(
            self,
            disconnect_fail: bool,
            skip_if_playing: bool,
            send_feedback: bool
        ):

        """
        Processes the next item in a guild's queue.

        Parameters:
            self (VoiceController)
            skip_if_playing (bool) - If something's playing, don't
                override it.
            disconnect_fail (bool) - If the client is disconnected
                or another error occurs, just disconnect and clean
                everything up. Will send feedback to
                self.feedback_channel.

        Returns:
            success (bool)
            feedback (str) - Result

        Raises:
            exceptions.VoiceNotConnected: Voice client is 
                not connected.
        """

        """
        if self.processing_skip:
            print("Processing skip")
            return

        self.processing_skip = True
        """

        if skip_if_playing:
            if self.client.is_connected() and self.client.is_playing():
                return True, "Already playing. Skipping."

        if self.playing != None or self.client.is_playing():
            self.skipping = True
            self.playing = None

            self.force_send_feedback = send_feedback

            self.client.stop()

            return

        if len(self.queue) == 0:
            # There is nothing left to play.

            # Make sure we're not looping the queue first
            if self.loop:
                self.queue.append(self.playing)

            else:
                if send_feedback or self.force_send_feedback:
                    await self.feedback_channel.send(
                        embed = DiscordUtils.create_embed(
                            self.bot,
                            title = "Nothing left in the queue!",
                            description = "Stopping playback.",
                            color = "invisible"
                        )
                    )

                self.playing = None

                return True

        if len(self.queue) != 0: # Repeat the if statement, just in case we're looping the queue and we want to
            # re-add the previous song.
            self.processing_skip = True

            self.playing = self.queue[0]

            del self.queue[0]

            if not self.playing.downloaded:
                await self.playing.download()

            self.playing.play()

            if (send_feedback or self.force_send_feedback) and self.skipping:
                await self.feedback_channel.send(
                    embed = DiscordUtils.create_embed(
                        self.bot,
                        title = "Skipped song!",
                        description = f"Now playing:\n{self.playing.generate_details()}",
                        color = "green",
                        raw_profile = self.get_profile()
                    )
                )

        self.processing_skip = False
        self.force_send_feedback = False
        self.skipping = False

    def process_complete(
            self,
            exception
        ):
        """
        Processes the queue. Will delete the playing 
        song and process the next item in the list.

        Parameters:
            self (VoiceController)
            exception (Exception)
        """
        
        # TODO: Read exceptions
        if exception != None:
            self.bot.client.loop.create_task(DiscordUtils.traceback(self.bot, exception, "Music playback"))

        self.playing = None

        self.bot.client.loop.create_task(self.process_queue_next(False, False, False))


class Song:
    """
    Represents an item in the music queue.

    Types:
        youtube_video:
            url: (str) - URL
        youtube_playlist:
            url: (str) - URL
            load: (int) - Number of videos to auto-load
        spotify_playlist:
            url: (str) - URL
            load: (int) - Number of songs to auto-load
        tts:
            voice: (str) - Voice to use
            content: (str) - Message to play
    """

    def __init__(
            self, 
            item_type: str, 
            item_options: dict, 
            directory: str,
            controller: VoiceController
        ):
        """
        Constructs a Song object.

        Parameters:
            item_type (str) - Item type
            item_options (dict) - Item options
            directory (str) - Directory to store songs in
            controller (VoiceController) - VoiceController object

        Types:
            youtube_video:
                url: (str) - URL
            youtube_playlist:
                url: (str) - URL
                load: (int) - Number of videos to auto-load
            spotify_playlist:
                url: (str) - URL
                load: (int) - Number of songs to auto-load
            tts:
                voice: (str) - Voice to use
                content: (str) - Message to play
        """
        self.type = item_type

        if self.type == "youtube_video":
            self.url = item_options["url"]

        elif self.type == "youtube_playlist":
            self.url = item_options["url"]
            self.load = item_options["load"]

        elif self.type == "spotify_playlist":
            self.url = item_options["url"]
            self.load = item_options["load"]

        elif self.tpye == "tts":
            self.voice = item_options["voice"]
            self.content = item_options["content"]

        else:
            raise exceptions.InvalidMusicType

        self.context = None
        self.controller = controller
        self.time_tracking = []
        self.bot = controller.bot
        self.downloaded = False
        self.file = None

    async def verify_validity(
            self
        ):
        """
        Verifies the validity of a song.

        Makes sure it can be downloaded and isn't too
        long.

        Returns:
            valid (bool) - If the song is valid or not
            reason (str) - If invalid, why

        Raises:
            exceptions.NoContext
        """

        if self.context == None:
            raise exceptions.MissingContext

        if self.context["duration"] > self.bot.config.max_duration:
            return False, f"This song is {MiscUtils.cooler_time(self.context['duration'])} long, but the current maximum is {MiscUtils.cooler_time(self.bot.config.max_duration)}."

        return True, None

    async def get_context(
            self
        ):
        """
        Downloads context for the song.

        Raises:
            exceptions.NoContext - The context for this 
                video is missing required data. It is 
                probably invalid.
        """

        # Adapt synchronous to async
        with concurrent.futures.ThreadPoolExecutor(max_workers = 5) as executor:
            future = executor.submit(self.get_context_base)

            while not future.done():
                await asyncio.sleep(0.05)

            self.context = future.result()

            # TODO: Parse exceptions

        if self.context == None:
            raise exceptions.NoContext

        if "duration" not in self.context:
            raise exceptions.NoContext

        # Populate values for easy access
        self.video = {
            "title": str(self.context.get("title")),
            "description": str(self.context.get("description")),
            "thumbnail": str(self.context.get("thumbnail")),
            "date": str(self.context.get("upload_date")) # TODO: Needs to be parsed first
        }

        self.uploader = {
            "name": str(self.context.get("uploader")),
            "subs": self.context.get("subscriber_count"),
            "url": str(self.context.get("channel_url"))
        }

        self.stats = {
            "views": self.context.get("view_count"),
            "likes": self.context.get("like_count"),
            "dislikes": self.context.get("dislike_count")
        }

        return self.context

    def generate_details(
            self,
            current_time: int = 0
        ):
        """
        Generates an embed description containing a video's details.

        Returns:
            description (str)

        Raises:
            exceptions.NoContext
        """

        if not self.context:
            raise exceptions.NoContext

        # Some videos don't populate this. Since we need to do math for
        # these values to matter, we have to make sure it exists first.
        if self.stats["likes"] and self.stats["dislikes"]:
            total = self.stats["likes"] + self.stats["dislikes"]
            like_ratio = f" | {math.trunc((self.stats['likes'] / total) * 100)}%"

        else:
            like_ratio = ""

        linebreak = "\n" # Linebreaks can't be in f-strings for some reason
        bq = f"""{self.get_player_string(current_time)}

        **{self.video['title']}**
        {MiscUtils.friendly_number(self.stats['views'], True)} ▶ | {MiscUtils.friendly_number(self.stats['likes'], True)} 👍 | {MiscUtils.friendly_number(self.stats['dislikes'], True)} 👎{like_ratio}

        {self.uploader['name']} | {MiscUtils.friendly_number(self.uploader['subs'], True)} 👤

        *{self.video['description'][:100].replace(linebreak, ' ').replace('*', '-').strip()}*"""

        # Could easily be a one-liner but I'm trying to stray away
        # from those now. 

        # Strips each line individually, since block strings
        # keep all indentation (and since this function is
        # indented twice, that's not ideal).

        # Doesn't matter on desktop, since Discord filters them
        # out, but mobile renders it incorrectly if this isn't here.
        bq = bq.split("\n")
        new = []
        for line in bq:
            new.append(line.strip())

        return "\n".join(new)

    def generate_oneliner(
            self
        ):
        """
        Generates a one-line description of the song.

        Returns:
            description (str)

        Raises:
            exceptions.NoContext
        """

        if not self.context:
            raise exceptions.NoContext

        return f"`{self.video['title'][:30]}` from `{self.uploader['name'][:20]}` | {MiscUtils.get_duration_timestamp(self.duration)}"

    def get_player_string(
            self,
            play_time: int
        ):
        """
        Generates a player string, denoting video progress.

        Parameters:
            time (int) - Current time in seconds

        Returns:
            player (str)

        Raises:
            exceptions.NoContext
        """

        if not self.context:
            raise exceptions.NoContext

        percentage = play_time / self.duration

        progress = ("·" * math.trunc(percentage * 20)) + "•"

        progress += "-" * (20 - len(progress))

        return f"{MiscUtils.get_duration_timestamp(play_time)} `[ {progress} ]` {MiscUtils.get_duration_timestamp(self.duration)}"


    def get_context_base(
            self
        ):
        """
        PRIVATE: Access this function through:
            await Song.get_context() or
            Song.get_context_synchronous()

        Raises:
            exceptions.MissingContext
        """

        with youtube_dlc.YoutubeDL({**self.controller.dl_opts}) as downloader:
            self.context = self.controller.downloader.extract_info(self.url, download = False)

        if "duration" not in self.context:
            raise exceptions.MissingContext

        self.duration = self.context["duration"]

        return self.context

    def get_context_synchronous(
            self
        ):
        """
        Synchronous adapter to the asynchronous function 
        Song.get_context().
        """

        self.bot.loop.create_task(self.get_context())

    async def download(
            self
        ):
        """
        Downloads the song for playback.
        """

        # Adapt synchronous to async
        with concurrent.futures.ThreadPoolExecutor(max_workers = 5) as executor:
            future = executor.submit(self.download_base)

            while not future.done():
                await asyncio.sleep(0.05)

            details = future.result()

            # TODO: Parse exceptions

    def download_base(
            self
        ):
        """
        PRIVATE: Access this function through:
            await Song.download() or
            Song.download_synchronous()

        Raises:
            exceptions.NoContext
            exceptions.TooLong
            exceptions.DownloadFailed
        """

        if self.context == None:
            raise exceptions.NoContext

        if self.duration > self.controller.bot.config.max_duration:
            raise exceptions.TooLong

        if "id" in self.context:
            self.file = f"{self.controller.bot.config.audio_directory}/{self.context['id']}.mp3"

        else:
            self.file = f"{self.controller.bot.config.audio_directory}/{self.url.split('?')[-1].split('&')[0].replace('/', '-').replace(':', '-')}.mp3"

        if not os.path.exists(self.file):
            with youtube_dlc.YoutubeDL({"outtmpl": self.file, **self.controller.dl_opts}) as downloader:
                downloader.extract_info(self.url, download = True)

        self.downloaded = True

    def download_synchronous(
            self
        ):
        """
        Synchronous adapter to the asynchronous function 
        Song.download().
        """

        self.bot.loop.create_task(DiscordUtils.task_wrapper(self.controller.bot, self.download()))

    def get_opus_obj(
            self,
            play_time: int
        ):
        """
        Returns an Opus audio stream to funnel to Discord
        for playback in a channel.

        Song must be downloaded first.

        Will start at the specified time in seconds.

        Filters should be set in the Song object first.

        Parameters:
            self (Song)
            time (int) - Time from start of audio file
                to begin playing

        Returns:
            discord.FFmpegOpusAudio - New audio stream

        Raises:
            exceptions.NotDownloaded
        """

        if not self.downloaded:
            raise exceptions.NotDownloaded


        af_opts = []
        # Parse options here

        # Iterate over VoiceController.filters
        for filter_name, details in self.controller.filters.items():
            if details["enabled"]:
                # Create a string from a list of options
                opt = ",".join(details["filter"])

                # Iterate over each setting and replace the placeholder
                if "settings" in details:
                    # Replace placholder values
                    for setting_name, value in details["settings"].items():
                        opt = opt.replace(f"%{setting_name}%", str(value))
                
                af_opts.append(opt)

        if self.controller.enable_speed and self.controller.speed != 1:
            af_opts.append(f"atempo={self.controller.speed}")

        af_opts = ",".join(af_opts)

        if af_opts != "":
            af_opts = f"-filter:a '{af_opts}'"

        # Save time tracking.

        # End the old time track (*if we have one yet)
        if len(self.time_tracking) > 0:
            self.time_tracking[-1]["complete"] = True
            self.time_tracking[-1]["end"] = time.time()

        # Start a new time track
        self.time_tracking.append(
            {
                "complete": False,
                "start": time.time(),
                "multiplier": self.controller.speed
            }
        )

        self.source = discord.FFmpegOpusAudio(self.file, before_options = f"-ss {play_time}", options = af_opts)
        return self.source

    def play(
            self,
            play_time: int = 0
        ):
        """
        Starts playing a song. Will overwrite the current
        opus stream (if there is one) of the song's parent
        VoiceController.

        Song must be downloaded first.

        Will start at the specified time in seconds.

        Filters should be set in the Song object first.

        WARNING: Feedback must be sent in an asynchronous
        function. This will not handle that.

        Parameters:
            self (Song)
            time (int) - Time from start of audio file
                to begin playing

        Returns:
            success (bool) - Whether or not the operation
                succeeded

        Raises:
            exceptions.NotDownloaded
        """

        # Set opus stream
        self.get_opus_obj(play_time)

        # Play the opus stream
        self.controller.client.play(self.source, after = lambda e: self.controller.process_complete(e))

        # Set playing song to self
        self.playing = self

        # Remove self from queue
        # Temporarily removed. No point in this. Just process the queue instead.
        #if self in self.controller.queue:
        #    del self.controller.queue[self.controller.queue.index(self)]

        # WARNING: Feedback must be sent in an asynchronous
        # function. This will not handle that.

        # Return success
        return True

    def get_time(
            self
        ):
        """
        Gets the current position in the song file
        in seconds.

        Returns:
            time (int)
        """

        timecount = []
        for timeset in self.time_tracking:
            if timeset["complete"]:
                # Each time dict has a start time (epoch) and an end time (also epoch).
                # They also have a multiplier denoting the playback speed for the
                # time period.

                # So, to calculate the value for complete time periods, we have to
                # subtract the end time from the start time.

                timecount.append((timeset["end"] - timeset["start"]) * timeset["multiplier"])

            else:
                # If the time period isn't complete, the end time is now (since it's
                # still active).

                timecount.append((time.time() - timeset["start"]) * timeset["multiplier"])

        return sum(timecount)

    def cleanup(
            self
        ):
        """
        Removes all downloaded copies of the song.

        Raises:
            exceptions.NotDownloaded
        """
        if not self.downloaded:
            raise exceptions.NotDownloaded

        if os.path.exists(self.file):
            os.remove(self.file)

    def seek(
            self, 
            play_time: int
        ):
        """
        Seeks the song to the requested time.

        WARNING: Feedback must be sent in an asynchronous
        function. This will not handle that.


        Parameters:
            time (int) - Time in seconds

        Returns:
            discord.FFmpegOpusAudio - New audio stream

        Raises:
            exceptions.SongNotPlaying
            exceptions.TimeOutOfBounds
        """

        if self.controller.playing != self:
            raise exceptions.SongNotPlaying

        # Set opus stream
        self.get_opus_obj(play_time)

        # Play the opus stream
        self.controller.client.play(self.source, after = lambda e: self.controller.process_complete(e))

        # WARNING: Feedback must be sent in an asynchronous
        # function. This will not handle that.

        # Return success
        return True

class AsyncHelpers:
    """
    Not intended as an object, just here to help
    organize everything.

    All asynchronous helper functions that aren't
    categorized in a VoiceController. Helps in the
    creation of VoiceControllers. 
    """

    async def verify_connection(
            bot, 
            gid: int, 
            gdb: dict, 
            author: discord.Member, 
            channel: discord.TextChannel,
            connect: bool,
            allow_steal: bool,
            send_feedback: bool,
            error_feedback: bool
        ):

        """
        Verifies that the bot is connected to the channel
        that the user that ran this command is in. If they
        aren't, return an error message or join, depending
        on parameters.

        Parameters:
            bot (Bot)
            gid (int) - Guild's ID
            gdb (dict) - Guild's database
            author (discord.Member) - Member to perform 
                the action on
            channel (discord.TextChannel) - Channel to 
                return feedback to
            connect (bool) - If True, this will connect
                to a channel (if they're in one)
            allow_steal (bool) - Allow the bot to be
                "stolen" (moved to a new channel) if it's
                already connected elsewhere
            send_feedback (bool) - Send feedback back
                to the user on success
            error_feedback (bool) - Send feedback to the
                channel on error

        Returns:
            connected (bool) - If the voice client is
                connected or not
            vctl (VoiceController) - VoiceController object
        """

        permitted, reason, can_respond, can_embed = await AsyncHelpers.verify_feedback_permissions(bot, author.guild, channel)

        if not permitted:
            # Check if we can at least send messages
            if can_respond and can_embed and error_feedback:
                await DiscordUtils.error(bot, channel, title = "Can't use this channel!", description = f"Make sure I have permission to read and send messages and message history, as well as add and use external emojis in <#{channel.id}>")

            elif can_respond and error_feedback:
                # Can't send an embed, but can send a normal message
                await channel.send(f"**Can't use this channel!**\nMake sure I have permission to read and send messages and message history, embed links and attach files, as well as add and use external emojis in <#{channel.id}>")

            return False, None

        if author.voice == None:
            if error_feedback:
                await DiscordUtils.error(bot, channel, title = "Can't play!", description = "You're not connected to a voice channel!")

            return False, None

        if gid in bot.mem_storage["voice"]:
            vctl = bot.mem_storage["voice"][gid]
            vctl.feedback_channel = channel

            if vctl.client.is_connected():
                # Already connected. Make sure the user isn't trying
                # to steal the bot.

                if author.voice.channel != vctl.client.channel:
                    # Bot is in another channel

                    if allow_steal:
                        permitted, reason = await AsyncHelpers.verify_channel_permissions(bot, author.guild, author.voice.channel)

                        if not permitted:
                            if error_feedback:
                                await DiscordUtils.error(bot, channel, title = "Can't connect!", description = f"I don't have permission to join and play sound in 🔉{author.voice.channel.name}!")

                            return False, None

                        await vctl.client.disconnect(force = True)

                        vctl.client = await author.voice.channel.connect()

                        if send_feedback:
                            await channel.send(
                                embed = DiscordUtils.create_embed(
                                    bot,
                                    title = f"Moved to 🔉{author.voice.channel.name}.",
                                    color = "green"
                                )
                            )

                    else:
                        if error_feedback:
                            await DiscordUtils.error(bot, channel, title = "Can't connect!", description = f"I'm already connected to another channel. If you have permission to, you can use `{gdb['prefix']}music steal` to move me to your channel.")

                        return False, None

            elif connect:
                vctl.client = await author.voice.channel.connect()

                #https://www.youtube.com/watch?v=IG2JF0P4GFA

                if send_feedback:
                    await channel.send(
                        embed = DiscordUtils.create_embed(
                            bot,
                            title = f"Connected to 🔉{author.voice.channel.name}.",
                            color = "green"
                        )
                    )

        else:
            vctl = VoiceController(bot, gid, {} if not gdb.get("voice_settings") else gdb.get("voice_settings"))
            vctl.feedback_channel = channel
            bot.mem_storage["voice"][gid] = vctl

            if connect:
                permitted, reason = await AsyncHelpers.verify_channel_permissions(bot, author.guild, author.voice.channel)

                if not permitted:
                    if error_feedback:
                        await DiscordUtils.error(bot, channel, title = "Can't connect!", description = f"I don't have permission to join and play sound in 🔉{author.voice.channel.name}!")

                    return False, None

                client = await author.voice.channel.connect()
                vctl.client = client
                vctl.channel = author.voice.channel

                if send_feedback:
                    await channel.send(
                        embed = DiscordUtils.create_embed(
                            bot,
                            title = f"Connected to 🔉{author.voice.channel.name}.",
                            color = "green"
                        )
                    )

        return True, vctl
            


    async def verify_channel_permissions(
            bot,
            guild: discord.Guild,
            channel: discord.VoiceChannel
        ):
        """
        Verifies that the bot has all necessary permissions
        to interact with a voice channel.

        Parameters:
            bot (Bot)
            guild (discord.Guild)
            channel (discord.VoiceChannel)

        Returns:
            permitted (bool) - If the bot can use the channel
            reason (str) - Why the action isn't permitted, if
                permitted is False
        """

        perms = channel.permissions_for(guild.get_member(bot.client.user.id))

        req = [
            perms.view_channel,
            perms.connect,
            perms.speak,
            perms.use_voice_activation
        ]

        if False in req:
            return False, "Missing permissions to join that channel."
        
        return True, None

    async def verify_feedback_permissions(
            bot,
            guild: discord.Guild,
            channel: discord.TextChannel
        ):
        """
        Verifies that the bot has all necessary permissions
        to interact with a feedback channel.

        Parameters:
            bot (Bot)
            guild (discord.Guild)
            channel (discord.TextChannel)

        Returns:
            permitted (bool) - If the bot can use the channel
            reason (str) - Why the action isn't permitted, if
                permitted is False
            can_send (bool) - If missing permissions, can I
                at least send a message there?
            can_embed (bool) - If failed, can I send an embed
                error message?
        """

        perms = channel.permissions_for(guild.get_member(bot.client.user.id))

        req = [
            perms.view_channel,
            perms.send_messages,
            perms.read_message_history,
            perms.use_external_emojis,
            perms.add_reactions,
            perms.embed_links
        ]

        if False in req:
            return False, "Missing permissions to chat in that channel.", perms.send_messages, perms.embed_links
        
        return True, None, None, None

    async def search_youtube(
            bot,
            url: str,
            max_duration: int,
            results: int
        ):
        """
        Searches YouTube for the specified keywords. Returns
        the top 5 videos found under the maximum duration.

        Parameters:
            url (str)
            max_duration (int)

        Returns:
            videos (list) - Maximum length of 5. First 5
                videos found under the search term.
        """

        vidlist = VideoList(bot)

        await vidlist.search(url, results + 5) # 5 extra, just in case the ones we find exceed the max duration.

        nl = []
        for video in vidlist.videos:
            if video.duration <= max_duration:
                nl.append(video)

            if len(nl) >= results:
                break

        del vidlist # Thing takes up a lot of RAM. Better to purge it now.
        return nl

class YoutubeClient:
    """
    Code adapted from the danksearch package.

    Some modifications to make it run better & 
    get more refined search results.
    """

    def __init__(self):
        self.cobj = ClientSession(connector = TCPConnector(verify_ssl = False))

    async def get(self, url):
        async with self.cobj.get(url) as r:
            return await r.text()

    async def close(self):
        await self.cobj.close()

class YoutubeVideo:
    def __init__(self, url):
        self.url = url

        self.title = None

    async def search(self, index = 0):
        pass

class VideoList:
    def __init__(self, bot):
        self.videos = []
        self.bot = bot

    async def search(self, query, find = 5):
        if query.strip() == "":
            raise exceptions.NoVideoSpecified

        """
        Video list starts with:
        {"contents":[{"itemSectionRenderer":{"contents":


        Each video is within that list
        Can also include playlists or channels. Need to filter those out

        A video object will be listed as "videoRenderer".

        Everything else should be ignored.

        To validate this, we have to also end at:
        }}}}],"trackingParams"
        then append:
        }}}}]
        """
        start_prepend = "["
        start_header = '{"contents":[{"itemSectionRenderer":{"contents":['
        end_header = ',"toggledAccessibility":{"accessibilityData":{"label":"Added"}},'
        end_append = '}}]}}]'

        try: # TODO: Parse this better.
            raw = await yc.get(f"https://youtube.com/results?search_query={query}") # Get the youtube page

            if start_header not in raw:
                raise exceptions.InvalidDataSent

            if end_header not in raw:
                raise exceptions.InvalidDataSent

            json_raw = start_prepend + raw.split(start_header, 1)[1].rsplit(end_header, 1)[0] + end_append

            data = json.loads(json_raw) # Very memory inefficient. PogU

        except Exception as e:
            path = f"fail-{time.time()}.html"
            json_path = f"fail-{time.time()}.json"

            try:
                with open(json_path, "w+") as f:
                    f.write(json_raw)

                json_str = f"\nDumped JSON file as `{json_path}`."

            except:
                json_str = ""

            await self.bot.config.error_reporting.send(
                embed = DiscordUtils.create_embed(
                    self.bot,
                    title = "Failed to read YouTube data!",
                    description = f"Dumped file as `{path}`.{json_str}",
                    color = "yellow"
                )
            )

            with open(path, "w+") as f:
                f.write(raw)

            raise

        del raw
        del json_raw # Try to free *some* stuff up

        for renderer in data:
            if "videoRenderer" == list(renderer)[0]:
                # This is a video. Parse it
                v_ctx = renderer["videoRenderer"]
                vid = YoutubeVideo(f"https://youtube.com/watch?v={v_ctx['videoId']}")
                vid.title = MiscUtils.follow(v_ctx, "title/runs:0/text")
                vid.timestamp = MiscUtils.follow(v_ctx, "lengthText/simpleText")
                
                if not vid.timestamp:
                    continue # Best way to check for validity

                vid.description = MiscUtils.follow(v_ctx, "descriptionSnippet/runs:0/text")
                vid.duration = MiscUtils.get_sec_from_timestamp(vid.timestamp)
                vid.views = MiscUtils.follow(v_ctx, "viewCountText/simpleText").split(" ")[0]
                vid.thumbnail = MiscUtils.follow(v_ctx, "thumbnail/thumbnails:0/url")
                vid.uploader = MiscUtils.follow(v_ctx, "ownerText/runs:0/text")
                    
                self.videos.append(vid)

        return self.videos


yc = YoutubeClient() # Define this globally. Only need one.