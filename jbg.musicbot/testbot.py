import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv
import os
import yt_dlp
import random

# .env 파일에서 환경 변수를 로드합니다
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')  # 환경 변수 이름 확인 (대소문자 주의)

# FFmpeg 경로 설정
FFMPEG_PATH = r'C:\Program Files\FFmpeg\ffmpeg\bin\ffmpeg.exe'

# 봇 생성
intents = discord.Intents.default()
intents.message_content = True  # 메시지 콘텐츠 인텐트 활성화
bot = commands.Bot(command_prefix='!', intents=intents)

# 재생 대기열을 저장할 딕셔너리
queues = {}

# 대화 응답 사전
responses = {
    "안녕": ["안녕하세요! 선생님!", "반가워요 선생님!!"],
    "잘 지내?": ["아리스는 항상 잘 지내요! 선생님은요?!"],
    "고마워": ["천만에요!", "별 말씀을요!"],
    "뭐해?": ["선생님을 기다리고 있었어요!!", "아리스는 혼자 대기 중이었어요.."]
}

# 음성 채널에 들어가기 위한 함수
async def join_voice_channel(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_connected():
        await ctx.send("이미 음성 채널에 연결되어 있습니다.")
        return

    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()  # 음성 채널에 연결
        await ctx.send(f"{channel.name} 아리스 채널에 들어왔습니다!")
    else:
        await ctx.send("아리스 음성 채널에 먼저 들어가야 해요..")

# 음성 채널에서 나가기 위한 함수
async def leave_voice_channel(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await ctx.send("아리스가 음성 채널에서 나갔습니다.")
    else:
        await ctx.send("아리스는 현재 음성 채널에 연결되어 있지 않아요.")

# 오디오 다운로드 함수
async def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist': True
    }

    ydl = yt_dlp.YoutubeDL(ydl_opts)
    info = ydl.extract_info(url, download=True)
    return f"{info['title']}.mp3"

# 재생 대기열 관리 함수
def add_to_queue(ctx, filename):
    guild_id = ctx.guild.id
    if guild_id not in queues:
        queues[guild_id] = []
    queues[guild_id].append(filename)

async def play_next(ctx):
    guild_id = ctx.guild.id
    voice_client = ctx.voice_client

    if guild_id in queues and queues[guild_id]:
        next_song = queues[guild_id].pop(0)
        voice_client.play(discord.FFmpegPCMAudio(next_song, executable=FFMPEG_PATH),
                          after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
    else:
        await ctx.send("재생할 다음 곡이 없어요 선생님.. 대기열을 확인해주세요..")

# URL로 재생 명령어
@bot.command(name='재생')
async def 재생(ctx, url: str):
    voice_client = ctx.voice_client

    if not voice_client:
        await ctx.send("아리스가 음성 채널에 들어가야 해요.")
        return

    filename = await download_audio(url)
    if filename is None:
        await ctx.send("아리스 오디오를 다운로드하는 데 실패했어요.")
        return

    add_to_queue(ctx, filename)

    if not voice_client.is_playing():
        await play_next(ctx)

# 스킵 명령어
@bot.command(name='스킵')
async def 스킵(ctx):
    voice_client = ctx.voice_client

    if not voice_client or not voice_client.is_playing():
        await ctx.send("현재 재생 중인 곡이 없어요 선생님..")
        return

    voice_client.stop()
    await ctx.send("현재 곡을 스킵했습니다 선생님!")
    await play_next(ctx)

# "아리스" 단어 감지
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if "아리스" in message.content:
        ctx = await bot.get_context(message)
        voice_client = ctx.guild.voice_client
        if not voice_client or not voice_client.is_connected():
            if ctx.author.voice:
                await join_voice_channel(ctx)

    for key in responses:
        if key in message.content:
            response = random.choice(responses[key])
            await message.channel.send(response)
            break

    await bot.process_commands(message)

# 봇이 음성 채널에서 나가기 위한 명령어
@bot.command(name='나가기')
async def 나가기(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await ctx.send("아리스가 음성 채널에서 나갔습니다.")
    else:
        await ctx.send("아리스는 현재 음성 채널에 연결되어 있지 않아요.")

@bot.event
async def on_ready():
    print(f'로그인 완료: {bot.user.name}')

# 봇 실행
bot.run(TOKEN)  # TOKEN을 여기에서 사용하세요
