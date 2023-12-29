import discord
from discord.ext import commands
from dotenv.main import load_dotenv
import os
from discord.ui import View, Button
from discord.utils import get
from discord import FFmpegPCMAudio
from youtube_dl import YoutubeDL
from pytube import YouTube
import re
from yandex_music import ClientAsync
import asyncio
import random


load_dotenv()

TOKEN = os.environ['TOKEN']
TOKEN_YANDEX = os.environ['TOKEN_YANDEX']

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

queue = {}
track_inform = {}
information_track = {}
playlist_change = {}
repeat_status = {}

random.seed(1)

# =============================================================================#
Button1 = Button(label="Vol: + 10", style=discord.ButtonStyle.blurple,
                 emoji='🔊',  row=0)
Button2 = Button(label='Vol: - 10', style=discord.ButtonStyle.blurple,
                 emoji='🔉',  row=0)
Button3 = Button(label="Vol: + 50", style=discord.ButtonStyle.blurple,
                 emoji='🔊',  row=0)
Button4 = Button(label='Vol: - 50', style=discord.ButtonStyle.blurple,
                 emoji='🔉',  row=0)
Button5 = Button(label='pause', style=discord.ButtonStyle.green,
                 emoji='⏸️', row=1)
Button6 = Button(label='clean', style=discord.ButtonStyle.red,
                 emoji='🧹', row=1)
Button7 = Button(label='next', style=discord.ButtonStyle.grey,
                 emoji='⏭️', row=1)
Button8 = Button(label='repeat', style=discord.ButtonStyle.grey, emoji='🔁',
                 row=2)
Button9 = Button(label='mix', style=discord.ButtonStyle.grey, emoji='🔀',
                 row=2)
# =============================================================================#


@bot.command()
async def join(ctx):
    if ctx.author.voice is None:
        await ctx.send("Вы не подключены к голосовому каналу!")
        return
    channel = ctx.author.voice.channel
    repeat_status[ctx.channel.id] = 0
    await channel.connect()


async def other(ctx, url, voice_client, channel_queue):
    if voice_client.is_playing():
        channel_queue.append(url)
        queue[ctx.channel.id] = channel_queue
        # queue.append(url)
        # Получите информацию о треках для текущего канала или создайте новую
        channel_track_inform = track_inform.get(ctx.channel.id, [])
        channel_track_inform.append(url)
        track_inform[ctx.channel.id] = channel_track_inform
        message = await ctx.channel.fetch_message(ctx.channel.last_message_id)
        await message.add_reaction("👍")
    else:
        message = await ctx.channel.fetch_message(ctx.channel.last_message_id)
        await message.add_reaction("👍")
        # Получите информацию о треках для текущего канала или создайте новую
        channel_track_inform = track_inform.get(ctx.channel.id, [])
        channel_track_inform.append(url)
        track_inform[ctx.channel.id] = channel_track_inform
        channel_queue.append(url)
        queue[ctx.channel.id] = channel_queue
        await info(ctx)
        await play_next(ctx, status=False)


async def album_yandex(ctx, url, voice_client, channel_queue):
    pattern = r'https://music\.yandex\.ru/album/(\d+)$'

    # Используем регулярное выражение для извлечения
    # идентификатора альбома из URL
    match = re.match(pattern, url)

    # Если URL соответствует шаблону, то выводим идентификатор альбома
    if match:
        message = await ctx.channel.fetch_message(ctx.channel.last_message_id)
        await message.add_reaction("🔥")
        album_id = match.group(1)
        client = ClientAsync(TOKEN_YANDEX)
        await client.init()

        album = await client.albums_with_tracks(album_id)

        del client

        track = []

        for i in album.volumes[0]:
            track.append(
                f"https://music.yandex.ru/album/{album_id}/track/{i['id']}")

        for i in track:
            if voice_client.is_playing():
                channel_queue.append(i)
                queue[ctx.channel.id] = channel_queue
                # queue.append(i)
                # Получите информацию о треках для текущего канала
                # или создайте новую
                channel_track_inform = track_inform.get(ctx.channel.id, [])
                channel_track_inform.append(i)
                track_inform[ctx.channel.id] = channel_track_inform
            else:
                # Получите информацию о треках для текущего канала
                # или создайте новую
                channel_track_inform = track_inform.get(ctx.channel.id, [])
                channel_track_inform.append(i)
                track_inform[ctx.channel.id] = channel_track_inform
                await play_track(ctx, i)
    else:
        ctx.send("Не верная ссылка на альбом.")


async def playlist_yandex(ctx, url, voice_client, channel_queue):
    pattern = r'https://music\.yandex\.ru/users/(.+)/playlists/(\d+)$'

    match = re.match(pattern, url)

    if match:
        message = await ctx.channel.fetch_message(ctx.channel.last_message_id)
        await message.add_reaction("❤️")
        username = match.group(1)
        playlist_id = match.group(2)

        client = ClientAsync(TOKEN_YANDEX)
        await client.init()

        playlist = await client.users_playlists(playlist_id, username)

        tracks = []

        for i in playlist.tracks:
            track = await client.tracks(i.id)
            data = track[0].track_id.split(':')
            tracks.append(
                f"https://music.yandex.ru/album/{data[1]}/track/{data[0]}")

        del client

        for i in tracks:
            if voice_client.is_playing():
                channel_queue.append(i)
                queue[ctx.channel.id] = channel_queue
                # queue.append(i)
                # Получите информацию о треках для текущего канала
                # или создайте новую
                channel_track_inform = track_inform.get(ctx.channel.id, [])
                channel_track_inform.append(i)
                track_inform[ctx.channel.id] = channel_track_inform
            else:
                # Получите информацию о треках для текущего канала
                # или создайте новую
                channel_track_inform = track_inform.get(ctx.channel.id, [])
                channel_track_inform.append(i)
                track_inform[ctx.channel.id] = channel_track_inform
                await play_track(ctx, i)

    else:
        ctx.send("Не верная ссылка на плейлист.")


async def playlist_youtube(ctx, url, voice_client, channel_queue):
    video_urls = []

    message = await ctx.channel.fetch_message(ctx.channel.last_message_id)
    await message.add_reaction("❤️‍🔥")

    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        if 'entries' in info_dict:
            video_info = info_dict['entries']
            for video in video_info:
                video_urls.append(
                    f'https://www.youtube.com/watch?v={video["id"]}')

    for i in video_urls:
        if voice_client.is_playing():
            channel_queue.append(i)
            queue[ctx.channel.id] = channel_queue
            # queue.append(i)
            # Получите информацию о треках для текущего канала
            # или создайте новую
            channel_track_inform = track_inform.get(ctx.channel.id, [])
            channel_track_inform.append(i)
            track_inform[ctx.channel.id] = channel_track_inform
        else:
            # Получите информацию о треках для текущего канала
            # или создайте новую
            channel_track_inform = track_inform.get(ctx.channel.id, [])
            channel_track_inform.append(i)
            track_inform[ctx.channel.id] = channel_track_inform
            await play_track(ctx, i)


@bot.command()
async def play(ctx, url):
    global playlist_change
    voice_client = ctx.guild.voice_client
    # Получите очередь для текущего канала или создайте новую
    channel_queue = queue.get(ctx.channel.id, [])
    pattern = r'https://music\.yandex\.ru/album/(\d+)$'
    pattern1 = r'https://music\.yandex\.ru/users/.+/playlists/\d+$'
    pattern2 = (
        r'(https?://)?(www\.)?(youtube\.com|youtu\.?be)'
        r'/playlist\?list=[^&]+'
    )

    playlist_change[ctx.channel.id] = True

    if re.match(pattern, url):
        await album_yandex(ctx, url, voice_client, channel_queue)
    elif re.match(pattern1, url):
        await playlist_yandex(ctx, url, voice_client, channel_queue)
    elif re.match(pattern2, url):
        await playlist_youtube(ctx, url, voice_client, channel_queue)
    else:
        await other(ctx, url, voice_client, channel_queue)


async def play_track(ctx, url):
    YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
    FFMPEG_OPTIONS = {
        'before_options':
            '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    try:
        volume = ctx.guild.voice_client.source.volume
    except Exception:
        volume = 1.0

    voice = get(bot.voice_clients, guild=ctx.guild)

    youtube_regex = r"(youtube\.com|youtu\.be)"
    yandex_regex = r"music\.yandex\.ru"

    if not voice.is_playing():
        if re.search(youtube_regex, url):
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
            URL = info['formats'][0]['url']
            voice.play(
                discord.PCMVolumeTransformer(
                    FFmpegPCMAudio(URL, **FFMPEG_OPTIONS)
                ),
                after=lambda e: asyncio.run(play_next(ctx)))
            voice.is_playing()
            ctx.guild.voice_client.source.volume = volume
        elif re.search(yandex_regex, url):
            match = re.search(r'/album/(\d+)/track/(\d+)', url)

            if match:
                album_id, track_id = match.groups()
                formatted_string = f"{track_id}:{album_id}"

                client = ClientAsync(TOKEN_YANDEX)
                await client.init()

                track = await client.tracks(formatted_string)

                try:
                    track = await client.tracks_download_info(
                        track[0].id, get_direct_links=True)
                    URL = track[0].direct_link
                except Exception as e:
                    await ctx.send(f"Ошибка при загрузке аудио: {e}")

                del client

                voice.play(
                    discord.PCMVolumeTransformer(
                        FFmpegPCMAudio(URL, **FFMPEG_OPTIONS)
                    ),
                    after=lambda e: asyncio.run(play_next(ctx)))
                voice.is_playing()
                ctx.guild.voice_client.source.volume = volume
            else:
                await ctx.send(
                    "Не удалось найти идентификаторы альбома и трека в URL")
    else:
        await ctx.send("Уже проигрывается песня")
        return


async def play_next(ctx, status=True):
    # Получите очередь для текущего канала
    global playlist_change
    try:
        channel_queue = queue[ctx.channel.id]
        channel_track = track_inform[ctx.channel.id]
        channel_playlist = information_track[ctx.channel.id]
        if len(channel_queue) > 0:
            if repeat_status[ctx.channel.id] == 0:
                if status:
                    channel_queue.pop(0)
                    channel_track.pop(0)
                    channel_playlist.pop(0)
                    next_track = channel_queue.pop(0)
                else:
                    next_track = channel_queue[0]
            elif repeat_status[ctx.channel.id] == 1:
                channel_queue.append(channel_queue.pop(0))
                channel_track.append(channel_track.pop(0))
                channel_playlist.append(channel_playlist.pop(0))
                next_track = channel_queue[0]
            elif repeat_status[ctx.channel.id] == 2:
                next_track = channel_queue[0]
            # Обновите очередь в словаре после удаления трека
            queue[ctx.channel.id] = channel_queue
            track_inform[ctx.channel.id] = channel_track
            information_track[ctx.channel.id] = channel_playlist
            playlist_change[ctx.channel.id] = False
            await play_track(ctx, next_track)
        else:
            pass
    except Exception:
        pass


async def info(ctx):

    youtube_regex = r"(youtube\.com|youtu\.be)"
    yandex_regex = r"music\.yandex\.ru"

    # Получите информацию о треках для текущего канала
    channel_track_inform = track_inform.get(ctx.channel.id, [])
    information = []
    if channel_track_inform != []:
        for url in channel_track_inform:
            if re.search(youtube_regex, url):
                yt = YouTube(url)
                information.append(f'{yt.title} - {yt.author}')
            elif re.search(yandex_regex, url):
                match = re.search(r'/album/(\d+)/track/(\d+)', url)

                if match:
                    album_id, track_id = match.groups()
                    formatted_string = f"{track_id}:{album_id}"

                    client = ClientAsync(TOKEN_YANDEX)
                    await client.init()

                    track = await client.tracks(formatted_string)

                    artists = []

                    for i in track[0].artists:
                        artists.append(i.name)
                    artist = ', '.join(artists)

                    del client
                    information.append(
                        f'{track[0].title} - {artist}')
    else:
        information.append("Not track in list")

    playlist_change[ctx.channel.id] = False

    information_track[ctx.channel.id] = information


@bot.command()
async def interface(ctx):
    global playlist_change
    global Button1, Button2, Button3, Button4, Button5, Button6, Button7, \
        Button8, Button9

    async def volume_plus_10(interaction):
        global playlist_change
        voice_client = interaction.guild.voice_client
        if (voice_client.source.volume + 0.1) <= 2.0:
            x = voice_client.source.volume + 0.1
            voice_client.source.volume = round(x, 1)
            # await interaction.response.send_message(
            #     voice_client.source.volume * 100)

            if playlist_change[interaction.channel.id]:
                await info(interaction)
            text = information_track[ctx.channel.id]
            text = '\n'.join(text)
            text += f'\n\nVol: \
{int(ctx.guild.voice_client.source.volume * 100)}'

            await interaction.message.edit(
                embed=discord.Embed(
                    description=text, color=discord.Color.red()), view=view)
            await interaction.response.defer()

    async def volume_minus_10(interaction):
        global playlist_change
        voice_client = interaction.guild.voice_client
        if (voice_client.source.volume - 0.1) >= 0.0:
            x = voice_client.source.volume - 0.1
            voice_client.source.volume = round(x, 1)
            # await interaction.response.send_message(
            #     voice_client.source.volume * 100)

            if playlist_change[interaction.channel.id]:
                await info(interaction)
            text = information_track[ctx.channel.id]
            text = '\n'.join(text)
            text += f'\n\nVol: \
{int(ctx.guild.voice_client.source.volume * 100)}'

            await interaction.message.edit(
                embed=discord.Embed(
                    description=text, color=discord.Color.red()), view=view)
            await interaction.response.defer()

    async def volume_plus_50(interaction):
        global playlist_change
        voice_client = interaction.guild.voice_client
        if (voice_client.source.volume + 0.5) <= 2.0:
            x = voice_client.source.volume + 0.5
            voice_client.source.volume = round(x, 1)
            # await interaction.response.send_message(
            #     voice_client.source.volume * 100)

            if playlist_change[interaction.channel.id]:
                await info(interaction)
            text = information_track[ctx.channel.id]
            text = '\n'.join(text)
            text += f'\n\nVol: \
{int(ctx.guild.voice_client.source.volume * 100)}'

            await interaction.message.edit(
                embed=discord.Embed(
                    description=text, color=discord.Color.red()), view=view)
            await interaction.response.defer()

    async def volume_minus_50(interaction):
        global playlist_change
        voice_client = interaction.guild.voice_client
        if (voice_client.source.volume - 0.5) >= 0.0:
            x = voice_client.source.volume - 0.5
            voice_client.source.volume = round(x, 1)
            # await interaction.response.send_message(
            #     voice_client.source.volume * 100)

            if playlist_change[interaction.channel.id]:
                await info(interaction)
            text = information_track[ctx.channel.id]
            text = '\n'.join(text)
            text += f'\n\nVol: \
{int(ctx.guild.voice_client.source.volume * 100)}'

            await interaction.message.edit(
                embed=discord.Embed(
                    description=text, color=discord.Color.red()), view=view)
            await interaction.response.defer()

    async def pause(interaction):
        global Button1, Button2, Button3, Button4, Button5, Button6, Button7, \
            Button8, Button9
        voice_client = interaction.guild.voice_client
        if interaction.message.components[1].children[0].emoji.name == '⏸️':
            Button5 = Button(label='resume', style=discord.ButtonStyle.green,
                             emoji='▶️', row=1)
            Button5.callback = pause

            view = View()
            view.add_item(Button3)
            view.add_item(Button1)
            view.add_item(Button2)
            view.add_item(Button4)
            view.add_item(Button5)
            view.add_item(Button6)
            view.add_item(Button7)
            view.add_item(Button8)
            view.add_item(Button9)

            await interaction.message.edit(view=view)
            if voice_client is None:
                await interaction.response.send_message(
                    "Я не подключен к голосовому каналу!")
                return
            if voice_client.is_playing():
                voice_client.pause()
                await interaction.response.defer()
        elif interaction.message.components[1].children[0].emoji.name == '▶️':
            Button5 = Button(label='pause', style=discord.ButtonStyle.green,
                             emoji='⏸️', row=1)
            Button5.callback = pause

            view = View()
            view.add_item(Button3)
            view.add_item(Button1)
            view.add_item(Button2)
            view.add_item(Button4)
            view.add_item(Button5)
            view.add_item(Button6)
            view.add_item(Button7)
            view.add_item(Button8)
            view.add_item(Button9)

            await interaction.message.edit(view=view)
            if voice_client is None:
                await interaction.response.send_message(
                    "Я не подключен к голосовому каналу!")
                return
            if voice_client.is_paused():
                voice_client.resume()
                await interaction.response.defer()

    async def next_track(interaction):
        voice_client = ctx.guild.voice_client
        if voice_client is not None:
            voice_client.stop()
            await interaction.response.defer()

    async def clean(interaction):
        global playlist_change
        global queue
        global track_inform
        queue[interaction.channel.id] = []
        track_inform[interaction.channel.id] = []
        information_track[interaction.channel.id] = ["Not track in list"]
        if playlist_change[interaction.channel.id]:
            await info(interaction)
        text = information_track[ctx.channel.id]
        text = '\n'.join(text)
        text += f'\n\nVol: \
{int(ctx.guild.voice_client.source.volume * 100)}'

        await interaction.message.edit(
            embed=discord.Embed(
                description=text, color=discord.Color.red()), view=view)
        await interaction.response.defer()

    async def repeat(interaction):
        global Button1, Button2, Button3, Button4, Button5, Button6, Button7, \
            Button8, Button9
        if (interaction.message.components[2].children[0].style.value == 2
           and interaction.message.components[2].children[0].emoji.name ==
           '🔁'):
            Button8 = Button(label='repeat', style=discord.ButtonStyle.green,
                             emoji='🔁', row=2)

            repeat_status[interaction.channel.id] = 1

        elif (interaction.message.components[2].children[0].style.value == 3
              and interaction.message.components[2].children[0].emoji.name ==
              '🔁'):
            Button8 = Button(label='repeat', style=discord.ButtonStyle.green,
                             emoji='🔂', row=2)

            repeat_status[interaction.channel.id] = 2

        elif (interaction.message.components[2].children[0].style.value == 3
              and interaction.message.components[2].children[0].emoji.name ==
              '🔂'):
            Button8 = Button(label='repeat', style=discord.ButtonStyle.grey,
                             emoji='🔁', row=2)

            repeat_status[interaction.channel.id] = 0

        Button8.callback = repeat

        view = View()
        view.add_item(Button3)
        view.add_item(Button1)
        view.add_item(Button2)
        view.add_item(Button4)
        view.add_item(Button5)
        view.add_item(Button6)
        view.add_item(Button7)
        view.add_item(Button8)
        view.add_item(Button9)

        await interaction.message.edit(view=view)
        await interaction.response.defer()

    async def mix(interaction):
        global Button1, Button2, Button3, Button4, Button5, Button6, Button7, \
            Button8, Button9

        channel_queue = queue[interaction.channel.id]
        channel_track = track_inform[interaction.channel.id]
        channel_playlist = information_track[interaction.channel.id]

        random_gen1 = random.Random(1)
        random_gen2 = random.Random(1)
        random_gen3 = random.Random(1)

        first_element1 = channel_queue[0]
        first_element2 = channel_track[0]
        first_element3 = channel_playlist[0]

        rest_of_list1 = channel_queue[1:]
        rest_of_list2 = channel_track[1:]
        rest_of_list3 = channel_playlist[1:]

        random_gen1.shuffle(rest_of_list1)
        random_gen2.shuffle(rest_of_list2)
        random_gen3.shuffle(rest_of_list3)

        # Возвращаем первые элементы на их места
        queue[interaction.channel.id] = [first_element1] + rest_of_list1
        track_inform[interaction.channel.id] = [first_element2] + rest_of_list2
        information_track[interaction.channel.id] = [first_element3] +\
            rest_of_list3

        if playlist_change[interaction.channel.id]:
            await info(interaction)
        text = information_track[interaction.channel.id]
        text = '\n'.join(text)
        text += f'\n\nVol: \
{int(ctx.guild.voice_client.source.volume * 100)}'

        view = View()
        view.add_item(Button3)
        view.add_item(Button1)
        view.add_item(Button2)
        view.add_item(Button4)
        view.add_item(Button5)
        view.add_item(Button6)
        view.add_item(Button7)
        view.add_item(Button8)
        view.add_item(Button9)

        await interaction.message.edit(
            embed=discord.Embed(
                description=text, color=discord.Color.red()), view=view)
        await interaction.response.defer()

    Button1.callback = volume_plus_10
    Button2.callback = volume_minus_10
    Button3.callback = volume_plus_50
    Button4.callback = volume_minus_50
    Button5.callback = pause
    Button6.callback = clean
    Button7.callback = next_track
    Button8.callback = repeat
    Button9.callback = mix

    view = View()
    view.add_item(Button3)
    view.add_item(Button1)
    view.add_item(Button2)
    view.add_item(Button4)
    view.add_item(Button5)
    view.add_item(Button6)
    view.add_item(Button7)
    view.add_item(Button8)
    view.add_item(Button9)

    if playlist_change[ctx.channel.id]:
        await info(ctx)
    text = information_track[ctx.channel.id]
    text = '\n'.join(text)
    text += f'\n\nVol: {int(ctx.guild.voice_client.source.volume * 100)}'
    await ctx.send(embed=discord.Embed(
        description=text, color=discord.Color.red()), view=view)

'''
@bot.command()
async def test(ctx):
    # Создаем кнопку с emoji
    button = Button(style=discord.ButtonStyle.blurple, label='Нажми меня',
                    emoji='👍')

    # Создаем функцию обратного вызова для кнопки
    async def callback(interaction):
        # Заменяем emoji в сообщении
        button = Button(style=discord.ButtonStyle.blurple, label='Нажми меня',
                        emoji='✅')
        button.callback = callback
        view = View()
        view.add_item(button)
        await message.edit(view=view)
        await interaction.response.send_message('Ok')

    button.callback = callback

    # Отправляем сообщение с кнопкой
    view = View()
    view.add_item(button)
    message = await ctx.send("Привет, это тестовое сообщение", view=view)


@bot.command()
async def volume(ctx, volume: int):
    voice_client = ctx.guild.voice_client
    if voice_client is None:
        await ctx.send("Я не подключен к голосовому каналу!")
        return
    if voice_client.source is None:
        await ctx.send("Сейчас ничего не воспроизводится!")
        return

    volume = max(min(volume, 200), 0)  # ограничиваем громкость от 0 до 200
    volume = volume / 100
    voice_client.source.volume = volume
'''


@bot.command()
async def leave(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client is None:
        await ctx.send("Я не подключен к голосовому каналу!")
        return
    await voice_client.disconnect()

bot.run(TOKEN)
