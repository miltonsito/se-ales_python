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
from dotenv import load_dotenv
import json
from datetime import datetime, timezone

# =========================
# CONFIG
# =========================

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 20 Monedas con más volumen para mayor precisión
SYMBOLS = [
    "BTC/USDT","ETH/USDT","BNB/USDT","XRP/USDT","SOL/USDT","ADA/USDT","DOGE/USDT","TRX/USDT","AVAX/USDT","DOT/USDT",
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
"MAGIC/USDT","RDNT/USDT","SYN/USDT","LQTY/USDT","HIFI/USDT","BETA/USDT","ALCX/USDT"
]

TIMEFRAME = "5m"
LIMIT = 320
CHECK_EVERY_SECONDS = 30 

# Parámetros Estrategia
RSI_PERIOD = 7
BB_PERIOD = 20
BB_STD = 2.0

# --- FILTROS DE CALIDAD ---
COOLDOWN_MINUTES = 60         
EMA_TREND_PERIOD = 200       
ENTRY_WINDOW_PCT = 0.003     # 0.3% máximo para avisar que ya pasó la entrada

# Tracker Archivos
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
    header = ["closed_at_utc", "symbol", "side", "entry", "sl", "tp", "result", "pnl_pct", "probability", "trigger", "opened_at_utc"]
    file_exists = os.path.exists(HISTORY_CSV)
    with open(HISTORY_CSV, "a", encoding="utf-8") as f:
        if not file_exists: f.write(",".join(header) + "\n")
        f.write(",".join(str(row.get(k, "")) for k in header) + "\n")

def compute_winrate() -> tuple[int, int, float]:
    if not os.path.exists(HISTORY_CSV): return 0, 0, 0.0
    try:
        df_h = pd.read_csv(HISTORY_CSV)
        total = len(df_h)
        wins = len(df_h[df_h['result'] == 'TP'])
        return wins, total, (wins/total*100) if total > 0 else 0.0
    except: return 0, 0, 0.0

# =========================
# LÓGICA DE SEÑALES
# =========================
def generate_signal(df: pd.DataFrame) -> Optional[Signal]:
    if len(df) < 210: return None
    df = df.copy()
    
    # 1. Indicadores Avanzados
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['avg_vol'] = df['volume'].rolling(window=10).mean()
    
    # Bandas de Bollinger
    df['sma20'] = df['close'].rolling(window=20).mean()
    df['std'] = df['close'].rolling(window=20).std()
    df['upper'] = df['sma20'] + (2.0 * df['std'])
    df['lower'] = df['sma20'] - (2.0 * df['std'])
    
    # RSI 7
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
    df['rsi'] = 100 - (100 / (1 + (gain / loss)))

    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    side, prob = None, 70.0
    
    # --- LÓGICA DE VELAS (Price Action) ---
    body = abs(curr['close'] - curr['open'])
    lower_wick = min(curr['open'], curr['close']) - curr['low']
    upper_wick = curr['high'] - max(curr['open'], curr['close'])
    
    # --- FILTRO 1: VOLUMEN (Debe haber interés real) ---
    vol_confirmation = curr['volume'] > (df['avg_vol'].iloc[-1] * 1.1)

    # --- SEÑAL DE COMPRA (LONG) ---
    if curr['close'] < curr['lower'] and curr['rsi'] < 20:
        # Filtro: Precio sobre EMA 200 + Volumen alto + Mecha clara (Martillo)
        if curr['close'] > curr['ema200'] and vol_confirmation:
            if lower_wick > (body * 2): # La mecha es el doble que el cuerpo
                side = "BUY"
                prob = 90.0 # Subimos la confianza
                entry, tp, sl = curr['close'], curr['close'] * 1.012, curr['close'] * 0.985

    # --- SEÑAL DE VENTA (SHORT) ---
    elif curr['close'] > curr['upper'] and curr['rsi'] > 80:
        # Filtro: Precio bajo EMA 200 + Volumen alto + Mecha superior (Estrella fugaz)
        if curr['close'] < curr['ema200'] and vol_confirmation:
            if upper_wick > (body * 2):
                side = "SELL"
                prob = 90.0
                entry, tp, sl = curr['close'], curr['close'] * 0.988, curr['close'] * 1.015

    if side and prob >= 85.0:
        return Signal(side=side, entry=entry, sl=sl, tp=tp, probability=prob,
                      trigger="INSTITUTIONAL_REJECTION", reason="Filtro Vol+Mecha+EMA",
                      timestamp_ms=int(curr['timestamp'].timestamp() * 1000))
    return None

# =========================
# EXCHANGE & TOOLS
# =========================
def build_exchange():
    ex = ccxt.binanceusdm({"enableRateLimit": True})
    ex.load_markets()
    return ex

def normalize_symbol(ex: ccxt.Exchange, s: str) -> str:
    """Corrige el formato para Binance Futuros: BTC/USDT -> BTC/USDT:USDT"""
    if ":" in s: return s
    base_quote = s.split('/')
    if len(base_quote) == 2:
        futures_style = f"{base_quote[0]}/{base_quote[1]}:{base_quote[1]}"
        if futures_style in ex.symbols:
            return futures_style
    return s

def fetch_ohlcv(exchange: ccxt.Exchange, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df

def render_chart(df: pd.DataFrame, signal: Signal, symbol: str, out_path: str) -> str:
    df_c = df.dropna().tail(100).copy()
    df_c['sma'] = df_c['close'].rolling(20).mean()
    df_c['u'] = df_c['sma'] + (2 * df_c['close'].rolling(20).std())
    df_c['l'] = df_c['sma'] - (2 * df_c['close'].rolling(20).std())
    df_c = df_c.dropna()
    df_c.set_index("timestamp", inplace=True)
    ap = [
        mpf.make_addplot(df_c['sma'], color='gray', width=0.7),
        mpf.make_addplot(df_c['u'], color='blue', width=0.7),
        mpf.make_addplot(df_c['l'], color='blue', width=0.7),
        mpf.make_addplot([signal.entry]*len(df_c), color='cyan'),
        mpf.make_addplot([signal.sl]*len(df_c), color='red'),
        mpf.make_addplot([signal.tp]*len(df_c), color='green')
    ]
    mpf.plot(df_c, type='candle', style='binance', addplot=ap, savefig=out_path, tight_layout=True)
    return out_path

async def send_telegram(bot: Bot, signal: Signal, chart_path: str, symbol: str) -> None:
    # Cálculo de porcentajes para el mensaje
    tp_pct = abs((signal.tp - signal.entry) / signal.entry) * 100
    sl_pct = abs((signal.sl - signal.entry) / signal.entry) * 100
    
    msg = (f"🔥 NUEVA SEÑAL DETECTADA 🔥\n\n"
           f"📊 Activo: {symbol}\n"
           f"🟢 ESTADO: TIEMPO DE INGRESAR\n"
           f"🟦 Operación: {signal.side}\n"
           f"🎯 Entrada: {signal.entry:.6f}\n"
           f"✅ Take Profit: {signal.tp:.6f} (+{tp_pct:.2f}%)\n"
           f"🛑 Stop Loss: {signal.sl:.6f} (-{sl_pct:.2f}%)\n\n"
           f"⚡ Confianza: {signal.probability}%\n"
           f"📌 {signal.reason}")
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    with open(chart_path, "rb") as f: await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=f)

async def track_open_trades(exchange: ccxt.Exchange, bot: Bot, open_trades: dict) -> None:
    if not open_trades: return
    to_close = []
    for symbol, t in list(open_trades.items()):
        try:
            # Check Ventana de Entrada (Si status es OPEN)
            if t.get("status") == "OPEN":
                ticker = exchange.fetch_ticker(symbol)
                curr_p = ticker['last']
                diff = (curr_p - t["entry"]) / t["entry"]
                
                expired = False
                if t["side"] == "BUY" and diff > ENTRY_WINDOW_PCT: expired = True
                if t["side"] == "SELL" and diff < -ENTRY_WINDOW_PCT: expired = True
                
                if expired:
                    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"⚠️ {symbol}: ZONA DE ENTRADA SUPERADA.\nEl precio ya se alejó. No entrar tarde.")
                    open_trades[symbol]["status"] = "EXPIRED"

            # Check TP/SL con velas de 1m
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe="1m", limit=3)
            for ts, o, h, l, c, v in ohlcv:
                hit = None
                if t["side"] == "BUY":
                    if l <= t["sl"]: hit = "SL"
                    elif h >= t["tp"]: hit = "TP"
                else:
                    if h >= t["sl"]: hit = "SL"
                    elif l <= t["tp"]: hit = "TP"
                
                if hit:
                    pnl = 1.2 if hit == "TP" else -1.8
                    append_history_row({"closed_at_utc": _utc_now_str(), "symbol": symbol, "side": t["side"], "entry": t["entry"], "sl": t["sl"], "tp": t["tp"], "result": hit, "pnl_pct": pnl})
                    to_close.append(symbol)
                    w, tot, wr = compute_winrate()
                    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"🏁 {symbol} Cerrado en {hit}\n💰 PnL: {pnl}%\n📊 Winrate: {wr:.1f}%")
                    break
        except: pass
    for s in to_close: open_trades.pop(s, None)
    if to_close: save_open_trades(open_trades)

# =========================
# MAIN
# =========================
async def main():
    exchange = build_exchange()
    
    # Proceso de normalización robusto
    symbols_ok = []
    for s in SYMBOLS:
        norm = normalize_symbol(exchange, s)
        if norm in exchange.symbols:
            symbols_ok.append(norm)
    
    bot = Bot(token=TELEGRAM_TOKEN)
    last_sent_ts = {}
    open_trades = load_open_trades()

    print(f"🚀 Bot Operativo | Filtros de Alta Calidad | {len(symbols_ok)} Monedas Activas")
    if len(symbols_ok) == 0:
        print("❌ Error: No se reconocieron las monedas. Revisa el formato.")
        return

    while True:
        for symbol in symbols_ok:
            try:
                df = fetch_ohlcv(exchange, symbol, TIMEFRAME, 250)
                signal = generate_signal(df)
                
                if signal:
                    now = time.time()
                    if (now - last_sent_ts.get(symbol, 0)) > COOLDOWN_MINUTES * 60:
                        path = f"chart_{symbol.replace('/', '_').replace(':', '_')}.png"
                        render_chart(df, signal, symbol, path)
                        await send_telegram(bot, signal, path, symbol)
                        
                        last_sent_ts[symbol] = now
                        open_trades[symbol] = {
                            "side": signal.side, "entry": signal.entry, "tp": signal.tp, 
                            "sl": signal.sl, "status": "OPEN"
                        }
                        save_open_trades(open_trades)
            except Exception as e:
                print(f"Error {symbol}: {e}")
        
        await track_open_trades(exchange, bot, open_trades)
        await asyncio.sleep(CHECK_EVERY_SECONDS)

if __name__ == "__main__":
    asyncio.run(main())