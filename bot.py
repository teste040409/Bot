import discord
from discord.ext import commands
import asyncio
import aiohttp
import os
import random
import re
import sys
import traceback

# ===================== LER TOKEN =====================
def ler_token():
    token = os.getenv('BOT_TOKEN')
    if token:
        token = token.strip()
        print(f"[OK] Token via variável de ambiente (tamanho: {len(token)})")
        return token
    
    if len(sys.argv) > 1:
        token = sys.argv[1].strip()
        if token:
            print(f"[OK] Token via argumento (tamanho: {len(token)})")
            return token
    
    try:
        with open('temp_token.txt', 'r', encoding='utf-8') as f:
            token = f.read().strip()
            if token:
                print(f"[OK] Token via arquivo (tamanho: {len(token)})")
                return token
    except:
        pass
    
    print("[ERRO] Token não encontrado!")
    return None

TOKEN = ler_token()

if not TOKEN:
    print("[ERRO] Token não encontrado!")
    sys.exit(1)

# ===================== CONFIGURACOES =====================
WEBHOOK_URL = "https://discord.com/api/webhooks/1503269462781202433/t3UawMFCz0D2hqOiu3K189pJFy_ARDYHrXxNLz9nMyBKKMA2WzwIUJnJASfzqSDmpcU-"
WEBHOOK_BAN_URL = "https://discord.com/api/webhooks/1503670255376142517/yzTCvchmHp7N6qUj6vvvc4DTkZScOctfR7PbN0fN59Z_YnijdLl7HjUbbCJ-zapV9Wtk"
WEBHOOK_DM_URL = "https://discord.com/api/webhooks/1503945925729718313/hbk_5duS9aKezW2FaHvBclxd2idBeaWqpObC93gczDPYEB79_jpWlGJtL6UlGPEy5QmH"
WEBHOOK_FILAS_ENCONTRADAS = "https://discord.com/api/webhooks/1505161479001735292/9vC9SVAZ5Im5X1e9ymTX7YP3Iu-9QBESo5PG1738jQZwlmuTk15YDUnjPczkkCfpt0mA"
WEBHOOK_AUTO = "https://ptb.discord.com/api/webhooks/1504305654305652776/PtxEPtSshrRuosSooZpp9ltKfwZhKSJUgsb7ETSU3t0Kb0rib3PenHzE-u8QMHqoK8V8"

GIF_URL = "https://i.pinimg.com/736x/58/34/57/583457c59980ab936e62c8c7012b952e.jpg"
PREFIX = "."

state = {
    "ativo": False,
    "auto_ciclo": False,
    "valor_aposta": 1,
    "msg_auto": "Opa menino meu celular deu erro aqui, ch4ma no pr1v",
    "povo_avisado": set(),
    "ultima_msg_fila_id": None
}

# ===================== CRIAR BOT =====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.messages = True
intents.dm_messages = True

# Cria o bot (self_bot=True funciona com intents na versão 2.x)
bot = commands.Bot(
    command_prefix=PREFIX, 
    self_bot=True,  # ← Funciona na 1.7.3
    help_command=None
)

clicados = set()
em_fila = set()
salas_detectadas_log = []
filas_entradas_log = []

CORES_RGB = ["\033[1;35m", "\033[1;36m", "\033[1;32m", "\033[1;33m", "\033[1;34m", "\033[1;37m"]
RED = "\033[1;31m"
RESET = "\033[0m"

# [RESTO DO SEU CÓDIGO IGUAL - MANTENHA TODAS AS FUNÇÕES]
# ... (mantenha tudo igual daqui pra baixo)

# ===================== FUNCOES =====================
async def atualizar_status_bot():
    """Atualiza o status do bot com o valor atual da aposta"""
    texto_status = f"Bet: R${state['valor_aposta']} - Mando fotinha"
    try:
        await bot.change_presence(
            activity=discord.Streaming(
                name=texto_status,
                url='https://www.twitch.tv/'
            )
        )
    except Exception as e:
        try:
            await bot.change_presence(
                activity=discord.Game(name=texto_status)
            )
        except:
            pass

async def log_discord(titulo, desc, target_webhook=WEBHOOK_URL, color=0x800080, thumbnail=None):
    embed = {
        "title": titulo,
        "description": desc,
        "color": color,
        "footer": {"text": "ASULA SUPREME V172 | RUSH APOSTA"}
    }
    if thumbnail:
        embed["thumbnail"] = {"url": thumbnail}
    async with aiohttp.ClientSession() as session:
        try:
            await session.post(target_webhook, json={"embeds": [embed]})
        except:
            pass

async def log_valor_alterado(novo_valor):
    embed = {
        "title": "VALOR DA APOSTA ALTERADO",
        "description": f"**Novo Valor:** R${novo_valor}\n**Modo:** {'Automatico (.5)' if state.get('auto_ciclo') else 'Manual'}",
        "color": 0xFFD700,
        "footer": {"text": "ASULA SUPREME V172"}
    }
    async with aiohttp.ClientSession() as session:
        try:
            await session.post(WEBHOOK_AUTO, json={"embeds": [embed]})
        except:
            pass

# ===================== CICLO .5 =====================
async def ciclo_auto():
    valores = [1, 2, 3, 5, 10]
    print("[INFO] Ciclo automatico iniciado!")
    
    while state["auto_ciclo"]:
        for valor in valores:
            if not state["auto_ciclo"]:
                print("[INFO] Ciclo automatico interrompido!")
                return
            
            print(f"[INFO] Alterando valor para R${valor}")
            state["valor_aposta"] = valor
            await atualizar_status_bot()
            await log_valor_alterado(valor)

            state["ativo"] = True
            clicados.clear()
            em_fila.clear()
            salas_detectadas_log.clear()
            filas_entradas_log.clear()
            
            bot.loop.create_task(cacar())
            
            print(f"[INFO] Aguardando 6 minutos com valor R${valor}...")
            await asyncio.sleep(6 * 60)
        
        if state["auto_ciclo"]:
            print("[INFO] Ciclo completo, aguardando 6 minutos...")
            await asyncio.sleep(6 * 60)

# ===================== CACAR =====================
async def cacar():
    print("[INFO] Iniciando busca por partidas...")
    contador = 0
    
    while state["ativo"]:
        try:
            for guild in bot.guilds:
                if not state["ativo"]: break
                for channel in guild.text_channels:
                    if not state["ativo"]: break
                    nome_canal = channel.name.lower()
                    if any(k in nome_canal for k in ['1x1','2x2','3v3','4x4','2v2','mob','mobile','emu','emulador']):
                        await analisar(channel)
                        await asyncio.sleep(0.01)
            
            contador += 1
            if contador % 10 == 0:
                print(f"[INFO] Buscando partidas... (ativo: {state['ativo']})")
                
        except Exception as e:
            pass
        
        await asyncio.sleep(1.2)

async def valor(message):
    texto = message.content or ""

    if message.embeds:
        for embed in message.embeds:
            if embed.title:
                texto += f"\n{embed.title}"
            if embed.description:
                texto += f"\n{embed.description}"
            if embed.fields:
                for field in embed.fields:
                    texto += f"\n{field.name}: {field.value}"

    valor_desejado = f"{state['valor_aposta']},00"
    match = re.search(rf"r\$\s*{re.escape(valor_desejado)}", texto, re.IGNORECASE)
    if not match:
        return None

    return valor_desejado

async def analisar(channel):
    try:
        async for m in channel.history(limit=5):
            if m.id in clicados: 
                continue
            
            if m.components:
                try:
                    valor_mensagem = await valor(m)
                except:
                    valor_mensagem = None

                if valor_mensagem is None:
                    continue

                for row in m.components:
                    for btn in row.children:
                        label = (btn.label or "").lower()
                        if any(x in label for x in ["entrar", "jogar", "participar", "confirmar"]) and channel.id not in em_fila:
                            print(f"[INFO] Clicando em botao em {channel.name} - Valor: {valor_mensagem}")
                            await asyncio.sleep(random.uniform(0.3, 0.8))
                            await btn.click()
                            clicados.add(m.id)
                            em_fila.add(channel.id)
                            print(f"[INFO] Clique realizado!")
                            return
    except Exception as e:
        pass

# ===================== EVENTOS =====================
@bot.event
async def on_ready():
    print("=" * 60)
    print("                    SELF-BOT V172 - SUPREME")
    print("=" * 60)
    print(f"[+] Conta Logada  : {bot.user}")
    print(f"[+] Servidores     : {len(bot.guilds)}")
    print(f"[+] Valor Aposta   : R${state['valor_aposta']}")
    print("=" * 60)
    print("[+] COMANDOS: .1 .2 .3 .4")
    print("[+] MODO .5 INICIADO AUTOMATICAMENTE!")
    print("=" * 60)

    # Log no webhook
    msg_on = f"""BOT V172 carregada com sucesso.
Conta: {bot.user}
Total de Servidores: {len(bot.guilds)}
Valor da Aposta: R${state['valor_aposta']}
MODO .5 AUTOMATICO INICIADO AUTOMATICAMENTE!"""

    try:
        await log_discord(
            "SISTEMA ONLINE",
            msg_on,
            target_webhook=WEBHOOK_URL,
            thumbnail=bot.user.display_avatar.url
        )
    except:
        pass

    # Atualizar status
    await atualizar_status_bot()

    # ===================== INICIAR MODO .5 AUTOMATICAMENTE =====================
    print("\n[OK] INICIANDO MODO .5 AUTOMATICO AUTOMATICAMENTE!")
    state["auto_ciclo"] = True
    bot.loop.create_task(ciclo_auto())

# ===================== COMANDOS =====================
@bot.command(name="1")
async def iniciar_v(ctx):
    state["ativo"] = True
    clicados.clear()
    em_fila.clear()
    bot.loop.create_task(cacar())
    try:
        await ctx.message.delete()
    except:
        pass

@bot.command(name="2")
async def parar_v(ctx):
    state["ativo"] = False
    state["auto_ciclo"] = False
    try:
        await ctx.message.delete()
    except:
        pass

@bot.command(name="3")
async def msg_v(ctx, *, texto):
    state["msg_auto"] = texto
    try:
        await ctx.message.delete()
    except:
        pass

@bot.command(name="4")
async def definir_valor(ctx, valor: int):
    if valor > 0:
        state["valor_aposta"] = valor
        await atualizar_status_bot()
        try:
            await ctx.message.delete()
        except:
            pass

@bot.event
async def on_message(message):
    if message.author.id == bot.user.id:
        await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"[ERRO] Comando falhou: {error}")

# ===================== INICIAR =====================
print("[OK] Iniciando self-bot...")

try:
    bot.run(TOKEN)
except Exception as e:
    print(f"[ERRO] Falha ao iniciar: {e}")
    sys.exit(1)
