import discord
from discord.ext import commands
from dotenv.main import load_dotenv
import os
from discord.ui import View, Button
from discord.utils import get
from discord import FFmpegPCMAudio
from youtube_dl import YoutubeDL
from pytube import YouTube

load_dotenv()

TOKEN = os.environ['TOKEN']

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

queue = {}
track_inform = {}


@bot.command()
async def join(ctx):
    if ctx.author.voice is None:
        await ctx.send("Вы не подключены к голосовому каналу!")
        return
    channel = ctx.author.voice.channel
    await channel.connect()


@bot.command()
async def play(ctx, url):
    voice_client = ctx.guild.voice_client
    # Получите очередь для текущего канала или создайте новую
    channel_queue = queue.get(ctx.channel.id, [])
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
        play_track(ctx, url)


def play_track(ctx, url):
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

    if not voice.is_playing():
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
        URL = info['formats'][0]['url']
        voice.play(
            discord.PCMVolumeTransformer(
                FFmpegPCMAudio(URL, **FFMPEG_OPTIONS)
            ),
            after=lambda e: play_next(ctx))
        voice.is_playing()
        ctx.guild.voice_client.source.volume = volume
    else:
        ctx.send("Уже проигрывается песня")
        return


def play_next(ctx):
    # Получите очередь для текущего канала
    try:
        channel_queue = queue[ctx.channel.id]
        channel_track = track_inform[ctx.channel.id]
        if len(channel_queue) > 0:
            next_track = channel_queue.pop(0)
            channel_track.pop(0)
            # Обновите очередь в словаре после удаления трека
            queue[ctx.channel.id] = channel_queue
            track_inform[ctx.channel.id] = channel_track
            play_track(ctx, next_track)
        else:
            channel_track.pop(0)
            track_inform[ctx.channel.id] = channel_track
    except Exception:
        pass


async def info(ctx):
    # Получите информацию о треках для текущего канала
    channel_track_inform = track_inform.get(ctx.channel.id, [])
    information = []
    if channel_track_inform != []:
        for x, url in enumerate(channel_track_inform):
            yt = YouTube(url)
            information.append(f'#{x+1}: {yt.title} - {yt.author}')
    else:
        information.append("Not track in list")

    return information


@bot.command()
async def interface(ctx):
    Button1 = Button(label="Vol: + 10", style=discord.ButtonStyle.blurple,
                     row=0)
    Button2 = Button(label='Vol: - 10', style=discord.ButtonStyle.blurple,
                     row=0)
    Button3 = Button(label="Vol: + 50", style=discord.ButtonStyle.blurple,
                     row=0)
    Button4 = Button(label='Vol: - 50', style=discord.ButtonStyle.blurple,
                     row=0)
    Button5 = Button(label='pause', style=discord.ButtonStyle.green,
                     emoji='⏸️', row=1)
    Button7 = Button(label='next', style=discord.ButtonStyle.grey, row=1)
    Button6 = Button(label='clean', style=discord.ButtonStyle.red, row=1)

    async def volume_plus_10(interaction):
        voice_client = interaction.guild.voice_client
        if (voice_client.source.volume + 0.1) <= 2.0:
            x = voice_client.source.volume + 0.1
            voice_client.source.volume = round(x, 1)
            # await interaction.response.send_message(
            #     voice_client.source.volume * 100)

            text = await info(interaction)
            text = '\n'.join(text)
            text += f'\n\nVol: \
{int(ctx.guild.voice_client.source.volume * 100)}'

            await interaction.message.edit(
                embed=discord.Embed(
                    description=text, color=discord.Color.red()), view=view)
            await interaction.response.defer()

    async def volume_minus_10(interaction):
        voice_client = interaction.guild.voice_client
        if (voice_client.source.volume - 0.1) >= 0.0:
            x = voice_client.source.volume - 0.1
            voice_client.source.volume = round(x, 1)
            # await interaction.response.send_message(
            #     voice_client.source.volume * 100)

            text = await info(interaction)
            text = '\n'.join(text)
            text += f'\n\nVol: \
{int(ctx.guild.voice_client.source.volume * 100)}'

            await interaction.message.edit(
                embed=discord.Embed(
                    description=text, color=discord.Color.red()), view=view)
            await interaction.response.defer()

    async def volume_plus_50(interaction):
        voice_client = interaction.guild.voice_client
        if (voice_client.source.volume + 0.5) <= 2.0:
            x = voice_client.source.volume + 0.5
            voice_client.source.volume = round(x, 1)
            # await interaction.response.send_message(
            #     voice_client.source.volume * 100)

            text = await info(interaction)
            text = '\n'.join(text)
            text += f'\n\nVol: \
{int(ctx.guild.voice_client.source.volume * 100)}'

            await interaction.message.edit(
                embed=discord.Embed(
                    description=text, color=discord.Color.red()), view=view)
            await interaction.response.defer()

    async def volume_minus_50(interaction):
        voice_client = interaction.guild.voice_client
        if (voice_client.source.volume - 0.5) >= 0.0:
            x = voice_client.source.volume - 0.5
            voice_client.source.volume = round(x, 1)
            # await interaction.response.send_message(
            #     voice_client.source.volume * 100)

            text = await info(interaction)
            text = '\n'.join(text)
            text += f'\n\nVol: \
{int(ctx.guild.voice_client.source.volume * 100)}'

            await interaction.message.edit(
                embed=discord.Embed(
                    description=text, color=discord.Color.red()), view=view)
            await interaction.response.defer()

    async def pause(interaction):
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
            view.add_item(Button7)
            view.add_item(Button6)

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
            view.add_item(Button7)
            view.add_item(Button6)

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
        global queue
        global track_inform
        queue = {}
        track_inform = {}
        text = await info(interaction)
        text = '\n'.join(text)
        text += f'\n\nVol: \
{int(ctx.guild.voice_client.source.volume * 100)}'

        await interaction.message.edit(
            embed=discord.Embed(
                description=text, color=discord.Color.red()), view=view)
        await interaction.response.defer()

    Button1.callback = volume_plus_10
    Button2.callback = volume_minus_10
    Button3.callback = volume_plus_50
    Button4.callback = volume_minus_50
    Button5.callback = pause
    Button7.callback = next_track
    Button6.callback = clean

    view = View()
    view.add_item(Button3)
    view.add_item(Button1)
    view.add_item(Button2)
    view.add_item(Button4)
    view.add_item(Button5)
    view.add_item(Button7)
    view.add_item(Button6)
    text = await info(ctx)
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
