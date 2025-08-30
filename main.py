import os
import requests
import discord
from discord.ext import tasks
from dotenv import load_dotenv

# --- CONFIGURAÇÃO INICIAL ---
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
STEAM_API_KEY = os.getenv('STEAM_API_KEY')
NEWS_CHANNEL_ID = int(os.getenv('NEWS_CHANNEL_ID'))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

last_posted_title = [""]

# --- FUNÇÃO PARA BUSCAR NOTÍCIAS ---
def get_dota_news():
    """Busca a notícia mais recente do Dota 2 na API da Steam."""
    url = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"
    params = {
        "appid": 570,
        "count": 1,
        "maxlength": 500,
        "format": "json"
    }
    headers = {
        "x-webapi-key": STEAM_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        news_item = response.json()["appnews"]["newsitems"][0]
        return news_item
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a API da Steam: {e}")
        return None

# --- EVENTO ON_READY (QUANDO O BOT LIGA) ---
@client.event
async def on_ready():
    print(f'Login bem-sucedido como {client.user}')
    print('Iniciando a verificação de notícias...')
    check_news.start()

# --- LOOP DE VERIFICAÇÃO DE NOTÍCIAS ---
@tasks.loop(minutes=10)
async def check_news():
    print("Verificando por novas notícias do Dota 2...")
    news_item = get_dota_news()
    
    if news_item and news_item["title"] != last_posted_title[0]:
        print(f"Nova notícia encontrada: {news_item['title']}")
        last_posted_title[0] = news_item["title"]
        
        channel = client.get_channel(NEWS_CHANNEL_ID)
        
        if channel:
            embed = discord.Embed(
                title=news_item["title"],
                url=news_item["url"],
                description=news_item["contents"],
                color=discord.Color.red()
            )
            if "image" in news_item and news_item["image"]:
                embed.set_image(url=news_item["image"])
            
            # --- LINHA ALTERADA ---
            # Adicionamos o parâmetro 'content' para enviar a menção @everyone junto com o embed.
            await channel.send(content="@everyone", embed=embed)

            print("Notícia postada no Discord com sucesso!")
        else:
            print(f"ERRO: Canal com ID {NEWS_CHANNEL_ID} não encontrado.")
    else:
        print("Nenhuma notícia nova encontrada.")

# --- EVENTO ON_MESSAGE (PARA COMANDOS) ---
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('!ping'):
        await message.channel.send('Pong!')
    if message.content.startswith('!dotaverificar'):
        await message.channel.send("Ok, vou verificar se há notícias novas agora mesmo...")
        await check_news()


# --- INICIA O BOT ---
try:
    client.run(DISCORD_TOKEN)
except discord.errors.LoginFailure:
    print("ERRO: Token do Discord inválido.")
except Exception as e:
    print(f"Ocorreu um erro: {e}")