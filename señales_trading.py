import time
import asyncio
from dataclasses import dataclass
from typing import Optional, Tuple, Dict
import numpy as np
import pandas as pd
import mplfinance as mpf
import ccxt
from telegram import Bot
from telegram.error import TelegramError
import os
import dotenv  # type: ignore
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# =========================
# CONFIG
# =========================
dotenv.load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TZ_ARG = ZoneInfo("America/Argentina/Rio_Gallegos")
HORA_INICIO = 6   
HORA_FIN = 22     
ultimo_reporte_fecha = None

# Configuración de Riesgo
MAX_OPERACIONES_SIMULTANEAS = 5  # <--- Límite de 5 activos a la vez
CHECK_EVERY_SECONDS = 20         # Escaneo más rápido para 150 monedas

SYMBOLS = ["BTC/USDT","ETH/USDT","BNB/USDT","XRP/USDT","SOL/USDT","ADA/USDT","DOGE/USDT","TRX/USDT","AVAX/USDT","DOT/USDT",
    "MATIC/USDT","LINK/USDT","LTC/USDT","BCH/USDT","XLM/USDT","ATOM/USDT","ICP/USDT","FIL/USDT","APT/USDT","ARB/USDT",
    "OP/USDT","NEAR/USDT","VET/USDT","HBAR/USDT","EGLD/USDT","XTZ/USDT","EOS/USDT","SAND/USDT","MANA/USDT","AAVE/USDT",
    "THETA/USDT","AXS/USDT","GRT/USDT","FLOW/USDT","KAVA/USDT","RUNE/USDT","CAKE/USDT","DYDX/USDT","PEPE/USDT","SHIB/USDT",
    "INJ/USDT","SEI/USDT","SUI/USDT","BLUR/USDT","LDO/USDT","STX/USDT","RNDR/USDT","FET/USDT","AGIX/USDT","OCEAN/USDT",
    "IMX/USDT","MINA/USDT","ROSE/USDT","ZEC/USDT","XMR/USDT","KSM/USDT","ENS/USDT","GLMR/USDT","CFX/USDT","WOO/USDT",
    "CHZ/USDT","1INCH/USDT","COMP/USDT","SNX/USDT","CRV/USDT","BAL/USDT","YFI/USDT","GMX/USDT","CVX/USDT","FXS/USDT",
    "ILV/USDT","CELO/USDT","ANKR/USDT","ZIL/USDT","QTUM/USDT","OMG/USDT","BAND/USDT","SKL/USDT","ICX/USDT","HOT/USDT",
    "DASH/USDT","IOST/USDT","ONT/USDT","WAVES/USDT","KLAY/USDT","CSPR/USDT","FLUX/USDT","LRC/USDT","RSR/USDT","REEF/USDT",
    "ALGO/USDT","HNT/USDT","ZEN/USDT","SC/USDT","AR/USDT","KDA/USDT","CKB/USDT","XNO/USDT","BTG/USDT","DCR/USDT",
    "RVN/USDT","NEXO/USDT","TWT/USDT","OKB/USDT","GT/USDT","BGB/USDT","HT/USDT","MX/USDT","LEO/USDT","FLOKI/USDT",
    "BONK/USDT","WIF/USDT","MEME/USDT","ORDI/USDT","PYTH/USDT","TIA/USDT","JTO/USDT","STRK/USDT","ALT/USDT","PIXEL/USDT",
    "ACE/USDT","PORTAL/USDT","AI/USDT","NFP/USDT","GALA/USDT","ENJ/USDT","WAXP/USDT","BORA/USDT","COTI/USDT","DGB/USDT",
    "STORJ/USDT","SXP/USDT","PERP/USDT","LIT/USDT","TRB/USDT","API3/USDT","PLA/USDT","IDEX/USDT","ALICE/USDT","TLM/USDT",
    "MBL/USDT","NKN/USDT","DODO/USDT","MDT/USDT","CTSI/USDT","ARPA/USDT","ATA/USDT","PROM/USDT","OGN/USDT","FORTH/USDT",
    "RAD/USDT","BADGER/USDT","MLN/USDT","SUPER/USDT","UOS/USDT","TVK/USDT","POND/USDT","ERN/USDT","GHST/USDT","AUDIO/USDT",
    "RLC/USDT","NUM/USDT","CLV/USDT","PHA/USDT","RARE/USDT","MOVR/USDT","ASTR/USDT","SD/USDT","KEEP/USDT","T/USDT",
    "MASK/USDT","REQ/USDT","FARM/USDT","QUICK/USDT","KP3R/USDT","BIFI/USDT","AUTO/USDT","DF/USDT","JASMY/USDT","ELF/USDT",
    "WRX/USDT","BNT/USDT","STMX/USDT","AKRO/USDT","HARD/USDT","FIRO/USDT","SYS/USDT","STRAX/USDT","NULS/USDT","PIVX/USDT",
    "ARK/USDT","FUN/USDT","DENT/USDT","WIN/USDT","TKO/USDT","ALPHA/USDT","PSG/USDT","CITY/USDT","LAZIO/USDT","PORTO/USDT",
    "SANTOS/USDT","ATM/USDT","ASR/USDT","JUV/USDT","BAR/USDT","ACM/USDT","INTER/USDT","NAP/USDT","ALPINE/USDT","GAL/USDT",
    "HOOK/USDT","EDU/USDT","ID/USDT","ARKM/USDT","CYBER/USDT","XAI/USDT","MAV/USDT","AUCTION/USDT","SSV/USDT","PENDLE/USDT",
    "MAGIC/USDT","RDNT/USDT","SYN/USDT","LQTY/USDT","HIFI/USDT","BETA/USDT","ALCX/USDT"]

TIMEFRAME = "5m"
LIMIT = 320
COOLDOWN_MINUTES = 60
ENTRY_WINDOW_PCT = 0.003

OPEN_TRADES_FILE = "open_trades.json"
HISTORY_CSV = "trade_history.csv"

@dataclass
class Signal:
    side: str
    entry: float
    sl: float
    tp: float
    probability: float
    trigger: str
    reason: str
    timestamp_ms: int

# =========================
# HELPERS
# =========================
def _utc_now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

def load_open_trades() -> dict:
    if not os.path.exists(OPEN_TRADES_FILE): return {}
    try:
        with open(OPEN_TRADES_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def save_open_trades(open_trades: dict) -> None:
    with open(OPEN_TRADES_FILE, "w", encoding="utf-8") as f:
        json.dump(open_trades, f, ensure_ascii=False, indent=2)

def append_history_row(row: dict) -> None:
    header = ["closed_at_utc", "symbol", "side", "entry", "sl", "tp", "result", "pnl_pct", "probability", "trigger"]
    file_exists = os.path.exists(HISTORY_CSV)
    with open(HISTORY_CSV, "a", encoding="utf-8") as f:
        if not file_exists: f.write(",".join(header) + "\n")
        f.write(",".join(str(row.get(k, "")) for k in header) + "\n")

# =========================
# LÓGICA DE ULTRA-PRECISIÓN
# =========================
def generate_signal(df: pd.DataFrame) -> Optional[Signal]:
    if len(df) < 210: return None
    df = df.copy()
    df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()
    df["sma20"] = df["close"].rolling(window=20).mean()
    df["std"] = df["close"].rolling(window=20).std()
    df["upper"] = df["sma20"] + (2.5 * df["std"])
    df["lower"] = df["sma20"] - (2.5 * df["std"])

    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
    df["rsi"] = 100 - (100 / (1 + (gain / loss)))

    curr = df.iloc[-1]
    body = abs(curr["close"] - curr["open"])
    lower_wick = min(curr["open"], curr["close"]) - curr["low"]
    upper_wick = curr["high"] - max(curr["open"], curr["close"])
    
    side, prob = None, 0.0

    if curr["close"] > curr["ema200"]:
        if curr["low"] < curr["lower"] and curr["rsi"] < 18:
            if lower_wick > (body * 2):
                side, prob = "BUY", 92.0
                entry = curr["close"]
                tp, sl = entry * 1.008, entry * 0.980

    elif curr["close"] < curr["ema200"]:
        if curr["high"] > curr["upper"] and curr["rsi"] > 82:
            if upper_wick > (body * 2):
                side, prob = "SELL", 92.0
                entry = curr["close"]
                tp, sl = entry * 0.992, entry * 1.020

    if side:
        return Signal(side=side, entry=entry, sl=sl, tp=tp, probability=prob,
                      trigger="ULTRA_PRECISION", reason="Trend+Extremes+WickRejection",
                      timestamp_ms=int(curr["timestamp"].timestamp() * 1000))
    return None

# =========================
# EXCHANGE & TOOLS
# =========================
def build_exchange():
    ex = ccxt.binanceusdm({"enableRateLimit": True})
    ex.load_markets()
    return ex

def normalize_symbol(ex: ccxt.Exchange, s: str) -> str:
    if ":" in s: return s
    base_quote = s.split("/")
    if len(base_quote) == 2:
        futures_style = f"{base_quote[0]}/{base_quote[1]}:{base_quote[1]}"
        if futures_style in ex.symbols: return futures_style
    return s

def fetch_ohlcv(exchange: ccxt.Exchange, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df

def render_chart(df: pd.DataFrame, signal: Signal, symbol: str, out_path: str) -> str:
    df_c = df.dropna().tail(80).copy()
    df_c.set_index("timestamp", inplace=True)
    ap = [
        mpf.make_addplot([signal.entry] * len(df_c), color="cyan", linestyle="--"),
        mpf.make_addplot([signal.sl] * len(df_c), color="red", width=0.8),
        mpf.make_addplot([signal.tp] * len(df_c), color="green", width=0.8)
    ]
    mpf.plot(df_c, type="candle", style="binance", addplot=ap, savefig=out_path, tight_layout=True)
    return out_path

async def send_telegram(bot: Bot, signal: Signal, chart_path: str, symbol: str, cupos_info: str) -> None:
    msg = (f"🎯 **SEÑAL DE ALTA PRECISIÓN**\n{cupos_info}\n\n"
           f"📊 Activo: {symbol}\n🟦 Operación: {signal.side}\n"
           f"💰 Entrada: {signal.entry:.6f}\n✅ TP: {signal.tp:.6f} (+0.80%)\n"
           f"🛑 SL: {signal.sl:.6f} (-2.00%)\n⚡ Confianza: {signal.probability}%")
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode="Markdown")
    with open(chart_path, "rb") as f: await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=f)

async def track_open_trades(exchange: ccxt.Exchange, bot: Bot, open_trades: dict) -> None:
    if not open_trades: return
    to_close = []
    cambio_en_json = False # Bandera para saber si guardar cambios

    for symbol, t in list(open_trades.items()):
        try:
            ticker = exchange.fetch_ticker(symbol)
            curr_p = ticker["last"]
            
            # --- CORRECCIÓN AQUÍ: Evitar el bucle de spam ---
            if t.get("status") == "OPEN":
                diff = (curr_p - t["entry"]) / t["entry"]
                
                # Si se escapa la zona, avisamos UNA SOLA VEZ y cambiamos el status
                if (t["side"] == "BUY" and diff > ENTRY_WINDOW_PCT) or (t["side"] == "SELL" and diff < -ENTRY_WINDOW_PCT):
                    try:
                        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"⚠️ {symbol}: ZONA SUPERADA. No entrar.")
                    except: pass
                    
                    open_trades[symbol]["status"] = "EXPIRED" # Cambiamos status para que no entre más aquí
                    cambio_en_json = True 

            # Lógica de TP y SL (Sigue igual)
            hit = None
            if t["side"] == "BUY":
                if curr_p <= t["sl"]: hit = "SL"
                elif curr_p >= t["tp"]: hit = "TP"
            else:
                if curr_p >= t["sl"]: hit = "SL"
                elif curr_p <= t["tp"]: hit = "TP"

            if hit:
                pnl = 0.8 if hit == "TP" else -2.0
                append_history_row({
                    "closed_at_utc": _utc_now_str(), "symbol": symbol, "side": t["side"],
                    "entry": t["entry"], "sl": t["sl"], "tp": t["tp"], "result": hit,
                    "pnl_pct": pnl, "probability": 92.0, "trigger": "ULTRA"
                })
                to_close.append(symbol)
                await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"🏁 **{symbol} Cerrado en {hit}** ({pnl}%)")
                cambio_en_json = True
        except: pass

    # Limpiar cerrados
    for s in to_close:
        if s in open_trades:
            open_trades.pop(s)
            cambio_en_json = True

    # Guardar solo si hubo cambios reales (Cierre o Expiración)
    if cambio_en_json:
        save_open_trades(open_trades)

async def enviar_reporte_diario(bot: Bot):
    if not os.path.exists(HISTORY_CSV): return
    try:
        df_h = pd.read_csv(HISTORY_CSV)
        df_h["closed_at_utc_dt"] = pd.to_datetime(df_h["closed_at_utc"].str.replace(" UTC", ""), utc=True)
        df_h["fecha_arg"] = df_h["closed_at_utc_dt"].dt.tz_convert(TZ_ARG).dt.date
        hoy_arg = datetime.now(TZ_ARG).date()
        df_hoy = df_h[df_h["fecha_arg"] == hoy_arg]
        if not df_hoy.empty:
            total, wins = len(df_hoy), len(df_hoy[df_hoy["result"] == "TP"])
            pnl = df_hoy["pnl_pct"].sum()
            msg = (f"📝 **REPORTE DIARIO ({hoy_arg})**\n\n✅ Ganadas: {wins}\n❌ Perdidas: {total-wins}\n"
                   f"📈 Winrate: {(wins/total*100):.1f}%\n💰 PnL Total: {pnl:.2f}%")
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode="Markdown")
    except Exception as e: print(f"Error reporte: {e}")

# =========================
# MAIN
# =========================
async def main():
    global ultimo_reporte_fecha
    exchange = build_exchange()
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"🚀 Bot francotirador iniciado (Límite: {MAX_OPERACIONES_SIMULTANEAS} activos)")
    
    symbols_ok = [normalize_symbol(exchange, s) for s in SYMBOLS if normalize_symbol(exchange, s) in exchange.symbols]
    last_sent_ts = {}
    
    while True:
        ahora_arg = datetime.now(TZ_ARG)
        hora, fecha_hoy = ahora_arg.hour, ahora_arg.date()
        open_trades = load_open_trades()

        await track_open_trades(exchange, bot, open_trades)

        if HORA_INICIO <= hora < HORA_FIN:
            cantidad_abiertas = len(open_trades)
            if cantidad_abiertas < MAX_OPERACIONES_SIMULTANEAS:
                print(f"[{ahora_arg.strftime('%H:%M:%S')}] Escaneando... ({cantidad_abiertas}/{MAX_OPERACIONES_SIMULTANEAS})")
                for symbol in symbols_ok:
                    if len(open_trades) >= MAX_OPERACIONES_SIMULTANEAS: break
                    try:
                        df = fetch_ohlcv(exchange, symbol, TIMEFRAME, 250)
                        signal = generate_signal(df)
                        if signal:
                            now_t = time.time()
                            if (now_t - last_sent_ts.get(symbol, 0)) > COOLDOWN_MINUTES * 60:
                                path = f"chart_{symbol.replace('/', '_').replace(':', '_')}.png"
                                render_chart(df, signal, symbol, path)
                                
                                # Info de cupos para el mensaje
                                info_cupos = f"📌 Cupos: {len(open_trades) + 1}/{MAX_OPERACIONES_SIMULTANEAS}"
                                await send_telegram(bot, signal, path, symbol, info_cupos)
                                
                                last_sent_ts[symbol] = now_t
                                open_trades[symbol] = {"side": signal.side, "entry": signal.entry, "tp": signal.tp, "sl": signal.sl, "status": "OPEN"}
                                save_open_trades(open_trades)
                    except: pass
            else:
                if ahora_arg.second % 60 < 20: print(f"⚠️ Límite alcanzado ({MAX_OPERACIONES_SIMULTANEAS}/5).")

        elif hora >= HORA_FIN and ultimo_reporte_fecha != fecha_hoy:
            await enviar_reporte_diario(bot)
            ultimo_reporte_fecha = fecha_hoy

        await asyncio.sleep(CHECK_EVERY_SECONDS)

if __name__ == "__main__":
    asyncio.run(main())