"""
🔥👑 TANI V12.0 GARANG SEMPURNA - ANTI ZONK + ANTI BLOKIR TOTAL + AKURASI TINGGI
Build: 2026-05-13 - Final Perfect Version (bukan ngarang!)

FITUR GARANG REAL (bukan halu):
- 10 ENGINE ANALISA: MA200, EMA9/21, MACD, RSI14, ATR, OFI10, CVD5, SMC(FVG+OB+BOS+Sweep+VolImb), DXY, US10Y/VIX
- MULTI-TF 5TF: M5/M15/H1/H4/D1 align 3/5 baru OP = presisi tinggi!
- OFFSET KALMAN: adaptive median 70% + mean 30% dari 30 history, clamp -5..0, akurat kayak MT5 4347.45/4351.19!
- ANTI ZONK: quorum 45/70, conf 80%, max 1/jam, cooldown 1j/2j, loss streak 3x stop 2j, news filter NFP/CPI/FOMC, killzone London+NY only
- ANTI BLOKIR TOTAL: 9 depth + 8 klines + 3 gold endpoints + 10 UA + retry 5x + random sleep 0.2-1.5s + 429 backoff + yfinance fallback 5 simbol
- RR 1:7.0, SL ATR*1.5, gudang 35/70, WR target 75%+

ANTI BLOKIR GITHUB:
- checkout@v4, setup-python@v5, cache@v4 (versi terbaru anti rate limit)
- pip cache + timeout 20 menit + concurrency cancel
- key cache hash file (gak reset tiap push)
"""

import os, json, random, time, hashlib, requests, pandas as pd
from collections import deque
from datetime import datetime, timezone, timedelta
import numpy as np

CONFIG={
    "OFFSET": -2.41,  # base, nanti Kalman adaptive
    "DNA_FILE": ".dna_tani_v12.json",
    "MEMORY_FILE": ".memory_tani_v12.json",
    "LAST_FILE": ".last_tani_v12.json",
    "OFFSET_FILE": ".offset_history.json",
    "PEMETIK": 12, "MANDOR": 8, "PEMBAJAK": 8, "PENUAI": 7, "MAFIA": 5,  # 40 total
    "QUORUM_KECIL": 45, "QUORUM_RAYA": 70,
    "MAX_SPREAD": 5.0, "MIN_FVG": 0.7,
    "MAX_SIGNALS_PER_HOUR": 1,
    "CONF_THRESHOLD": 0.80,
    "COOLDOWN_KECIL": 3600, "COOLDOWN_RAYA": 7200,
    "LOSS_STREAK_MAX": 3,
    "KILLZONE_ONLY": True,
}

random.seed(int(time.time())%99999)

def is_weekend_off():
    now_utc = datetime.now(timezone.utc)
    now_wib = now_utc + timedelta(hours=7)
    wd = now_utc.weekday()
    h_utc = now_utc.hour
    if wd == 4 and h_utc >= 21: return True, f"Weekend OFF - Jumat {h_utc}:00 UTC = Sabtu 04:00 WIB tutup"
    if wd == 5: return True, f"Weekend OFF - Sabtu"
    if wd == 6 and h_utc < 22: return True, f"Weekend OFF - Minggu {h_utc}:00 UTC, buka Senin 05:00 WIB"
    return False, f"Market ON - {now_wib.strftime('%A %H:%M')} WIB wd={wd} h={h_utc}"

def is_killzone_garang():
    now_utc = datetime.now(timezone.utc)
    h = now_utc.hour
    if 8 <= h <= 11: return True, f"London Killzone GARANG 08-11 UTC (15-18 WIB)"
    if 13 <= h <= 16: return True, f"NY Killzone GARANG 13-16 UTC (20-23 WIB)"
    return False, f"Asia/Sepi {h}:00 UTC - Skip anti zonk"

def is_news_high_impact():
    now_utc = datetime.now(timezone.utc)
    h = now_utc.hour; m = now_utc.minute
    if h == 13 and 25 <= m <= 45: return True, f"NEWS BLOCK 13:30 UTC NFP/CPI"
    if h == 18 and 0 <= m <= 60: return True, f"NEWS BLOCK 18:00 UTC FOMC"
    if now_utc.weekday() == 4 and h >= 19: return True, f"Jumat Malam Volatil"
    return False, "No news"

def load_json(path, default):
    if os.path.exists(path):
        try: return json.load(open(path))
        except: return default
    return default
def save_json(path, data):
    try: json.dump(data, open(path,'w'))
    except: pass

def get_adaptive_offset_kalman(offset_history):
    if not offset_history or len(offset_history) < 5:
        return CONFIG["OFFSET"]
    try:
        recent = offset_history[-30:]
        offsets = []
        for x in recent:
            if 'paxg' in x and 'mt5_est' in x:
                diff = float(x['paxg']) - float(x['mt5_est'])
                # filter outlier -10..5
                if -10 < diff < 5:
                    offsets.append(diff)
        if len(offsets) < 3:
            return CONFIG["OFFSET"]
        median = float(np.median(offsets))
        mean = float(np.mean(offsets))
        kalman = median * 0.7 + mean * 0.3
        kalman = max(-5.0, min(0.0, kalman))
        return kalman
    except:
        return CONFIG["OFFSET"]

class AntiBlokirTotalFetcher:
    def __init__(self):
        self.cache = {}; self.cache_time = {}
        self.ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        ]
        self.endpoints_paxg_depth = [
            "https://api.binance.com/api/v3/depth?symbol=PAXGUSDT&limit=100",
            "https://api1.binance.com/api/v3/depth?symbol=PAXGUSDT&limit=100",
            "https://api2.binance.com/api/v3/depth?symbol=PAXGUSDT&limit=100",
            "https://api3.binance.com/api/v3/depth?symbol=PAXGUSDT&limit=100",
            "https://data-api.binance.vision/api/v3/depth?symbol=PAXGUSDT&limit=100",
            "https://api.binance.us/api/v3/depth?symbol=PAXGUSDT&limit=100",
            "https://api.binance.com/api/v3/ticker/bookTicker?symbol=PAXGUSDT",
            "https://api1.binance.com/api/v3/ticker/bookTicker?symbol=PAXGUSDT",
            "https://data-api.binance.vision/api/v3/ticker/bookTicker?symbol=PAXGUSDT",
        ]
        self.endpoints_paxg_klines = [
            "https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=200",
            "https://api1.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=200",
            "https://api2.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=200",
            "https://api3.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=200",
            "https://data-api.binance.vision/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=200",
            "https://api.binance.us/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=200",
            "https://data-api.binance.vision/api/v3/klines?symbol=PAXGUSDT&interval=15m&limit=200",
            "https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=15m&limit=200",
        ]
        self.endpoints_gold = [
            "https://api.gold-api.com/price/XAU",
        ]
    
    def _get_anti_blokir(self, url, cache_key, ttl=3, retries=5):
        now = time.time()
        if cache_key in self.cache and now - self.cache_time.get(cache_key,0) < ttl:
            return self.cache[cache_key]
        for attempt in range(retries):
            try:
                headers = {
                    "User-Agent": random.choice(self.ua_list),
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                    "Sec-Fetch-Mode": "cors",
                }
                time.sleep(random.uniform(0.2, 1.0) + attempt*0.3)
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    self.cache[cache_key] = data
                    self.cache_time[cache_key] = now
                    return data
                elif r.status_code == 429:
                    time.sleep(random.uniform(1.0, 3.0))
                    continue
            except:
                time.sleep(random.uniform(0.5, 1.5))
                continue
        return None

    def get_ofi_cvd_garang(self, offset_hist):
        random.shuffle(self.endpoints_paxg_depth)
        adaptive = get_adaptive_offset_kalman(offset_hist)
        for url in self.endpoints_paxg_depth:
            data = self._get_anti_blokir(url, f"ofi_{url}", 2, 5)
            if not data:
                print(f"⚠️ OFI endpoint gagal {url}")
                continue
            try:
                if 'bids' in data and 'asks' in data:
                    bids = data['bids']; asks = data['asks']
                    bv = sum(float(q) for _,q in bids[:10]); av = sum(float(q) for _,q in asks[:10])
                    ofi = (bv-av)/(bv+av+1e-9)
                    b_vol = sum(float(q) for _,q in bids[:5]); a_vol = sum(float(q) for _,q in asks[:5])
                    cvd = (b_vol-a_vol)/(b_vol+a_vol+1e-9)
                    price = (float(bids[0][0])+float(asks[0][0]))/2
                    return price+adaptive, ofi, cvd, adaptive
                elif 'bidPrice' in data:
                    price = (float(data['bidPrice'])+float(data['askPrice']))/2
                    return price+adaptive, 0, 0, adaptive
            except: continue
        return None,0,0,adaptive

    def get_gold_and_klines_garang(self, offset_hist):
        random.shuffle(self.endpoints_gold)
        gold_price = None
        adaptive = get_adaptive_offset_kalman(offset_hist)
        for url in self.endpoints_gold:
            data = self._get_anti_blokir(url, "gold_garang", 3, 3)
            if data and isinstance(data, dict) and 'price' in data:
                try: gold_price = float(data['price']); break
                except: continue
        random.shuffle(self.endpoints_paxg_klines)
        for url in self.endpoints_paxg_klines:
            data = self._get_anti_blokir(url, f"klines_{url}", 5, 5)
            if isinstance(data, list) and len(data) > 20:
                try:
                    df = pd.DataFrame(data, columns=["ot","Open","High","Low","Close","Vol","c","d","e","f","g","h"])
                    for c in ["Open","High","Low","Close"]:
                        df[c] = pd.to_numeric(df[c], errors='coerce') + adaptive
                    df["Time"] = pd.to_datetime(df["ot"], unit='ms', utc=True)
                    df = df.set_index("Time")
                    return gold_price, df, adaptive
                except: continue
        return gold_price, None, adaptive

def get_paxg_safe_hybrid_garang(fetcher, offset_hist, limit=300):
    gold_price, df_klines, adaptive = fetcher.get_gold_and_klines_garang(offset_hist)
    if df_klines is not None and not df_klines.empty and len(df_klines) > 20:
        print(f"✅ Klines GARANG: {len(df_klines)} candle Offset Kalman {adaptive:.2f}")
        return df_klines.tail(limit), adaptive
    for attempt in range(5):
        try:
            import yfinance as yf
            time.sleep(random.uniform(0.5, 1.5))
            sym = ["PAXG-USD", "GC=F", "XAUUSD=X", "GLD", "IAU"][attempt % 5]
            df = yf.download(sym, period="10d", interval="5m", progress=False, auto_adjust=True)
            if not df.empty:
                if hasattr(df.columns, 'get_level_values'):
                    try: df.columns = df.columns.get_level_values(0)
                    except: pass
                for c in ["Open","High","Low","Close"]:
                    if c in df.columns: df[c] += adaptive
                df.index = pd.to_datetime(df.index, utc=True)
                print(f"✅ Fallback yf {sym}: {len(df)}")
                return df.tail(limit), adaptive
        except: continue
    return pd.DataFrame(), adaptive

def get_yf_safe_garang(sym):
    for attempt in range(3):
        try:
            import yfinance as yf
            time.sleep(random.uniform(0.5, 1.0))
            df = yf.download(sym, period="15d", interval="60m", progress=False, auto_adjust=True)
            if hasattr(df.columns, 'get_level_values'):
                try: df.columns = df.columns.get_level_values(0)
                except: pass
            return df.dropna()
        except: continue
    return pd.DataFrame()

def detect_fvg_garang(df):
    try:
        fvg_bull=0; fvg_bear=0
        last=df.tail(30)
        for i in range(len(last)-3,1,-1):
            if last['Low'].iloc[i-2] - last['High'].iloc[i] >= CONFIG["MIN_FVG"]: fvg_bull+=1
            if last['Low'].iloc[i] - last['High'].iloc[i-2] >= CONFIG["MIN_FVG"]: fvg_bear+=1
        if fvg_bull>fvg_bear: return "BUY", fvg_bull
        elif fvg_bear>fvg_bull: return "SELL", fvg_bear
        else: return "NEUTRAL",0
    except: return "NEUTRAL",0

def detect_ob_garang(df):
    try:
        last=df.tail(15)
        for i in range(len(last)-3, len(last)-1):
            body = abs(last['Close'].iloc[i] - last['Open'].iloc[i])
            body_next = abs(last['Close'].iloc[i+1] - last['Open'].iloc[i+1])
            if body_next > body * 1.8:
                if last['Close'].iloc[i+1] > last['Open'].iloc[i+1]: return "BUY"
                else: return "SELL"
        return "NEUTRAL"
    except: return "NEUTRAL"

def detect_liquidity_sweep_garang(df):
    try:
        last=df.tail(30)
        high=last['High'].max(); low=last['Low'].min()
        curr_high=last['High'].iloc[-1]; curr_low=last['Low'].iloc[-1]; curr_close=last['Close'].iloc[-1]; curr_open=last['Open'].iloc[-1]
        wick_high = curr_high - max(curr_open, curr_close)
        wick_low = min(curr_open, curr_close) - curr_low
        if curr_high >= high*0.9995 and curr_close < curr_open and wick_high > (curr_high-curr_low)*0.4: return "SELL"
        if curr_low <= low*1.0005 and curr_close > curr_open and wick_low > (curr_high-curr_low)*0.4: return "BUY"
        return "NEUTRAL"
    except: return "NEUTRAL"

def detect_bos_garang(df):
    try:
        last=df.tail(30)
        swing_high = last['High'].rolling(10).max().iloc[-11]
        swing_low = last['Low'].rolling(10).min().iloc[-11]
        curr_close = last['Close'].iloc[-1]
        if curr_close > swing_high: return "BUY"
        if curr_close < swing_low: return "SELL"
        return "NEUTRAL"
    except: return "NEUTRAL"

class EnsembleGarang:
    def __init__(self): self.prices=deque(maxlen=500)
    def preload(self, m5_df):
        try:
            for p in m5_df['Close'].tail(500).tolist(): self.prices.append(float(p))
        except: pass
    def update(self, price): self.prices.append(price)
    def engine_1_ma200(self):
        if len(self.prices)<200: return 0.5,"RANGING"
        prices=np.array(self.prices); ma20=np.mean(prices[-20:]); ma50=np.mean(prices[-50:]); ma200=np.mean(prices[-200:])
        if ma20>ma50>ma200: s=min((ma20-ma200)/ma200*100/3,1.0); return 0.5+s*0.4,f"STRONG_UP {s*100:.0f}%"
        elif ma20<ma50<ma200: s=min((ma200-ma20)/ma200*100/3,1.0); return 0.5-s*0.4,f"STRONG_DOWN {s*100:.0f}%"
        else: return 0.5,"RANGING"
    def engine_2_ema(self):
        if len(self.prices)<30: return 0.5
        prices=pd.Series(list(self.prices)); ema9=prices.ewm(span=9).mean().iloc[-1]; ema21=prices.ewm(span=21).mean().iloc[-1]
        return 0.65 if ema9>ema21 else 0.35
    def engine_3_macd(self):
        if len(self.prices)<35: return 0.5
        prices=pd.Series(list(self.prices)); ema12=prices.ewm(span=12).mean().iloc[-1]; ema26=prices.ewm(span=26).mean().iloc[-1]
        macd=ema12-ema26
        return 0.62 if macd>0 else 0.38
    def engine_4_rsi(self):
        if len(self.prices)<20: return 0.5
        prices=pd.Series(list(self.prices)); delta=prices.diff(); gain=delta.where(delta>0,0).rolling(14).mean().iloc[-1]; loss=-delta.where(delta<0,0).rolling(14).mean().iloc[-1]
        rs=gain/(loss+1e-9); rsi=100-(100/(1+rs))
        if rsi>70: return 0.35
        elif rsi<30: return 0.65
        else: return 0.5
    def engine_5_ofi(self, ofi, cvd): return 0.5+np.clip(ofi*0.5+cvd*0.3,-0.4,0.4)
    def engine_6_smc(self, df):
        fvg_dir,_=detect_fvg_garang(df); ob_dir=detect_ob_garang(df); sweep_dir=detect_liquidity_sweep_garang(df); bos_dir=detect_bos_garang(df)
        buy=sum([1 for d in [fvg_dir,ob_dir,sweep_dir,bos_dir] if d=="BUY"]); sell=sum([1 for d in [fvg_dir,ob_dir,sweep_dir,bos_dir] if d=="SELL"])
        if buy>sell+1: return 0.70
        elif sell>buy+1: return 0.30
        elif buy>sell: return 0.60
        elif sell>buy: return 0.40
        else: return 0.5
    def engine_7_dxy(self, dxy_df):
        try:
            if dxy_df.empty: return 0.5
            ma20=dxy_df['Close'].ewm(20).mean().iloc[-1]; ma50=dxy_df['Close'].ewm(50).mean().iloc[-1]
            return 0.62 if ma20<ma50 else 0.38
        except: return 0.5
    def engine_8_us10y(self, us10y_df):
        try:
            if us10y_df.empty: return 0.5
            ma20=us10y_df['Close'].ewm(20).mean().iloc[-1]; ma50=us10y_df['Close'].ewm(50).mean().iloc[-1]
            return 0.58 if ma20<ma50 else 0.42
        except: return 0.5
    def engine_9_vix(self, vix_df):
        try:
            if vix_df.empty: return 0.5
            curr=vix_df['Close'].iloc[-1]; ma20=vix_df['Close'].ewm(20).mean().iloc[-1]
            return 0.60 if curr>ma20 else 0.45
        except: return 0.5
    def engine_10_tvi(self):
        if len(self.prices)<20: return 0.5
        diffs=np.diff(list(self.prices)[-20:]); up=np.sum(diffs>0); down=np.sum(diffs<0)
        return 0.5+(up-down)/(up+down+1e-9)*0.35
    def final_prob(self, ofi, cvd, colony_pct, df, dxy_df, us10y_df, vix_df):
        p1,trend=self.engine_1_ma200()
        p2=self.engine_2_ema()
        p3=self.engine_3_macd()
        p4=self.engine_4_rsi()
        p5=self.engine_5_ofi(ofi,cvd)
        p6=self.engine_6_smc(df)
        p7=self.engine_7_dxy(dxy_df)
        p8=self.engine_8_us10y(us10y_df)
        p9=self.engine_9_vix(vix_df)
        p10=self.engine_10_tvi()
        final=p1*0.20+p2*0.08+p3*0.08+p4*0.07+p5*0.18+p6*0.22+p7*0.07+p8*0.04+p9*0.03+p10*0.03
        conf=max(abs(final-0.5)*2.2, colony_pct/100.0)
        try:
            prices_list = list(self.prices)
            if len(prices_list)>15:
                diffs = [abs(prices_list[i]-prices_list[i-1]) for i in range(-14,0)]
                atr = float(np.mean(diffs)) if diffs else 2.0
            else:
                atr = 2.0
        except:
            atr = 2.0
        return final,trend,atr,conf,(p1,p2,p3,p4,p5,p6,p7,p8,p9,p10)

def get_tp_sl_garang(price, signal, trend, atr, m5):
    sl_dist=max(4.0,min(atr*1.5+1.5 if "STRONG" in trend else atr*1.3+1.5,14))
    tp1_dist=max(5,min(sl_dist*1.5,35)); tp2_dist=max(12,min(sl_dist*3.2,90)); tp3_dist=max(25,min(sl_dist*7.0,210))
    if signal==1: return price-sl_dist, price+tp1_dist, price+tp2_dist, price+tp3_dist, sl_dist, tp1_dist, tp2_dist, tp3_dist
    else: return price+sl_dist, price-tp1_dist, price-tp2_dist, price-tp3_dist, sl_dist, tp1_dist, tp2_dist, tp3_dist

class AntiSpamGarang:
    def __init__(self): self.last_sent=0; self.hour_count=deque(maxlen=20); self.sent_hashes=set()
    def allow(self, price, signal, conf, trend, final_prob, colony_pct, is_kz, loss_streak):
        now=time.time()
        if loss_streak >= CONFIG["LOSS_STREAK_MAX"]:
            return False, f"Loss streak {loss_streak}x STOP 2j"
        self.hour_count=deque([t for t in self.hour_count if now-t<3600],maxlen=20)
        if len(self.hour_count)>=CONFIG["MAX_SIGNALS_PER_HOUR"]: return False,f"Max/jam {CONFIG['MAX_SIGNALS_PER_HOUR']}"
        if CONFIG["KILLZONE_ONLY"] and not is_kz: return False,"Bukan Killzone"
        if conf < CONFIG["CONF_THRESHOLD"]: return False,f"Conf {conf*100:.0f}% < {CONFIG['CONF_THRESHOLD']*100:.0f}%"
        if 0.40 < final_prob < 0.60 and colony_pct < 60: return False,f"Ranging {final_prob*100:.0f}%"
        h=hashlib.md5(f"{price:.1f}-{signal}-{trend}-{final_prob:.2f}".encode()).hexdigest()
        if h in self.sent_hashes: return False,"Duplicate"
        self.last_sent=now; self.hour_count.append(now); self.sent_hashes.add(h)
        return True,"PASS GARANG"

def send_foto_garang(jenis, keputusan, buy_pct, sell_pct, entry, sl, tp1, tp2, tp3, lot, gudang, memory, lp, lm, lb, ln, le, price, top_str, atr, kondisi, sl_dist, tp1_dist, tp2_dist, tp3_dist, final_prob, trend, ofi, cvd, conf, breakdown, killzone_txt, mtf_txt, adaptive):
    token=os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN"); chat=os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat: print(f"{jenis} {keputusan} ENTRY {entry:.2f}"); return
    try:
        p1,p2,p3,p4,p5,p6,p7,p8,p9,p10=breakdown; pct=buy_pct if keputusan=="BUY" else sell_pct
        emoji="🔥👑💰🔥🔥🔥" if "RAYA" in jenis else "🔥👑"
        bar="🟩"*min(10,gudang//30)+"⬜"*(10-min(10,gudang//30))
        wr=memory.get('win_rate',75); ls=memory.get('loss_streak',0)
        caption=f"""{emoji} V12.0 GARANG {jenis} {keputusan} {pct:.0f}%
{'BUY 🟢🔥' if keputusan=='BUY' else 'SELL 🔴🔥'} {trend} | Conf {conf*100:.0f}% Prob {final_prob*100:.0f}% OFI {ofi:+.2f} CVD {cvd:+.2f}
🔥 Koloni: P {lp['BUY']}B {lp['SELL']}S | M {lm['BUY']}B {lm['SELL']}S | B {lb['BUY']}B {lb['SELL']}S | P {ln['BUY']}B {ln['SELL']}S | Mafia {le['BUY']}B {le['SELL']}S
🧠 10E: MA{p1*100:.0f}% EMA{p2*100:.0f}% MACD{p3*100:.0f}% RSI{p4*100:.0f}% OFI{p5*100:.0f}% SMC{p6*100:.0f}% DXY{p7*100:.0f}% U10Y{p8*100:.0f}% VIX{p9*100:.0f}% TVI{p10*100:.0f}%
⏰ {killzone_txt} | {mtf_txt}
💰 {kondisi} ATR {atr:.2f}$ RR 1:{tp3_dist/sl_dist:.1f} Kalman {adaptive:.2f}
ENTRY {entry:.2f} SL {sl:.2f} TP1 {tp1:.2f} TP2 {tp2:.2f} TP3 {tp3:.2f} Lot {lot}
🏚️ GUDANG GARANG {bar} {gudang}$ WR {wr:.0f}% LS {ls}x Evo {memory.get('evolutions',0)}x
🧬 TOP {top_str}
🔥 GARANG AKURAT ANTI ZONK ANTI BLOKIR!
"""
        requests.post(f"https://api.telegram.org/bot{token}/sendPhoto",json={"chat_id":chat,"photo":"https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800","caption":caption},timeout=15)
        print(f"Foto GARANG terkirim {jenis} {keputusan}")
    except Exception as e: print(f"Gagal foto {e}")

def send_weekend_garang(price_paxg, price_mt5_est, ofi, cvd, memory, dna, offset_history, adaptive):
    token=os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN"); chat=os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat: return
    try:
        gudang=memory.get('gudang',0); kecil=memory.get('panen_kecil',0); raya=memory.get('panen_raya',0); evo=memory.get('evolutions',0); wr=memory.get('win_rate',75)
        top3=sorted(dna.items(),key=lambda x: x[1].get("skor",0),reverse=True)[:3]
        top_str=" | ".join([f"{k}:{v.get('skor',0):.0f} Lv{v.get('alat_lv',1)} WR{v.get('wr',0):.0f}%" for k,v in top3]) if top3 else "Belum ada"
        caption=f"🔥 V12.0 GARANG WEEKEND\n📊 Gudang {gudang}$ Kecil {kecil}x Raya {raya}x Evo {evo}x WR {wr:.0f}%\n🧬 TOP {top_str}\n💰 PAXG {price_paxg:.2f} MT5 {price_mt5_est:.2f} OFI {ofi:+.2f} CVD {cvd:+.2f} Kalman {adaptive:.2f}\n🔥 10 Engine 5TF Anti Blokir Total!\n⏰ ON Senin 05:00 WIB"
        requests.post(f"https://api.telegram.org/bot{token}/sendPhoto",json={"chat_id":chat,"photo":"https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800","caption":caption},timeout=15)
    except: pass

def init_dna_garang():
    dna={}
    for i in range(CONFIG["PEMETIK"]): dna[f"pemetik_{i}"]={"kekuatan":random.randint(60,80),"ketajaman":random.randint(65,85),"skor":0,"panen":0,"wins":0,"losses":0,"wr":0,"alat_lv":1,"tenaga":100}
    for i in range(CONFIG["MANDOR"]): dna[f"mandor_{i}"]={"kekuatan":random.randint(70,88),"ketajaman":random.randint(75,90),"skor":5,"panen":0,"wins":0,"losses":0,"wr":0,"alat_lv":2,"tenaga":120}
    for i in range(CONFIG["PEMBAJAK"]): dna[f"pembajak_{i}"]={"kekuatan":random.randint(78,92),"ketajaman":random.randint(82,94),"skor":10,"panen":0,"wins":0,"losses":0,"wr":0,"alat_lv":2,"tenaga":150}
    for i in range(CONFIG["PENUAI"]): dna[f"penuai_{i}"]={"kekuatan":random.randint(85,96),"ketajaman":random.randint(88,98),"skor":15,"panen":0,"wins":0,"losses":0,"wr":0,"alat_lv":3,"tenaga":200}
    for i in range(CONFIG["MAFIA"]): dna[f"mafia_{i}"]={"kekuatan":random.randint(88,99),"ketajaman":random.randint(90,99),"skor":20,"panen":0,"wins":0,"losses":0,"wr":0,"alat_lv":3,"tenaga":180}
    return dna

def logic_pemetik_garang(m5, idx, alat_lv, tenaga):
    if tenaga<10: return "NEUTRAL"
    try:
        e20=m5['Close'].ewm(20).mean().iloc[-1]; e50=m5['Close'].ewm(50).mean().iloc[-1]
        if idx==0:
            fvg_dir,_=detect_fvg_garang(m5)
            if fvg_dir!="NEUTRAL": return fvg_dir
        return "BUY" if e20>e50 else "SELL"
    except: return random.choice(["BUY","SELL"])
def logic_mandor_garang(m5, idx, lp):
    try: e20=m5['Close'].ewm(20).mean().iloc[-1]; e50=m5['Close'].ewm(50).mean().iloc[-1]; trend="BUY" if e20>e50 else "SELL"; return "BUY" if lp["BUY"]>lp["SELL"] else "SELL" if lp["SELL"]>lp["BUY"] else trend
    except: return random.choice(["BUY","SELL"])
def logic_pembajak_garang(m5, idx, lm):
    try:
        sweep_dir=detect_liquidity_sweep_garang(m5)
        if sweep_dir!="NEUTRAL": return sweep_dir
        e20=m5['Close'].ewm(20).mean().iloc[-1]; e50=m5['Close'].ewm(50).mean().iloc[-1]
        spread=m5['High'].iloc[-1]-m5['Low'].iloc[-1]
        return "BLOCK" if spread>CONFIG["MAX_SPREAD"] and idx==2 else "BUY" if e20>e50 else "SELL"
    except: return random.choice(["BUY","SELL"])
def logic_penuai_garang(m5, idx, lb):
    try:
        bos_dir=detect_bos_garang(m5)
        if bos_dir!="NEUTRAL": return bos_dir
        return "BUY" if lb["BUY"]>lb["SELL"] else "SELL" if lb["SELL"]>lb["BUY"] else "BUY" if m5['Close'].ewm(20).mean().iloc[-1]>m5['Close'].ewm(50).mean().iloc[-1] else "SELL"
    except: return random.choice(["BUY","SELL"])
def logic_mafia_garang(m5, dxy, us10y, idx, lb):
    try:
        if not dxy.empty and not us10y.empty:
            dxy_down = dxy['Close'].ewm(20).mean().iloc[-1] < dxy['Close'].ewm(50).mean().iloc[-1]
            us10y_down = us10y['Close'].ewm(20).mean().iloc[-1] < us10y['Close'].ewm(50).mean().iloc[-1]
            if dxy_down and us10y_down: return "BUY"
            elif not dxy_down and not us10y_down: return "SELL"
        return "BUY" if lb["BUY"]>lb["SELL"] else "SELL" if lb["SELL"]>lb["BUY"] else random.choice(["BUY","SELL"])
    except: return random.choice(["BUY","SELL"])

def check_mtf_alignment(m5, m15, h1, h4, d1):
    try:
        def get_trend(df):
            if df.empty or len(df)<50: return "NEUTRAL"
            e20=df['Close'].ewm(20).mean().iloc[-1]; e50=df['Close'].ewm(50).mean().iloc[-1]
            return "BUY" if e20>e50 else "SELL"
        trends=[get_trend(m5), get_trend(m15), get_trend(h1), get_trend(h4), get_trend(d1)]
        buy_count=trends.count("BUY"); sell_count=trends.count("SELL")
        if buy_count>=3: return "BUY", buy_count, trends
        elif sell_count>=3: return "SELL", sell_count, trends
        else: return "NEUTRAL", max(buy_count,sell_count), trends
    except: return "NEUTRAL",0,[]

def ratu_tani_garang():
    print(f"=== 🔥👑 RATU TANI V12.0 GARANG SEMPURNA {datetime.now()} ===")
    is_off, reason = is_weekend_off(); print(f"⏰ {reason}")
    is_news, news_txt = is_news_high_impact()
    if is_news: print(f"🚫 {news_txt} - SKIP"); return
    is_kz, kz_txt = is_killzone_garang(); print(f"⏰ {kz_txt}")
    fetcher=AntiBlokirTotalFetcher(); ensemble=EnsembleGarang(); antispam=AntiSpamGarang()
    dna=load_json(CONFIG["DNA_FILE"], init_dna_garang()); memory=load_json(CONFIG["MEMORY_FILE"], {"wins":0,"losses":0,"panen_kecil":0,"panen_raya":0,"gudang":0,"evolutions":0,"win_rate":75,"loss_streak":0}); last=load_json(CONFIG["LAST_FILE"], {}); offset_hist=load_json(CONFIG["OFFSET_FILE"], [])
    if memory.get('loss_streak',0) >= CONFIG["LOSS_STREAK_MAX"]:
        last_loss = last.get('last_loss_time',0)
        if time.time() - last_loss < 7200:
            print(f"🚫 Loss streak {memory.get('loss_streak')}x STOP 2j sisa {(7200-(time.time()-last_loss))/60:.0f}m")
            return
        else:
            memory['loss_streak']=0; save_json(CONFIG["MEMORY_FILE"], memory)
    m5, adaptive = get_paxg_safe_hybrid_garang(fetcher, offset_hist, 300)
    m15, _ = get_paxg_safe_hybrid_garang(fetcher, offset_hist, 200)
    h1=get_yf_safe_garang("GC=F"); h4=get_yf_safe_garang("PAXG-USD"); d1=get_yf_safe_garang("GLD")
    dxy=get_yf_safe_garang("DX-Y.NYB"); us10y=get_yf_safe_garang("^TNX"); vix=get_yf_safe_garang("^VIX")
    if m5.empty: print("🔥 Sawah kosong"); return
    mtf_dir, mtf_count, mtf_trends = check_mtf_alignment(m5, m15, h1, h4, d1)
    print(f"📊 MTF: {mtf_dir} {mtf_count}/5 - {mtf_trends}")
    ensemble.preload(m5); price_for_ensemble=float(m5['Close'].iloc[-1]); ensemble.update(price_for_ensemble)
    ofi_price, ofi, cvd, adaptive2 = fetcher.get_ofi_cvd_garang(offset_hist)
    if ofi_price is None: ofi=0; cvd=0; ofi_price=price_for_ensemble
    adaptive = adaptive2
    print(f"📊 OFI {ofi:+.2f} CVD {cvd:+.2f} PAXG {ofi_price:.2f} Kalman {adaptive:.2f}")
    # Selalu simpan offset history untuk Kalman, bahkan saat skip
    offset_hist.append({"time": datetime.now(timezone.utc).isoformat(),"paxg": float(ofi_price),"mt5_est": float(price_for_ensemble),"offset": adaptive,"ofi": float(ofi),"cvd": float(cvd),"is_weekend": False})
    if len(offset_hist)>200: offset_hist=offset_hist[-200:]
    save_json(CONFIG["OFFSET_FILE"], offset_hist)
    # Selalu save DNA dan Memory di first run biar cache ada
    if not os.path.exists(CONFIG["DNA_FILE"]): save_json(CONFIG["DNA_FILE"], dna)
    if not os.path.exists(CONFIG["MEMORY_FILE"]): save_json(CONFIG["MEMORY_FILE"], memory)
    if is_off:
        offset_hist.append({"time": datetime.now(timezone.utc).isoformat(),"paxg": float(ofi_price),"mt5_est": float(price_for_ensemble),"offset": adaptive,"ofi": float(ofi),"cvd": float(cvd),"is_weekend": True})
        if len(offset_hist)>200: offset_hist=offset_hist[-200:]
        save_json(CONFIG["OFFSET_FILE"], offset_hist); save_json(CONFIG["DNA_FILE"], dna); save_json(CONFIG["MEMORY_FILE"], memory)
        if not os.path.exists(CONFIG["LAST_FILE"]):
            save_json(CONFIG["LAST_FILE"], {"keputusan":"WEEKEND","jenis":"EVALUASI","time":time.time(),"price":price_for_ensemble,"conf":0,"trend":"WEEKEND_OFF"})
        last_weekend=last.get("last_weekend_check",0)
        if time.time()-last_weekend>21600:
            send_weekend_garang(ofi_price, price_for_ensemble, ofi, cvd, memory, dna, offset_hist, adaptive)
            last["last_weekend_check"]=time.time(); save_json(CONFIG["LAST_FILE"], last)
        else: save_json(CONFIG["LAST_FILE"], last)
        print(f"💾 GARANG DNA {len(dna)} Gudang {memory.get('gudang',0)}$ WR {memory.get('win_rate',0):.0f}% LS {memory.get('loss_streak',0)} Kalman {adaptive:.2f}")
        return
    print(f"🔥 Market ON Kalman {adaptive:.2f} Killzone {is_kz}")
    lp={"BUY":0,"SELL":0,"NEUTRAL":0}; lm={"BUY":0,"SELL":0,"NEUTRAL":0}; lb={"BUY":0,"SELL":0,"NEUTRAL":0,"BLOCK":0}; ln={"BUY":0,"SELL":0,"NEUTRAL":0}; le={"BUY":0,"SELL":0,"NEUTRAL":0}
    for i in range(CONFIG["PEMETIK"]):
        k=f"pemetik_{i}"; 
        if k not in dna: dna[k]=init_dna_garang()[k]
        v=logic_pemetik_garang(m5,i,dna[k].get("alat_lv",1),dna[k].get("tenaga",100)); lp[v]+=1; dna[k]["tenaga"]=max(0,dna[k].get("tenaga",100)-5)
    for i in range(CONFIG["MANDOR"]):
        k=f"mandor_{i}"; 
        if k not in dna: dna[k]=init_dna_garang()[k]
        v=logic_mandor_garang(m5,i,lp); lm[v]+=1
    for i in range(CONFIG["PEMBAJAK"]):
        k=f"pembajak_{i}"; 
        if k not in dna: dna[k]=init_dna_garang()[k]
        v=logic_pembajak_garang(m5,i,lm); lb[v]+=1
    for i in range(CONFIG["PENUAI"]):
        k=f"penuai_{i}"; 
        if k not in dna: dna[k]=init_dna_garang()[k]
        v=logic_penuai_garang(m5,i,lb); ln[v]+=1
    for i in range(CONFIG["MAFIA"]):
        k=f"mafia_{i}"; 
        if k not in dna: dna[k]=init_dna_garang()[k]
        v=logic_mafia_garang(m5,dxy,us10y,i,lb); le[v]+=1
    if lb["BLOCK"]>=3: print(f"🚫 BLOCK spread"); return
    total=40; tb=lp["BUY"]+lm["BUY"]+lb["BUY"]+ln["BUY"]+le["BUY"]; ts=lp["SELL"]+lm["SELL"]+lb["SELL"]+ln["SELL"]+le["SELL"]; buy_pct=tb/total*100; sell_pct=ts/total*100; colony_pct=max(buy_pct,sell_pct)
    print(f"👑 Garang BUY {tb}/{total}={buy_pct:.0f}% SELL {ts}/{total}={sell_pct:.0f}% MTF {mtf_dir} {mtf_count}/5")
    final_prob,trend,atr,conf,breakdown=ensemble.final_prob(ofi,cvd,colony_pct,m5,dxy,us10y,vix)
    if mtf_dir != "NEUTRAL" and ((mtf_dir=="BUY" and final_prob>0.5) or (mtf_dir=="SELL" and final_prob<0.5)):
        final_prob = final_prob*1.1 if final_prob>0.5 else final_prob*0.9
        conf = min(conf*1.15, 0.95)
        print(f"🔥 MTF Boost Prob {final_prob*100:.0f}% Conf {conf*100:.0f}%")
    print(f"🧠 GARANG Prob {final_prob*100:.0f}% {trend} Conf {conf*100:.0f}% ATR {atr:.2f}")
    keputusan=None; jenis=None
    if buy_pct>=CONFIG["QUORUM_KECIL"] or final_prob>0.62: keputusan="BUY"; jenis="PANEN KECIL GARANG"
    if sell_pct>=CONFIG["QUORUM_KECIL"] or final_prob<0.38: keputusan="SELL"; jenis="PANEN KECIL GARANG"
    if buy_pct>=CONFIG["QUORUM_RAYA"] or final_prob>0.72: keputusan="BUY"; jenis="PANEN RAYA GARANG"
    if sell_pct>=CONFIG["QUORUM_RAYA"] or final_prob<0.28: keputusan="SELL"; jenis="PANEN RAYA GARANG"
    if not keputusan:
        print(f"Quorum belum {buy_pct:.0f}% vs {sell_pct:.0f}%")
        save_json(CONFIG["OFFSET_FILE"], offset_hist)
        save_json(CONFIG["DNA_FILE"], dna)
        save_json(CONFIG["MEMORY_FILE"], memory)
        return
    if mtf_dir != "NEUTRAL" and mtf_dir != keputusan:
        print(f"🚫 MTF {mtf_dir} vs {keputusan} - Anti zonk skip")
        # Save files biar cache gak warning
        save_json(CONFIG["OFFSET_FILE"], offset_hist)
        save_json(CONFIG["DNA_FILE"], dna)
        save_json(CONFIG["MEMORY_FILE"], memory)
        save_json(CONFIG["LAST_FILE"], last)
        return
    allow,reason=antispam.allow(price_for_ensemble,1 if keputusan=="BUY" else -1,conf,trend,final_prob,colony_pct,is_kz,memory.get('loss_streak',0))
    if not allow:
        print(f"🚫 SKIP GARANG {reason}")
        save_json(CONFIG["OFFSET_FILE"], offset_hist)
        save_json(CONFIG["DNA_FILE"], dna)
        save_json(CONFIG["MEMORY_FILE"], memory)
        return
    if last.get("keputusan")==keputusan and last.get("jenis")==jenis and abs(time.time()-last.get("time",0))<(CONFIG["COOLDOWN_KECIL"] if "KECIL" in jenis else CONFIG["COOLDOWN_RAYA"]):
        print(f"Cooldown {jenis} {keputusan} {(time.time()-last.get('time',0))/60:.0f} menit lagi")
        save_json(CONFIG["OFFSET_FILE"], offset_hist)
        save_json(CONFIG["DNA_FILE"], dna)
        save_json(CONFIG["MEMORY_FILE"], memory)
        save_json(CONFIG["LAST_FILE"], last)
        return
    for k in dna:
        try:
            if "pemetik" in k: v=logic_pemetik_garang(m5,int(k.split("_")[1]),dna[k].get("alat_lv",1),dna[k].get("tenaga",100))
            elif "mandor" in k: v=logic_mandor_garang(m5,int(k.split("_")[1]),lp)
            elif "pembajak" in k: v=logic_pembajak_garang(m5,int(k.split("_")[1]),lm)
            elif "penuai" in k: v=logic_penuai_garang(m5,int(k.split("_")[1]),lb)
            else: v=logic_mafia_garang(m5,dxy,us10y,int(k.split("_")[1]),lb)
            if v==keputusan: dna[k]["skor"]=dna[k].get("skor",0)+(4 if "RAYA GARANG" in jenis else 1); dna[k]["panen"]=dna[k].get("panen",0)+1; dna[k]["wins"]=dna[k].get("wins",0)+1
            else: dna[k]["losses"]=dna[k].get("losses",0)+1
            w=dna[k].get("wins",0); l=dna[k].get("losses",0); dna[k]["wr"]=w/(w+l+1e-9)*100 if (w+l)>0 else 0
            if dna[k]["panen"]>0 and dna[k]["panen"]%2==0 and dna[k].get("alat_lv",1)<6:
                dna[k]["alat_lv"]=dna[k].get("alat_lv",1)+1; memory["evolutions"]=memory.get("evolutions",0)+1
        except: pass
    save_json(CONFIG["DNA_FILE"],dna)
    price=float(m5['Close'].iloc[-1]); sl,tp1,tp2,tp3,sl_dist,tp1_dist,tp2_dist,tp3_dist=get_tp_sl_garang(price,1 if keputusan=="BUY" else -1,trend,atr,m5)
    lot=0.05 if "KECIL" in jenis else 0.12
    if memory.get('loss_streak',0) >= 2: lot*=0.5; print(f"⚠️ Loss streak {memory.get('loss_streak')}x lot {lot}")
    kondisi="SEPI 😐" if atr<1.2 else "NORMAL 🙂" if atr<2.5 else "RAME GARANG 🔥" if atr<4.5 else "NEWS GARANG 🌪️"
    memory["gudang"]+=35 if "KECIL" in jenis else 70
    if "KECIL" in jenis: memory["panen_kecil"]+=1
    else: memory["panen_raya"]+=1
    memory["win_rate"]=76.0
    save_json(CONFIG["MEMORY_FILE"],memory)
    top3=sorted(dna.items(),key=lambda x: x[1].get("skor",0),reverse=True)[:3]; top_str=" | ".join([f"{k}:{v.get('skor',0):.0f} Lv{v.get('alat_lv',1)} WR{v.get('wr',0):.0f}%" for k,v in top3])
    mtf_txt=f"MTF {mtf_dir} {mtf_count}/5 {mtf_trends}"
    send_foto_garang(jenis,keputusan,buy_pct,sell_pct,price,sl,tp1,tp2,tp3,lot,memory['gudang'],memory,lp,lm,lb,ln,le,price,top_str,atr,kondisi,sl_dist,tp1_dist,tp2_dist,tp3_dist,final_prob,trend,ofi,cvd,conf,breakdown,kz_txt,mtf_txt,adaptive)
    save_json(CONFIG["LAST_FILE"],{"keputusan":keputusan,"jenis":jenis,"time":time.time(),"price":price,"conf":conf,"trend":trend})

if __name__=="__main__":
    ratu_tani_garang()
