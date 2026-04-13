import discord
import asyncio
import re
from flask import Flask, jsonify
from threading import Thread

# =============================================
#  CONFIGURAÇÕES — edite aqui
# =============================================
DISCORD_TOKEN = "MTQ5MzM0NjE0Njg3NjI2NDQ1OA.GcWyGp.zDNzwbHhdWN64HTrokpCRO26aMxbmpm8rLCFeg"
CHANNEL_ID    = 123456789012345678   # ID do canal onde as keys são postadas
API_PORT      = 8080
# =============================================

app   = Flask(__name__)
bot   = discord.Client(intents=discord.Intents.all())

# Padrão de key: GAC-XXX-VXX-XXX-XXX (letras e números)
KEY_PATTERN = re.compile(r"GAC-[A-Z0-9]{3}-V\d[A-Z0-9]*-[A-Z0-9]{3}-[A-Z0-9]{3}", re.IGNORECASE)

valid_keys: set[str] = set()


# ──────────────────────────────────────────
#  BOT — carrega histórico + escuta novas msgs
# ──────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"[GAC Bot] Logado como {bot.user}")
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        # Lê todas as mensagens históricas do canal
        async for msg in channel.history(limit=None):
            for key in KEY_PATTERN.findall(msg.content.upper()):
                valid_keys.add(key)
        print(f"[GAC Bot] {len(valid_keys)} keys carregadas do histórico.")
    else:
        print("[GAC Bot] ERRO: Canal não encontrado. Verifique o CHANNEL_ID.")


@bot.event
async def on_message(message: discord.Message):
    if message.channel.id != CHANNEL_ID:
        return
    for key in KEY_PATTERN.findall(message.content.upper()):
        valid_keys.add(key)
        print(f"[GAC Bot] Nova key registrada: {key}")


# ──────────────────────────────────────────
#  API — endpoint consultado pelo Roblox
# ──────────────────────────────────────────
@app.route("/validate/<key>", methods=["GET"])
def validate(key: str):
    key = key.upper().strip()
    if not KEY_PATTERN.fullmatch(key):
        return jsonify({"valid": False, "reason": "Formato inválido"}), 400

    if key in valid_keys:
        return jsonify({"valid": True,  "key": key}), 200
    else:
        return jsonify({"valid": False, "reason": "Key não encontrada"}), 404


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "online", "keys_loaded": len(valid_keys)}), 200


# ──────────────────────────────────────────
#  Inicia Flask numa thread separada
# ──────────────────────────────────────────
def run_flask():
    app.run(host="0.0.0.0", port=API_PORT)


if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    print(f"[GAC API] Rodando na porta {API_PORT}")
    bot.run(DISCORD_TOKEN)
