import asyncio
import random
from difflib import SequenceMatcher
import math
import discord.ext.pages
import discord.ext.tasks
import requests
import wavelink
from discord.ext import commands, tasks
from discord.ui import Item
from bot import reload_cogs
import git

from data.guilddata import get_data, set_data

import spotify
from backend import log, error_template, embed_template, client, alpha
from backend import wavelink_host, wavelink_password, wavelink_port

duration_increment = 3
minimum_duration = 3
maximum_duration = 30


class Main(discord.Cog):
    def __init__(self, client):
        self.client = client
        self.gcmd = git.cmd.Git("../git")
        self.grepo = git.Repo("./")

    async def git_pull(self):
        self.gcmd.pull()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.connect_nodes()
        if not alpha:
            self.update_information.start()

    async def connect_nodes(self):
        await self.client.wait_until_ready()
        await wavelink.NodePool.create_node(
            bot=self.client,
            host=wavelink_host,
            port=wavelink_port,
            password=wavelink_password,
        )

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        log.info(f"{node.identifier} is ready.")

    @tasks.loop(minutes=30)
    async def update_information(self):
        if alpha:
            return

        guild_count = len(list(client.guilds))

        ### Top.gg ###

        body = {
            "server_count": guild_count,
        }

        headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjEwNTU0MjU2ODc3MjY2MDg0NTQiLCJib3QiOnRydWUsImlhdCI6MTY3NzQ0MTU1M30.DkTNXxo5XP_w1KzhMENci9c9YU6YLKdcTAIQA9icFC4"
        }

        requests.post(
            "https://top.gg/api/bots/1055425687726608454/stats",
            json=body,
            headers=headers,
        )

        ### DiscordBotList.com ###

        body = {"guilds": guild_count}

        headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0IjoxLCJpZCI6IjEwNTU0MjU2ODc3MjY2MDg0NTQiLCJpYXQiOjE2NzczMjQ0NTF9.Nps_Cam9URmkTdBiUnak0gz2PkdXJsRYqejwRJxdxGQ"
        }

        requests.post(
            "https://discordbotlist.com/api/v1/bots/tunetrivia/stats",
            data=body,
            headers=headers,
        )

        ### Discords.com ###

        body = {"server_count": guild_count}

        headers = {
            "Authorization": "ac76827201be1ef033374d1bf3b92b2b1c440fb929a5f64f586b5069b0dbabe54ff639b22a5e2bf0d72e67302d02443369367736a0abbce1d1f9ea641d0d75b6"
        }

        requests.post(
            "https://discords.com/bots/api/bot/1055425687726608454",
            data=body,
            headers=headers,
        )

        ### Discord.Bots.gg ###

        body = {"guildCount": guild_count}

        headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiJ9.eyJhcGkiOnRydWUsImlkIjoiNTY2OTUxNzI3MTgyMzgxMDU3IiwiaWF0IjoxNjc3MzI0NzAyfQ.pVBZusOThAKtQ_VSmVXFLzBl8Ksg48Ayfgom6zekEI0"
        }

        requests.post(
            "https://discord.bots.gg/api/v1/bots/1055425687726608454/stats",
            json=body,
            headers=headers,
        )

        ### Disforge.com ###

        body = {"servers": guild_count}

        headers = {
            "Authorization": "a981aa94a7c86915bba835c4575e741f6200a95399397071257c7e498ee57ec3"
        }

        requests.post(
            "https://disforge.com/api/botstats/2958", json=body, headers=headers
        )

        ### DiscordList.com ###

        body = {"count": guild_count}

        headers = {
            "Authorization": "Bearer mR1thC8JGq5yQLIM994i4VS0dV5Ovfn6ZDeWATK2kdC7BxelGhhevC4eNNaM7fVPmVuWsl4veas0KR4iOnSs0i7OmapRWa3k"
        }

        requests.post(
            "https://api.discordlist.gg/v0/bots/1055425687726608454/guilds",
            json=body,
            headers=headers,
        )

        ######################

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        vc = member.guild.voice_client

        if before.channel is None and member.id == client.application_id:
            await member.guild.change_voice_state(channel=after.channel, self_deaf=True)

        if after.channel is None:
            if len(before.channel.members) == 1:
                if vc:
                    await vc.disconnect()

            if member.id == client.application_id:
                if get_data(member.guild.id, "state") == "stopped":
                    return
                self.end_session(member)
                ctx = get_data(before.channel.guild.id, "ctx")
                embed = embed_template()
                if len(before.channel.members) >= 1:
                    embed.title = "Session Ended"
                    embed.description = "Bot was disconnected from the voice channel."
                else:
                    embed.title = "Session Ended"
                    embed.description = (
                        "The session ended because everyone left the voice channel."
                    )
                await ctx.send(embed=embed)

    @commands.slash_command(
        description="View TuneTrivia's commands.",
    )
    async def help(self, ctx):
        commands = ""

        for command in client.application_commands:
            commands += f"/**{command.name}** - {command.description}\n"

        embed = embed_template()
        embed.title = "Commands of TuneTrivia"
        embed.description = commands

        await ctx.respond(embed=embed)

    @commands.slash_command(
        description="Play TuneTrivia!",
    )
    async def play(self, ctx, spotify_playlist_url=""):
        await self._play(ctx, spotify_playlist_url)

    @commands.slash_command(
        description="Alias of /play",
    )
    async def create(self, ctx, spotify_playlist_url=""):
        await self._play(ctx, spotify_playlist_url)

    @commands.slash_command(
        description="Alias of /play",
    )
    async def start(self, ctx, spotify_playlist_url=""):
        await self._play(ctx, spotify_playlist_url)

    @commands.slash_command(
        description="Invite TuneTrivia to your server!",
    )
    async def invite(self, ctx):
        embed = embed_template()
        embed.title = "Invite TuneTrivia!"
        embed.description = (
            "Click [here](https://discord.com/oauth2/authorize?client_id=1055425687726608454&permissions=277028539456&scope=bot"
            "%20applications.commands) to invite TuneTrivia to your server."
        )

        await ctx.respond(embed=embed)

    @commands.slash_command(
        description="Join the Support Server!",
    )
    async def support(self, ctx):
        embed = embed_template()
        embed.title = "Join the Support Server!"
        embed.description = (
            "Click [here](https://discord.gg/s8nWZVGqDF) to join the support server.\n"
            "Please report any bugs or issues you may find to the support server."
        )

        await ctx.respond(embed=embed)

    @commands.command("update")
    async def update(self, ctx):
        if ctx.author.id != 566951727182381057:
            return

        if alpha:
            reload_cogs()

            embed = embed_template()
            embed.title = "Successfully updated all cogs"
            embed.description = "Ran reload_cogs()"

            await ctx.send(embed=embed)
        else:
            await self.git_pull()
            reload_cogs()

            embed = embed_template()
            embed.title = "Successfully pulled from repo and updated all cogs"
            embed.description = "Ran git_pull() and reload_cogs()"

            await ctx.send(embed=embed)

    @commands.slash_command(
        description="Check the stats of TuneTrivia.",
    )
    async def stats(self, ctx):
        embed = embed_template()
        embed.title = "TuneTrivia Live Stats"
        embed.description = "Main Statistics for TuneTrivia"
        embed.add_field(name="Server Count", value=f"{len(client.guilds)}", inline=True)
        embed.add_field(name="User Count", value=f"{len(client.users)}\n", inline=True)
        embed.add_field(name="\u200b", value=f"\u200b", inline=True)
        embed.add_field(
            name="Ping", value=f"{round(client.latency * 1000)}ms", inline=True
        )
        embed.add_field(
            name="Build", value=f"{len(list(self.grepo.iter_commits()))}", inline=True
        )
        embed.add_field(name="\u200b", value=f"\u200b", inline=True)

        await ctx.respond(embed=embed)

    @commands.slash_command(description="Stop the current session.")
    async def stop(self, ctx):
        vc = ctx.voice_client

        if get_data(ctx.guild.id, "state") is None:
            self.end_session(ctx)

        if get_data(ctx.guild.id, "state") == "stopped":
            if vc:
                await vc.disconnect()
                return await ctx.respond(
                    embed=error_template(
                        "The bot was removed from call since no TuneTrivia session is running. If this issue is repeatable, "
                        "please report to SleepyStew#7777."
                    ),
                    ephemeral=True,
                )
            return await ctx.respond(
                embed=error_template(
                    "There is no TuneTrivia session running. You can start one using /play."
                ),
                ephemeral=True,
            )

        self.end_session(ctx)

        await vc.disconnect()

        embed = embed_template()
        embed.title = "Session Stopped"
        embed.description = "Successfully disconnected from the voice channel."

        await ctx.respond(embed=embed)

    async def _play(self, ctx, spotify_playlist_url):
        spotify_playlist_url = spotify_playlist_url.strip().strip("\n")

        if get_data(ctx.guild.id, "state") is None:
            set_data(ctx.guild.id, "state", "stopped")

        vc = ctx.voice_client

        if get_data(ctx.guild.id, "state") != "stopped":
            if not vc:
                self.end_session(ctx)
            else:
                return await ctx.respond(
                    embed=error_template(
                        "A TuneTrivia session is already running. Use /stop to end the session."
                    ),
                    ephemeral=True,
                )

        if ctx.author.voice is None:
            return await ctx.respond(
                embed=error_template(
                    "You are not connected to a voice channel. Join one to get started."
                ),
                ephemeral=True,
            )

        voice_channel = ctx.author.voice.channel

        if spotify_playlist_url != "":
            print(f"Attempting playlist search on: {spotify_playlist_url}")
            if spotify.is_valid_url(spotify_playlist_url):
                playlist = spotify.get_playlist(spotify_playlist_url)
                if not playlist:
                    return await ctx.respond(
                        embed=error_template(
                            "Sorry, couldn't access the spotify playlist you provided."
                        ),
                        ephemeral=True,
                    )
                playlist = playlist[0]
                if len(playlist["tracks"]["items"]) < 1:
                    return await ctx.respond(
                        embed=error_template(
                            "This playlist doesn't contain any songs, please try a different one."
                        ),
                        ephemeral=True,
                    )
            else:
                return await ctx.respond(
                    embed=error_template(
                        "The spotify playlist url you provided is invalid. Make sure it starts with "
                        "`https://open.spotify.com/playlist/`."
                    ),
                    ephemeral=True,
                )
        else:
            default_playlist = "https://open.spotify.com/playlist/37i9dQZF1DWU7oFJkRIANi?si=6bae30f0ac264a9e"
            playlist = spotify.get_playlist(default_playlist)
            if not playlist:
                return await ctx.respond(
                    embed=error_template(
                        """Sorry, couldn't access the default spotify playlist.
                Try again or report this to the support server (/support)."""
                    ),
                    ephemeral=True,
                )
            playlist = playlist[0]
            if not playlist:
                return await ctx.respond(
                    embed=error_template(
                        "An error occurred trying to play the default playlist, please try again or provide one "
                        "manually."
                    ),
                    ephemeral=True,
                )
            if len(playlist["tracks"]["items"]) < 1:
                return await ctx.respond(
                    embed=error_template(
                        "This playlist doesn't contain any songs, please try a different one."
                    ),
                    ephemeral=True,
                )

        client_user = voice_channel.guild.get_member(client.application_id)

        permissions = voice_channel.permissions_for(client_user)

        if not (permissions.connect and permissions.speak):
            return await ctx.respond(
                embed=error_template(
                    f"Sorry, I do not have permission the necessary permissions in this voice channel. Make sure I have "
                    f"the Connect and Speak permissions in <#{ctx.author.voice.channel.id}>."
                ),
                ephemeral=True,
            )

        permissions = ctx.channel.permissions_for(client_user)

        if not (
            permissions.read_messages
            and permissions.send_messages
            and permissions.add_reactions
        ):
            return await ctx.respond(
                embed=error_template(
                    f"Sorry, I do not have permission the necessary permissions in this text channel. Make sure I have the Read "
                    f"Messages, Send Messages and Add Reactions permissions in <#{ctx.channel.id}>."
                ),
                ephemeral=True,
            )

        vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)

        await vc.set_volume(50)

        set_data(ctx.guild.id, "state", "idle")
        set_data(ctx.guild.id, "active_channel", ctx.channel.id)
        set_data(ctx.guild.id, "playlist", playlist)
        set_data(ctx.guild.id, "ctx", ctx)
        set_data(ctx.guild.id, "duration", 15)

        print(f"Started session in guild: {ctx.guild.name}")

        embed = embed_template()
        embed.title = "Started Session"
        embed.description = (
            f"Click the play button below to begin.\n"
            "Use the up and down buttons to change duration."
        )
        embed.add_field(name="Playlist", value=playlist["name"], inline=True)
        embed.add_field(
            name="Song Duration",
            value=f"{get_data(ctx.guild.id, 'duration')} seconds",
            inline=True,
        )
        embed.add_field(
            name="Bound to",
            value=f"<#{get_data(ctx.guild.id, 'active_channel')}>",
            inline=True,
        )

        class StartSession(discord.ui.View):
            def __init__(self, play_song, *items: Item):
                super().__init__(*items, timeout=None)
                self.play_song = play_song

            @discord.ui.button(label="⬇", style=discord.ButtonStyle.primary)
            async def button_decrease(self, button, interaction):
                if get_data(ctx.guild.id, "duration") - 3 < minimum_duration:
                    return await interaction.response.send_message(
                        content=f"Minimum duration is {minimum_duration} seconds.",
                        ephemeral=True,
                    )
                await interaction.response.defer()
                set_data(
                    ctx.guild.id, "duration", get_data(ctx.guild.id, "duration") - 3
                )
                embed.set_field_at(
                    1,
                    name="Song Duration",
                    value=f"{get_data(ctx.guild.id, 'duration')} seconds",
                    inline=True,
                )
                await self.message.edit(embed=embed)

            @discord.ui.button(label="▶", style=discord.ButtonStyle.green)
            async def button_play(self, button, interaction):
                await interaction.response.defer()
                for child in self.children:
                    child.disabled = True
                await self.message.edit(view=self)
                await self.play_song(ctx)

            @discord.ui.button(label="⬆", style=discord.ButtonStyle.primary)
            async def button_increase(self, button, interaction):
                if get_data(ctx.guild.id, "duration") + 3 > maximum_duration:
                    return await interaction.response.send_message(
                        content=f"Maximum duration is {maximum_duration} seconds.",
                        ephemeral=True,
                    )
                await interaction.response.defer()
                set_data(
                    ctx.guild.id, "duration", get_data(ctx.guild.id, "duration") + 3
                )
                embed.set_field_at(
                    1,
                    name="Song Duration",
                    value=f"{get_data(ctx.guild.id, 'duration')} seconds",
                    inline=True,
                )
                await self.message.edit(embed=embed)

        session = StartSession(self.play_song)

        @client.event
        async def on_session_end(id):
            if id == ctx.guild.id:
                for child in session.children:
                    child.disabled = True
                await session.message.edit(view=session)

        await ctx.respond(embed=embed, view=session)

    async def skip(self):
        pass

    async def play_song(self, ctx):
        ctx = get_data(ctx.guild.id, "ctx")

        vc = ctx.voice_client

        if get_data(ctx.guild.id, "state") not in ["idle", "times_up", "skipping"]:
            return

        set_data(ctx.guild.id, "state", "playing")

        attempts = 0
        song = None
        while not song:
            if attempts >= 3:
                break

            attempts += 1

            selection = get_data(ctx.guild.id, "playlist")["tracks"]["items"][
                random.randint(
                    0, len(get_data(ctx.guild.id, "playlist")["tracks"]["items"]) - 1
                )
            ]

            try:
                song_name = selection["track"]["name"]
                song_artists = []
                for artist in selection["track"]["artists"]:
                    song_artists.append(artist["name"])
                song_artists = ", ".join(song_artists)
                set_data(ctx.guild.id, "song_name", song_name)
                set_data(ctx.guild.id, "song_artists", song_artists)
                set_data(ctx.guild.id, "current_song", selection)
            except:
                song = None
                continue
            try:
                song = await wavelink.YouTubeMusicTrack.search(
                    f"{song_name} - {song_artists}", return_first=True
                )
                if song.duration < 1:
                    raise
                set_data(ctx.guild.id, "song", song)
            except:
                await ctx.send(
                    embed=error_template(
                        "Song not found, retrying with a different song..."
                    )
                )
                song = None
                continue

        if attempts >= 3:
            return await ctx.respond(
                embed=error_template(
                    "Maximum attempts reached, please try again later or with a different playlist.\n"
                    "If this error persists, please report it in the support server by using /support."
                )
            )

        try:
            await vc.play(song)
            start_at = random.randint(
                math.floor(0 + (vc.source.duration * 0.2)),
                math.floor(
                    vc.source.duration
                    - (vc.source.duration * 0.4)
                    - get_data(ctx.guild.id, "duration")
                ),
            )
            set_data(ctx.guild.id, "start_at", start_at)
            await vc.seek(start_at * 1000)
        except AttributeError:
            # shouldn't be necessary, just in case
            self.end_session(ctx)

            return await ctx.respond(
                content="The session has ended. You can create a new one using /play.",
                ephemeral=True,
            )

        embed = embed_template()
        embed.title = "Now Playing"
        embed.description = (
            f"You now have {get_data(ctx.guild.id, 'duration') * 2} seconds guess the song by typing in chat.\n"
            "After the song stops you can click the question mark button below to reveal the answer.\n"
            "\n"
            "**Reactions Key**\n"
            "✅ - Correct Song\n"
            "❎ - Correct Artist\n"
            "❌ - Incorrect Guess"
        )

        embed.add_field(
            name="Song Duration",
            value=f"{get_data(ctx.guild.id, 'duration')} seconds",
            inline=True,
        )

        # embed.add_field(name="Song", value=f"{get_data(ctx.guild.id, 'song_name')}", inline=True)

        class PlayingSong(discord.ui.View):
            def __init__(self, *items: Item, reveal):
                super().__init__(*items, timeout=None)
                self.reveal = reveal

            @discord.ui.button(
                label="❔", style=discord.ButtonStyle.primary, disabled=True
            )
            async def button_reveal(self, button, interaction):
                await self.reveal(ctx)
                await interaction.response.defer()
                for child in self.children:
                    child.disabled = True
                await self.message.edit(view=self)

        play_song = PlayingSong(reveal=self.reveal)
        await ctx.send(embed=embed, view=play_song)

        @client.event
        async def on_correct_guess(id):
            if id == ctx.guild.id:
                for child in play_song.children:
                    child.disabled = True
                await play_song.message.edit(view=play_song)

        original_song = get_data(ctx.guild.id, "current_song")

        await asyncio.sleep(get_data(ctx.guild.id, "duration"))

        if (
            get_data(ctx.guild.id, "state") != "playing"
            or get_data(ctx.guild.id, "current_song") != original_song
        ):
            return

        set_data(ctx.guild.id, "state", "played")

        for child in play_song.children:
            child.disabled = False

        await vc.seek(vc.source.duration * 1000)
        await play_song.message.edit(view=play_song)

        await asyncio.sleep(get_data(ctx.guild.id, "duration"))

        if (
            get_data(ctx.guild.id, "state") != "played"
            or get_data(ctx.guild.id, "current_song") != original_song
        ):
            return

        for child in play_song.children:
            child.disabled = True

        await play_song.message.edit(view=play_song)

        await self.times_up(ctx)

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if f"<@{client.application_id}>" in ctx.content:
            embed = embed_template()
            embed.title = f"Hey {ctx.author.name}! 👋"
            embed.description = (
                f"Looking to start a TuneTrivia session? Use /play!\n"
                "Looking for a full list of commands? Use /help!"
            )
            await ctx.channel.send(embed=embed)

        try:
            if (
                get_data(ctx.guild.id, "state") not in ["playing", "played"]
                or ctx.author.id == client.application_id
                or ctx.channel.id != get_data(ctx.guild.id, "active_channel")
            ):
                return
        except AttributeError:
            return
        song_name = get_data(ctx.guild.id, "song_name")
        song_parts = song_name.lower().split("-")
        song_parts.extend(song_name.lower().split("("))
        song_parts.extend(song_name.lower().split(")"))
        song_parts.extend([song_name.lower()])
        artist_parts = get_data(ctx.guild.id, "song_artists").lower().split(", ")
        if any(
            part
            for part in song_parts
            if SequenceMatcher(None, ctx.content.lower(), part).ratio() > 0.7
        ):
            await ctx.add_reaction(emoji="✅")
            await self.correct_guess(ctx, ctx.author)
        elif any(
            part
            for part in artist_parts
            if SequenceMatcher(None, ctx.content.lower(), part).ratio() > 0.7
        ):
            await ctx.add_reaction(emoji="❎")
        else:
            await ctx.add_reaction(emoji="❌")

    async def correct_guess(self, ctx, guesser):
        ctx = get_data(ctx.guild.id, "ctx")

        vc = ctx.voice_client

        if get_data(ctx.guild.id, "state") not in ["playing", "played"]:
            return

        set_data(ctx.guild.id, "state", "idle")

        client.dispatch("correct_guess", ctx.guild.id)

        embed = embed_template()
        embed.title = "Correct!"
        embed.description = (
            f"Congratulations <@{guesser.id}> for guessing correctly!\n"
            "Enjoy the song! To play again press the play button below."
        )

        embed.add_field(
            name="Song", value=f"{get_data(ctx.guild.id, 'song_name')}", inline=True
        )
        embed.add_field(
            name="Artists",
            value=f"{get_data(ctx.guild.id, 'song_artists')}",
            inline=True,
        )
        embed.add_field(
            name="Song Duration",
            value=f"{get_data(ctx.guild.id, 'duration')} seconds",
            inline=False,
        )

        class PlayAgain(discord.ui.View):
            def __init__(self, *items: Item, play_song):
                super().__init__(*items, timeout=None)
                self.play_song = play_song

            @discord.ui.button(label="⬇", style=discord.ButtonStyle.primary)
            async def button_decrease(self, button, interaction):
                if get_data(ctx.guild.id, "duration") - 3 < minimum_duration:
                    return await interaction.response.send_message(
                        content=f"Minimum duration is {minimum_duration} seconds.",
                        ephemeral=True,
                    )
                await interaction.response.defer()
                set_data(
                    ctx.guild.id, "duration", get_data(ctx.guild.id, "duration") - 3
                )
                embed.set_field_at(
                    2,
                    name="Song Duration",
                    value=f"{get_data(ctx.guild.id, 'duration')} seconds",
                    inline=False,
                )
                await self.message.edit(embed=embed)

            @discord.ui.button(label="▶", style=discord.ButtonStyle.green)
            async def button_reveal(self, button, interaction):
                await interaction.response.defer()
                for child in self.children:
                    child.disabled = True
                await self.message.edit(view=self)
                await self.play_song(ctx)

            @discord.ui.button(label="⬆", style=discord.ButtonStyle.primary)
            async def button_increase(self, button, interaction):
                if get_data(ctx.guild.id, "duration") + 3 > maximum_duration:
                    return await interaction.response.send_message(
                        content=f"Maximum duration is {maximum_duration} seconds.",
                        ephemeral=True,
                    )
                await interaction.response.defer()
                set_data(
                    ctx.guild.id, "duration", get_data(ctx.guild.id, "duration") + 3
                )
                embed.set_field_at(
                    2,
                    name="Song Duration",
                    value=f"{get_data(ctx.guild.id, 'duration')} seconds",
                    inline=False,
                )
                await self.message.edit(embed=embed)

        play_song = PlayAgain(play_song=self.play_song)

        @client.event
        async def on_session_end(id):
            if id == ctx.guild.id:
                for child in play_song.children:
                    child.disabled = True
                await play_song.message.edit(view=play_song)

        await ctx.channel.send(embed=embed, view=play_song)

        if not vc.is_playing():
            await vc.play(get_data(ctx.guild.id, "song"))
            await vc.seek(
                (
                    get_data(ctx.guild.id, "start_at")
                    + get_data(ctx.guild.id, "duration")
                )
                * 1000
            )

    async def times_up(self, ctx):
        ctx = get_data(ctx.guild.id, "ctx")

        if get_data(ctx.guild.id, "state") not in ["played"]:
            return

        set_data(ctx.guild.id, "state", "idle")

        embed = embed_template()
        embed.title = "Time is Up!"
        embed.description = f"To play again press the play button below."
        embed.add_field(
            name="Song", value=f"{get_data(ctx.guild.id, 'song_name')}", inline=True
        )
        embed.add_field(
            name="Artists",
            value=f"{get_data(ctx.guild.id, 'song_artists')}",
            inline=True,
        )
        embed.add_field(
            name="Song Duration",
            value=f"{get_data(ctx.guild.id, 'duration')} seconds",
            inline=False,
        )

        class PlayAgain(discord.ui.View):
            def __init__(self, *items: Item, play_song):
                super().__init__(*items, timeout=None)
                self.play_song = play_song

            @discord.ui.button(label="⬇", style=discord.ButtonStyle.primary)
            async def button_decrease(self, button, interaction):
                if get_data(ctx.guild.id, "duration") - 3 < minimum_duration:
                    return await interaction.response.send_message(
                        content=f"Minimum duration is {minimum_duration} seconds.",
                        ephemeral=True,
                    )
                await interaction.response.defer()
                set_data(
                    ctx.guild.id, "duration", get_data(ctx.guild.id, "duration") - 3
                )
                embed.set_field_at(
                    2,
                    name="Song Duration",
                    value=f"{get_data(ctx.guild.id, 'duration')} seconds",
                    inline=False,
                )
                await self.message.edit(embed=embed)

            @discord.ui.button(label="▶", style=discord.ButtonStyle.green)
            async def button_reveal(self, button, interaction):
                await interaction.response.defer()
                for child in self.children:
                    child.disabled = True
                await self.message.edit(view=self)
                await self.play_song(ctx)

            @discord.ui.button(label="⬆", style=discord.ButtonStyle.primary)
            async def button_increase(self, button, interaction):
                if get_data(ctx.guild.id, "duration") + 3 > maximum_duration:
                    return await interaction.response.send_message(
                        content=f"Maximum duration is {maximum_duration} seconds.",
                        ephemeral=True,
                    )
                await interaction.response.defer()
                set_data(
                    ctx.guild.id, "duration", get_data(ctx.guild.id, "duration") + 3
                )
                embed.set_field_at(
                    2,
                    name="Song Duration",
                    value=f"{get_data(ctx.guild.id, 'duration')} seconds",
                    inline=False,
                )
                await self.message.edit(embed=embed)

        play_song = PlayAgain(play_song=self.play_song)

        @client.event
        async def on_session_end(id):
            if id == ctx.guild.id:
                for child in play_song.children:
                    child.disabled = True
                await play_song.message.edit(view=play_song)

        await ctx.send(embed=embed, view=play_song)

    async def reveal(self, ctx):
        ctx = get_data(ctx.guild.id, "ctx")

        if get_data(ctx.guild.id, "state") not in ["played", "times_up"]:
            return

        set_data(ctx.guild.id, "state", "idle")

        embed = embed_template()
        embed.title = "Guessing has Concluded"
        embed.description = f"To play again press the play button below."
        embed.add_field(
            name="Song", value=f"{get_data(ctx.guild.id, 'song_name')}", inline=True
        )
        embed.add_field(
            name="Artists",
            value=f"{get_data(ctx.guild.id, 'song_artists')}",
            inline=True,
        )
        embed.add_field(
            name="Song Duration",
            value=f"{get_data(ctx.guild.id, 'duration')} seconds",
            inline=False,
        )

        class PlayAgain(discord.ui.View):
            def __init__(self, *items: Item, play_song):
                super().__init__(*items, timeout=None)
                self.play_song = play_song

            @discord.ui.button(label="⬇", style=discord.ButtonStyle.primary)
            async def button_decrease(self, button, interaction):
                if get_data(ctx.guild.id, "duration") - 3 < minimum_duration:
                    return await interaction.response.send_message(
                        content=f"Minimum duration is {minimum_duration} seconds.",
                        ephemeral=True,
                    )
                await interaction.response.defer()
                set_data(
                    ctx.guild.id, "duration", get_data(ctx.guild.id, "duration") - 3
                )
                embed.set_field_at(
                    2,
                    name="Song Duration",
                    value=f"{get_data(ctx.guild.id, 'duration')} seconds",
                    inline=False,
                )
                await self.message.edit(embed=embed)

            @discord.ui.button(label="▶", style=discord.ButtonStyle.green)
            async def button_reveal(self, button, interaction):
                await interaction.response.defer()
                for child in self.children:
                    child.disabled = True
                await self.message.edit(view=self)
                await self.play_song(ctx)

            @discord.ui.button(label="⬆", style=discord.ButtonStyle.primary)
            async def button_increase(self, button, interaction):
                if get_data(ctx.guild.id, "duration") + 3 > maximum_duration:
                    return await interaction.response.send_message(
                        content=f"Maximum duration is {maximum_duration} seconds.",
                        ephemeral=True,
                    )
                await interaction.response.defer()
                set_data(
                    ctx.guild.id, "duration", get_data(ctx.guild.id, "duration") + 3
                )
                embed.set_field_at(
                    2,
                    name="Song Duration",
                    value=f"{get_data(ctx.guild.id, 'duration')} seconds",
                    inline=False,
                )
                await self.message.edit(embed=embed)

        play_song = PlayAgain(play_song=self.play_song)

        @client.event
        async def on_session_end(id):
            if id == ctx.guild.id:
                for child in play_song.children:
                    child.disabled = True
                await play_song.message.edit(view=play_song)

        await ctx.send(embed=embed, view=play_song)

    def end_session(self, ctx):
        print(f"Stopped session in guild: {ctx.guild.name}")
        client.dispatch("session_end", id=ctx.guild.id)
        set_data(ctx.guild.id, "state", "stopped")


def setup(client):
    client.add_cog(Main(client))
