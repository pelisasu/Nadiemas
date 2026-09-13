"""
🌾👑 SINGULARITY TANI V8.8.1 FIX - FIX 100% SELL KE-SKIP ANTI SPAM!
Bug V8.8: 25 petani 100% SELL tapi Prob 44% RANGING Conf 13% ke-skip!
Fix:
1. Preload 200 harga ke ensemble biar MA/MACD/TVI gak 0.5 terus
2. Colony confidence override: kalo 100% SELL, conf = 100% bukan 13%
3. Anti spam bypass kalo quorum RAYA 55%+ (colony kuat)
4. Hapus metals.live SSL error
5. OFI -0.43 kuat SELL harusnya boost conf
"""
import os, json, random, time, hashlib, requests, pandas as pd
from collections import deque
from datetime import datetime, timezone
import numpy as np

CONFIG={
    "OFFSET": -2.25,
    "DNA_FILE": ".dna_tani_v8.json",
    "MEMORY_FILE": ".memory_tani_v8.json",
    "LAST_FILE": ".last_tani_v8.json",
    "PEMETIK": 10,
    "MANDOR": 5,
    "PEMBAJAK": 5,
    "PENUAI": 5,
    "QUORUM_KECIL": 32,
    "QUORUM_RAYA": 55,
    "MAX_SPREAD": 9.0,
    "MIN_FVG": 0.4,
    "MAX_SIGNALS_PER_HOUR": 4,
    "CONF_THRESHOLD": 0.68,
    "COOLDOWN_KECIL": 900,
    "COOLDOWN_RAYA": 1800,
}

random.seed(int(time.time())%99999)

class AntiBlokirFetcher:
    def __init__(self):
        self.cache = {}
        self.cache_time = {}
        self.ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        self.endpoints_paxg_depth = [
            "https://api.binance.com/api/v3/depth?symbol=PAXGUSDT&limit=20",
            "https://api1.binance.com/api/v3/depth?symbol=PAXGUSDT&limit=20",
            "https://api2.binance.com/api/v3/depth?symbol=PAXGUSDT&limit=20",
            "https://data-api.binance.vision/api/v3/depth?symbol=PAXGUSDT&limit=20",
        ]
        self.endpoints_paxg_klines = [
            "https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=100",
            "https://api1.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=100",
            "https://data-api.binance.vision/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=100",
        ]
        self.endpoints_gold = [
            "https://api.gold-api.com/price/XAU",
        ]
    
    def _get(self, url, cache_key, ttl=2):
        now = time.time()
        if cache_key in self.cache and now - self.cache_time.get(cache_key,0) < ttl:
            return self.cache[cache_key]
        try:
            headers = {"User-Agent": random.choice(self.ua_list), "Accept": "application/json"}
            time.sleep(random.uniform(0.1, 0.4))
            r = requests.get(url, headers=headers, timeout=7)
            if r.status_code == 200:
                data = r.json()
                self.cache[cache_key] = data
                self.cache_time[cache_key] = now
                return data
        except Exception as e:
            print(f"Fetch gagal {url[:30]}: {e}")
            pass
        return None
    
    def get_ofi(self):
        random.shuffle(self.endpoints_paxg_depth)
        for url in self.endpoints_paxg_depth:
            data = self._get(url, "ofi", ttl=2)
            if data and 'bids' in data:
                try:
                    bids=data['bids']; asks=data['asks']
                    bv=sum(float(q) for _,q in bids[:5]); av=sum(float(q) for _,q in asks[:5])
                    ofi=(bv-av)/(bv+av+1e-9)
                    price=(float(bids[0][0])+float(asks[0][0]))/2
                    return price+CONFIG["OFFSET"], ofi
                except: continue
        return None, 0
    
    def get_gold_and_klines(self):
        random.shuffle(self.endpoints_gold)
        gold_price = None
        for url in self.endpoints_gold:
            data = self._get(url, "gold", ttl=3)
            if data:
                try:
                    if isinstance(data, dict) and 'price' in data: 
                        gold_price = float(data['price'])
                        break
                except: continue
        
        random.shuffle(self.endpoints_paxg_klines)
        for url in self.endpoints_paxg_klines:
            data = self._get(url, "klines", ttl=5)
            if isinstance(data, list) and len(data)>20:
                try:
                    df=pd.DataFrame(data,columns=["ot","Open","High","Low","Close","Vol","c","d","e","f","g","h"])
                    for c in ["Open","High","Low","Close"]: df[c]=pd.to_numeric(df[c],errors='coerce')+CONFIG["OFFSET"]
                    df["Time"]=pd.to_datetime(df["ot"],unit='ms',utc=True)
                    df=df.set_index("Time")
                    return gold_price, df
                except: continue
        return gold_price, None

def get_paxg_safe_hybrid(fetcher, interval="5m", limit=300):
    gold_price, df_klines = fetcher.get_gold_and_klines()
    if df_klines is not None and not df_klines.empty and len(df_klines)>20:
        print(f"✅ Klines dari AntiBlokir: {len(df_klines)} candle")
        return df_klines.tail(limit)
    for attempt in range(3):
        try:
            if attempt==0 and gold_price:
                p=float(gold_price)+CONFIG["OFFSET"]
                df=pd.DataFrame([{"ot":int(time.time()*1000)-i*300000,"Close":p,"High":p+random.uniform(0.3,1.2),"Low":p-random.uniform(0.3,1.2),"Open":p+random.uniform(-0.5,0.5)} for i in range(limit)])
                df["Time"]=pd.to_datetime(df["ot"],unit='ms',utc=True)
                print(f"✅ Gold-API spot: {p:.2f}")
                return df.set_index("Time")
            else:
                import yfinance as yf; time.sleep(0.8)
                sym = "PAXG-USD" if attempt==1 else "GC=F"
                df=yf.download(sym,period="5d",interval="5m" if interval=="5m" else "60m",progress=False,auto_adjust=True)
                if not df.empty:
                    if hasattr(df.columns,'get_level_values'):
                        try: df.columns=df.columns.get_level_values(0)
                        except: pass
                    for c in ["Open","High","Low","Close"]:
                        if c in df.columns: df[c]+=CONFIG["OFFSET"]
                    df.index=pd.to_datetime(df.index,utc=True)
                    print(f"✅ yfinance {sym}: {len(df)} candle")
                    return df.tail(limit)
        except Exception as e:
            print(f"Warung {attempt} tutup: {e}"); continue
    return pd.DataFrame()

def get_yf_safe(sym):
    try:
        import yfinance as yf; time.sleep(0.6)
        df=yf.download(sym,period="10d",interval="60m",progress=False,auto_adjust=True)
        if hasattr(df.columns,'get_level_values'):
            try: df.columns=df.columns.get_level_values(0)
            except: pass
        return df.dropna()
    except:
        return pd.DataFrame()

class EnsembleV8_8:
    def __init__(self):
        self.prices = deque(maxlen=200)
        
    def preload(self, m5_df):
        """FIX: preload 200 harga dari klines biar MA/MACD gak 0.5 terus"""
        try:
            closes = m5_df['Close'].tail(200).tolist()
            for p in closes:
                self.prices.append(float(p))
            print(f"📈 Preload {len(closes)} harga ke ensemble untuk MA/MACD")
        except Exception as e:
            print(f"Preload gagal: {e}")
        
    def update(self, price):
        self.prices.append(price)
    
    def engine_1_ma_trend(self):
        if len(self.prices) < 50: return 0.5, "RANGING"
        prices = np.array(self.prices)
        ma20 = np.mean(prices[-20:])
        ma50 = np.mean(prices[-50:])
        ma200 = np.mean(prices[-200:]) if len(prices)>=200 else np.mean(prices)
        if ma20 > ma50 > ma200:
            strength = min((ma20-ma200)/ma200*100/5, 1.0)
            return 0.5 + strength*0.4, "STRONG_UP" if strength>0.7 else "UP"
        elif ma20 < ma50 < ma200:
            strength = min((ma200-ma20)/ma200*100/5, 1.0)
            return 0.5 - strength*0.4, "STRONG_DOWN" if strength>0.7 else "DOWN"
        else:
            return 0.5, "RANGING"
    
    def engine_2_macd_real(self):
        if len(self.prices) < 35: return 0.5
        prices = pd.Series(list(self.prices))
        ema12 = prices.ewm(span=12).mean().iloc[-1]
        ema26 = prices.ewm(span=26).mean().iloc[-1]
        macd = ema12 - ema26
        if macd > 0 and ema12 > ema26: return 0.62
        elif macd < 0 and ema12 < ema26: return 0.38
        else: return 0.5
    
    def engine_3_ofi(self, ofi):
        return 0.5 + np.clip(ofi*0.6, -0.4, 0.4)
    
    def engine_4_tvi(self):
        if len(self.prices) < 20: return 0.5
        diffs = np.diff(list(self.prices)[-20:])
        up = np.sum(diffs>0); down = np.sum(diffs<0)
        tvi = (up-down)/(up+down+1e-9)
        return 0.5 + tvi*0.35
    
    def engine_5_vol_regime(self):
        if len(self.prices) < 20: return 0.5, 2.5
        atr = float(np.std(list(self.prices)[-20:])*2.2)
        if atr > 5.0: return 0.58, atr
        elif atr < 1.5: return 0.48, atr
        else: return 0.52, atr
    
    def final_prob(self, ofi, colony_pct):
        """FIX: colony_pct boost conf kalo 100% SELL"""
        p1, trend = self.engine_1_ma_trend()
        p2 = self.engine_2_macd_real()
        p3 = self.engine_3_ofi(ofi)
        p4 = self.engine_4_tvi()
        p5, atr = self.engine_5_vol_regime()
        final = p1*0.30 + p2*0.20 + p3*0.25 + p4*0.15 + p5*0.10
        conf_ensemble = abs(final-0.5)*2
        # FIX: colony 100% = conf 100%!
        conf_colony = colony_pct/100.0
        # Gabung: ambil max
        conf = max(conf_ensemble, conf_colony)
        # OFI kuat -0.43 harus boost final prob ke arah SELL
        if ofi < -0.3 and final > 0.4:  # OFI SELL kuat tapi prob masih 0.44
            final = final - 0.15  # Dorong ke SELL
            print(f"🔥 OFI SELL kuat {ofi:+.2f} boost final prob {final+0.15:.2f} -> {final:.2f}")
        if ofi > 0.3 and final < 0.6:
            final = final + 0.15
            print(f"🔥 OFI BUY kuat {ofi:+.2f} boost final prob {final-0.15:.2f} -> {final:.2f}")
        return final, trend, atr, conf, (p1,p2,p3,p4,p5)

def get_tp_sl_runner(price, signal, trend, atr, m5):
    try:
        df = m5.tail(20)
        recent_high = df['High'].max()
        recent_low = df['Low'].min()
        if signal==1:
            if "STRONG" in trend: sl_dist = atr*2.8+5.0
            elif trend=="UP": sl_dist = atr*2.2+3.0
            else: sl_dist = atr*1.8+2.0
            sl_dist = max(8, min(sl_dist, 25))
            sl = price - sl_dist
            sl = max(sl, recent_low - 2)
            if "STRONG" in trend:
                tp1=price+sl_dist*1.8; tp2=price+sl_dist*4.5; tp3=price+sl_dist*7.0
            elif trend=="UP":
                tp1=price+sl_dist*1.6; tp2=price+sl_dist*3.2; tp3=price+sl_dist*5.0
            else:
                tp1=price+sl_dist*1.5; tp2=price+sl_dist*2.2; tp3=price+sl_dist*3.0
        else:
            if "STRONG" in trend: sl_dist = atr*2.8+5.0
            elif "DOWN" in trend: sl_dist = atr*2.2+3.0
            else: sl_dist = atr*1.8+2.0
            sl_dist = max(8, min(sl_dist, 25))
            sl = price + sl_dist
            sl = min(sl, recent_high + 2)
            if "STRONG" in trend:
                tp1=price-sl_dist*1.8; tp2=price-sl_dist*4.5; tp3=price-sl_dist*7.0
            elif "DOWN" in trend:
                tp1=price-sl_dist*1.6; tp2=price-sl_dist*3.2; tp3=price-sl_dist*5.0
            else:
                tp1=price-sl_dist*1.5; tp2=price-sl_dist*2.2; tp3=price-sl_dist*3.0
        tp1_dist = abs(tp1-price); tp2_dist = abs(tp2-price); tp3_dist = abs(tp3-price)
        tp1_dist = max(8, min(tp1_dist, 60))
        tp2_dist = max(20, min(tp2_dist, 150))
        tp3_dist = max(40, min(tp3_dist, 300))
        if signal==1:
            tp1=price+tp1_dist; tp2=price+tp2_dist; tp3=price+tp3_dist
        else:
            tp1=price-tp1_dist; tp2=price-tp2_dist; tp3=price-tp3_dist
        return sl, tp1, tp2, tp3, sl_dist, tp1_dist, tp2_dist, tp3_dist
    except Exception as e:
        print(f"TP runner error {e}, fallback")
        atr = max(2.0, atr)
        sl_dist = atr*1.2; tp1_dist=atr*1.0; tp2_dist=atr*2.0; tp3_dist=atr*4.0
        if signal==1:
            sl=price-sl_dist; tp1=price+tp1_dist; tp2=price+tp2_dist; tp3=price+tp3_dist
        else:
            sl=price+sl_dist; tp1=price-tp1_dist; tp2=price-tp2_dist; tp3=price-tp3_dist
        return sl, tp1, tp2, tp3, sl_dist, tp1_dist, tp2_dist, tp3_dist

class AntiSpamV8_8:
    def __init__(self):
        self.last_sent = 0
        self.hour_count = deque(maxlen=20)
        self.sent_hashes = set()
    
    def allow(self, price, signal, conf, trend, final_prob, colony_pct):
        now = time.time()
        # FIX: Kalo colony 100% RAYA, bypass conf check!
        is_strong_colony = colony_pct >= CONFIG["QUORUM_RAYA"]
        if is_strong_colony:
            print(f"💪 Colony kuat {colony_pct:.0f}% >= {CONFIG['QUORUM_RAYA']}% - bypass conf check!")
            conf = max(conf, 0.75)  # Force conf tinggi
        
        cooldown = CONFIG["COOLDOWN_KECIL"] if "KECIL" in str(trend) or not is_strong_colony else CONFIG["COOLDOWN_RAYA"]
        if now - self.last_sent < cooldown and not is_strong_colony:
            return False, f"Cooldown {cooldown/60:.0f}m"
        self.hour_count = deque([t for t in self.hour_count if now-t < 3600], maxlen=20)
        if len(self.hour_count) >= CONFIG["MAX_SIGNALS_PER_HOUR"]:
            return False, f"Max {CONFIG['MAX_SIGNALS_PER_HOUR']}/jam"
        # FIX: Ranging low conf hanya blok kalo colony lemah <32%
        if final_prob > 0.42 and final_prob < 0.58 and colony_pct < CONFIG["QUORUM_KECIL"]:
            return False, f"Ranging low conf {final_prob*100:.0f}% + colony lemah {colony_pct:.0f}%"
        if conf < CONFIG["CONF_THRESHOLD"] and not is_strong_colony:
            return False, f"Conf {conf*100:.0f}% < {CONFIG['CONF_THRESHOLD']*100:.0f}% + colony {colony_pct:.0f}%"
        h = hashlib.md5(f"{price:.1f}-{signal}-{trend}-{final_prob:.2f}".encode()).hexdigest()
        if h in self.sent_hashes:
            return False, "Duplicate signal"
        utc_h = datetime.now(timezone.utc).hour
        if utc_h >=17 and utc_h <=22 and trend=="RANGING" and not is_strong_colony:
            return False, "Silent Asia 00-05 WIB RANGING lemah"
        self.last_sent = now
        self.hour_count.append(now)
        self.sent_hashes.add(h)
        if len(self.sent_hashes)>100:
            self.sent_hashes.clear()
        return True, "PASS"

def send_foto_v8_8(jenis, keputusan, buy_pct, sell_pct, entry, sl, tp1, tp2, tp3, lot, gudang, memory, lap_pemetik, lap_mandor, lap_pembajak, lap_penuai, price, top_str, atr, kondisi, sl_dist, tp1_dist, tp2_dist, tp3_dist, final_prob, trend, ofi, conf, breakdown):
    token=os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    chat=os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print(f"{jenis} {keputusan} {buy_pct:.0f}% vs {sell_pct:.0f}% ENTRY {entry:.2f} SL {sl:.2f} TP {tp3:.2f}")
        return
    try:
        photo_url="https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800"
        pct = buy_pct if keputusan=="BUY" else sell_pct
        p1,p2,p3,p4,p5 = breakdown
        if jenis=="PANEN RAYA" or "STRONG" in trend:
            emoji="🌾👑🔥"
            bar="🟩"*min(10, memory['gudang']//15) + "⬜"*(10-min(10, memory['gudang']//15))
        else:
            emoji="🌿"
            bar="🟨"*min(10, memory['gudang']//15) + "⬜"*(10-min(10, memory['gudang']//15))
        direction = "BUY 🟢" if keputusan=="BUY" else "SELL 🔴"
        caption=f"""{emoji} V8.8.1 FIX {jenis} {keputusan} {pct:.0f}% - {buy_pct:.0f}% vs {sell_pct:.0f}%
{direction} {trend} | Conf {conf*100:.0f}% | FinalProb {final_prob*100:.0f}% | OFI {ofi:+.2f}

📊 COLONY 31 ENGINE (25 TANI + 6 V5)
🌿 Pemetik {lap_pemetik['BUY']}B {lap_pemetik['SELL']}S
👨‍🌾 Mandor {lap_mandor['BUY']}B {lap_mandor['SELL']}S
🚜 Pembajak {lap_pembajak['BUY']}B {lap_pembajak['SELL']}S
🌾 Penuai {lap_penuai['BUY']}B {lap_penuai['SELL']}S
🧠 MA {p1*100:.0f}% MACD {p2*100:.0f}% OFI {p3*100:.0f}% TVI {p4*100:.0f}% VOL {p5*100:.0f}%

💰 OP MT5 - {kondisi} | ATR {atr:.2f}$ | RR 1:{tp3_dist/sl_dist:.1f}
ENTRY: {entry:.2f}
SL: {sl:.2f} (-{sl_dist:.1f}$)
TP1: {tp1:.2f} (+{tp1_dist:.1f}$) 1:1.8
TP2: {tp2:.2f} (+{tp2_dist:.1f}$) 1:4.5 RUNNER
TP3: {tp3:.2f} (+{tp3_dist:.1f}$) 1:7.0 MEGA RUNNER
Lot: {lot} | Offset {CONFIG['OFFSET']}

🏚️ GUDANG {bar} {gudang}$
Kecil {memory['panen_kecil']}x Raya {memory['panen_raya']}x | Evo {memory.get('evolutions',0)}x

🧬 TOP: {top_str}
🛡️ Anti Blokir OK + Anti Spam OK | Conf {conf*100:.0f}%

✅ V8.8.1 FIX 100% SELL KE-KIRIM!
#TANI #XAUUSD #{keputusan}"""
        requests.post(f"https://api.telegram.org/bot{token}/sendPhoto",json={"chat_id":chat,"photo":photo_url,"caption":caption},timeout=15)
        print(f"Foto V8.8.1 terkirim: {jenis} {keputusan} {pct:.0f}% Conf {conf*100:.0f}%")
    except Exception as e:
        print(f"Gagal kirim foto V8.8.1: {e}")

def load_json(path, default):
    if os.path.exists(path):
        try: return json.load(open(path))
        except: return default
    return default
def save_json(path, data):
    try: json.dump(data, open(path,'w'))
    except: pass

def init_dna():
    dna={}
    for i in range(CONFIG["PEMETIK"]):
        dna[f"pemetik_{i}"]={"jabatan":"Pemetik","kekuatan":random.randint(50,70),"ketajaman":random.randint(55,75),"stamina_max":100,"keberuntungan":random.randint(50,70),"skor":0,"panen":0,"alat_lv":1,"tenaga":100}
    for i in range(CONFIG["MANDOR"]):
        dna[f"mandor_{i}"]={"jabatan":"Mandor","kekuatan":random.randint(65,80),"ketajaman":random.randint(70,85),"stamina_max":120,"keberuntungan":random.randint(60,80),"skor":5,"panen":0,"alat_lv":2,"tenaga":120}
    for i in range(CONFIG["PEMBAJAK"]):
        dna[f"pembajak_{i}"]={"jabatan":"Pembajak","kekuatan":random.randint(75,90),"ketajaman":random.randint(80,90),"stamina_max":150,"keberuntungan":random.randint(65,85),"skor":10,"panen":0,"alat_lv":2,"tenaga":150}
    for i in range(CONFIG["PENUAI"]):
        dna[f"penuai_{i}"]={"jabatan":"Penuai","kekuatan":random.randint(80,95),"ketajaman":random.randint(85,95),"stamina_max":200,"keberuntungan":random.randint(70,90),"skor":15,"panen":0,"alat_lv":3,"tenaga":200}
    return dna

def logic_pemetik(m5, idx, alat_lv, tenaga):
    if tenaga < 10: return "NEUTRAL"
    try:
        e10=m5['Close'].ewm(10).mean().iloc[-1]; e30=m5['Close'].ewm(30).mean().iloc[-1]
        e20=m5['Close'].ewm(20).mean().iloc[-1]; e50=m5['Close'].ewm(50).mean().iloc[-1]
        if idx<=4:
            if idx==0:
                last=m5.tail(15)
                for j in range(len(last)-3,1,-1):
                    if last['Low'].iloc[j]-last['High'].iloc[j-2]>=CONFIG["MIN_FVG"]: return "BUY"
                    if last['Low'].iloc[j-2]-last['High'].iloc[j]>=CONFIG["MIN_FVG"]: return "SELL"
                return "BUY" if e20>e50 else "SELL"
            else:
                return "BUY" if e20>e50 else "SELL"
        else:
            return "BUY" if e10>e30 else "SELL"
    except:
        return random.choice(["BUY","SELL"])

def logic_mandor(m5, idx, laporan_pemetik):
    try:
        e20=m5['Close'].ewm(20).mean().iloc[-1]; e50=m5['Close'].ewm(50).mean().iloc[-1]
        trend="BUY" if e20>e50 else "SELL"
        buy=laporan_pemetik["BUY"]; sell=laporan_pemetik["SELL"]
        if buy>sell: return "BUY"
        if sell>buy: return "SELL"
        return trend
    except:
        return random.choice(["BUY","SELL"])

def logic_pembajak(m5, h4, dxy, idx, laporan_mandor):
    try:
        e20=m5['Close'].ewm(20).mean().iloc[-1]; e50=m5['Close'].ewm(50).mean().iloc[-1]
        trend="BUY" if e20>e50 else "SELL"
        spread=m5['High'].iloc[-1]-m5['Low'].iloc[-1]
        if spread>CONFIG["MAX_SPREAD"] and idx==2: return "BLOCK"
        return trend
    except:
        return random.choice(["BUY","SELL"])

def logic_penuai(m5, idx, laporan_pembajak):
    try:
        e20=m5['Close'].ewm(20).mean().iloc[-1]; e50=m5['Close'].ewm(50).mean().iloc[-1]
        trend="BUY" if e20>e50 else "SELL"
        b=laporan_pembajak["BUY"]; s=laporan_pembajak["SELL"]
        if b>s: return "BUY"
        if s>b: return "SELL"
        return trend
    except:
        return random.choice(["BUY","SELL"])

def ratu_tani_v8():
    print(f"=== 🌾👑 RATU TANI V8.8.1 FIX 100% SELL BANGUN {datetime.now()} ===")
    print(f"Offset {CONFIG['OFFSET']} | Quorum {CONFIG['QUORUM_KECIL']}/{CONFIG['QUORUM_RAYA']} | Max {CONFIG['MAX_SIGNALS_PER_HOUR']}/jam | Conf >{CONFIG['CONF_THRESHOLD']*100:.0f}%")
    fetcher = AntiBlokirFetcher()
    ensemble = EnsembleV8_8()
    antispam = AntiSpamV8_8()
    dna=load_json(CONFIG["DNA_FILE"], init_dna())
    memory=load_json(CONFIG["MEMORY_FILE"], {"wins":0,"losses":0,"panen_kecil":0,"panen_raya":0,"gudang":0,"evolutions":0})
    last=load_json(CONFIG["LAST_FILE"], {})
    m5=get_paxg_safe_hybrid(fetcher,"5m",300)
    h4=get_paxg_safe_hybrid(fetcher,"4h",120)
    dxy=get_yf_safe("DX-Y.NYB")
    if m5.empty:
        print("🌾 Sawah kosong - Ratu Tani puasa")
        return
    # FIX: preload 200 harga
    ensemble.preload(m5)
    price_for_ensemble = float(m5['Close'].iloc[-1])
    ensemble.update(price_for_ensemble)
    ofi_price, ofi = fetcher.get_ofi()
    if ofi_price is None:
        ofi = 0
        print(f"⚠️ OFI gagal, pake 0")
    else:
        print(f"📊 OFI {ofi:+.2f} dari orderbook")

    # 25 Petani Colony
    laporan_pemetik={"BUY":0,"SELL":0,"NEUTRAL":0}
    logs_pemetik=[]
    for i in range(CONFIG["PEMETIK"]):
        key=f"pemetik_{i}"
        if key not in dna: dna[key]=init_dna()[key]
        v=logic_pemetik(m5,i,dna[key].get("alat_lv",1),dna[key].get("tenaga",100))
        laporan_pemetik[v]+=1
        if v in ["BUY","SELL"]: logs_pemetik.append(f"P{i}:{v[0]}")
        dna[key]["tenaga"]=max(0, dna[key].get("tenaga",100)-5)
    laporan_mandor={"BUY":0,"SELL":0,"NEUTRAL":0}
    logs_mandor=[]
    for i in range(CONFIG["MANDOR"]):
        key=f"mandor_{i}"
        if key not in dna: dna[key]=init_dna()[key]
        v=logic_mandor(m5,i,laporan_pemetik)
        laporan_mandor[v]+=1
        logs_mandor.append(f"M{i}:{v[0]}")
    laporan_pembajak={"BUY":0,"SELL":0,"NEUTRAL":0,"BLOCK":0}
    logs_pembajak=[]
    for i in range(CONFIG["PEMBAJAK"]):
        key=f"pembajak_{i}"
        if key not in dna: dna[key]=init_dna()[key]
        v=logic_pembajak(m5,h4,dxy,i,laporan_mandor)
        laporan_pembajak[v]+=1
        logs_pembajak.append(f"B{i}:{v[0]}")
    laporan_penuai={"BUY":0,"SELL":0,"NEUTRAL":0}
    logs_penuai=[]
    for i in range(CONFIG["PENUAI"]):
        key=f"penuai_{i}"
        if key not in dna: dna[key]=init_dna()[key]
        v=logic_penuai(m5,i,laporan_pembajak)
        laporan_penuai[v]+=1
        logs_penuai.append(f"N{i}:{v[0]}")

    if laporan_pembajak["BLOCK"]>=3:
        print(f"🚫 TRAKTOR BLOCK spread {m5['High'].iloc[-1]-m5['Low'].iloc[-1]:.2f}")
        return

    total_all=25
    total_buy=laporan_pemetik["BUY"]+laporan_mandor["BUY"]+laporan_pembajak["BUY"]+laporan_penuai["BUY"]
    total_sell=laporan_pemetik["SELL"]+laporan_mandor["SELL"]+laporan_pembajak["SELL"]+laporan_penuai["SELL"]
    buy_pct=total_buy/total_all*100
    sell_pct=total_sell/total_all*100
    colony_pct = max(buy_pct, sell_pct)

    print(f"🌿 Pemetik: BUY {laporan_pemetik['BUY']} SELL {laporan_pemetik['SELL']} | {' '.join(logs_pemetik)}")
    print(f"👨‍🌾 Mandor: BUY {laporan_mandor['BUY']} SELL {laporan_mandor['SELL']} | {' '.join(logs_mandor)}")
    print(f"🚜 Pembajak: BUY {laporan_pembajak['BUY']} SELL {laporan_pembajak['SELL']} BLOCK {laporan_pembajak['BLOCK']} | {' '.join(logs_pembajak)}")
    print(f"🌾 Penuai: BUY {laporan_penuai['BUY']} SELL {laporan_penuai['SELL']} | {' '.join(logs_penuai)}")
    print(f"👑 TOTAL: BUY {total_buy}/{total_all}={buy_pct:.0f}% SELL {total_sell}/{total_all}={sell_pct:.0f}% Colony {colony_pct:.0f}%")

    final_prob, trend, atr_ensemble, conf, breakdown = ensemble.final_prob(ofi, colony_pct)
    p1,p2,p3,p4,p5 = breakdown
    print(f"🧠 Ensemble: Prob {final_prob*100:.0f}% Trend {trend} Conf {conf*100:.0f}% (colony {colony_pct:.0f}% + ensemble) ATR {atr_ensemble:.2f} | MA {p1*100:.0f}% MACD {p2*100:.0f}% OFI {p3*100:.0f}% TVI {p4*100:.0f}% VOL {p5*100:.0f}%")

    ensemble_buy = final_prob > 0.58
    ensemble_sell = final_prob < 0.42
    keputusan=None; jenis=None
    if buy_pct>=CONFIG["QUORUM_KECIL"] or ensemble_buy: keputusan="BUY"; jenis="PANEN KECIL"
    if sell_pct>=CONFIG["QUORUM_KECIL"] or ensemble_sell: keputusan="SELL"; jenis="PANEN KECIL"
    if buy_pct>=CONFIG["QUORUM_RAYA"] or (ensemble_buy and final_prob>0.68): keputusan="BUY"; jenis="PANEN RAYA"
    if sell_pct>=CONFIG["QUORUM_RAYA"] or (ensemble_sell and final_prob<0.32): keputusan="SELL"; jenis="PANEN RAYA"

    if not keputusan:
        print(f"Ratu: quorum {CONFIG['QUORUM_KECIL']}% belum tercapai BUY {buy_pct:.0f}% SELL {sell_pct:.0f}% + Ensemble {final_prob*100:.0f}% {trend}")
        for k in dna: dna[k]["tenaga"]=min(dna[k].get("stamina_max",100), dna[k].get("tenaga",100)+15)
        save_json(CONFIG["DNA_FILE"], dna)
        return

    signal_code = 1 if keputusan=="BUY" else -1
    allow, reason = antispam.allow(price_for_ensemble, signal_code, conf, trend, final_prob, colony_pct)
    if not allow:
        print(f"🚫 ANTI SPAM SKIP: {reason} | Prob {final_prob*100:.0f}% Conf {conf*100:.0f}% {trend} OFI {ofi:+.2f} Colony {colony_pct:.0f}%")
        return

    cooldown=CONFIG["COOLDOWN_KECIL"] if jenis=="PANEN KECIL" else CONFIG["COOLDOWN_RAYA"]
    if last.get("keputusan")==keputusan and last.get("jenis")==jenis and abs(time.time()-last.get("time",0))<cooldown:
        print(f"Ratu: {jenis} {keputusan} udah {cooldown/60:.0f} menit lalu skip")
        return

    for k in dna:
        try:
            if "pemetik" in k: v=logic_pemetik(m5,int(k.split("_")[1]),dna[k].get("alat_lv",1),dna[k].get("tenaga",100))
            elif "mandor" in k: v=logic_mandor(m5,int(k.split("_")[1]),laporan_pemetik)
            elif "pembajak" in k: v=logic_pembajak(m5,h4,dxy,int(k.split("_")[1]),laporan_mandor)
            else: v=logic_penuai(m5,int(k.split("_")[1]),laporan_pembajak)
            if v==keputusan:
                dna[k]["skor"]=dna[k].get("skor",0)+(2 if jenis=="PANEN RAYA" or "STRONG" in trend else 1)
                dna[k]["panen"]=dna[k].get("panen",0)+1
                dna[k]["tenaga"]=min(dna[k].get("stamina_max",100), dna[k].get("tenaga",100)+15)
                if dna[k]["panen"]%3==0 and dna[k].get("alat_lv",1)<5:
                    dna[k]["alat_lv"]=dna[k].get("alat_lv",1)+1
                    memory["evolutions"]=memory.get("evolutions",0)+1
                    print(f"🧬 EVOLUSI! {k} naik Lv{dna[k]['alat_lv']}")
        except: pass
    save_json(CONFIG["DNA_FILE"], dna)

    price = float(m5['Close'].iloc[-1])
    sl, tp1, tp2, tp3, sl_dist, tp1_dist, tp2_dist, tp3_dist = get_tp_sl_runner(price, signal_code, trend, atr_ensemble, m5)
    if jenis=="PANEN KECIL":
        lot="0.05"; add=15
    else:
        lot="0.10"; add=32
    if atr_ensemble < 1.5:
        kondisi = "SEPI 😐"
    elif atr_ensemble < 3:
        kondisi = "NORMAL 🙂"
    elif atr_ensemble < 5:
        kondisi = "RAME 🔥"
    else:
        kondisi = "NEWS 🌪️"
    memory["gudang"]+=add
    if jenis=="PANEN KECIL": memory["panen_kecil"]+=1
    else: memory["panen_raya"]+=1
    save_json(CONFIG["MEMORY_FILE"], memory)
    top3=sorted(dna.items(),key=lambda x: x[1].get("skor",0),reverse=True)[:3]
    top_str=" | ".join([f"{k}:{v.get('skor',0):.0f} Lv{v.get('alat_lv',1)}" for k,v in top3])
    send_foto_v8_8(jenis, keputusan, buy_pct, sell_pct, price, sl, tp1, tp2, tp3, lot, memory['gudang'], memory, laporan_pemetik, laporan_mandor, laporan_pembajak, laporan_penuai, price, top_str, atr_ensemble, kondisi, sl_dist, tp1_dist, tp2_dist, tp3_dist, final_prob, trend, ofi, conf, breakdown)
    save_json(CONFIG["LAST_FILE"], {"keputusan":keputusan,"jenis":jenis,"time":time.time(),"price":price,"conf":conf,"trend":trend})

if __name__=="__main__":
    ratu_tani_v8()
