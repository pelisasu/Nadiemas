"""
🌾👑 TANI V8.9 HEADWAY DIRECT AUTO - GITHUB LANGSUNG OP MT5 TANPA APK!
- User cuma masukin MT5 ID + Password di GitHub Secrets
- GitHub Actions (windows-latest) yang OP langsung ke Headway MT5
- Gak perlu on terus, cuma jalan pas sinyal (tiap 30 menit)
- Sama kayak OP manual, tapi otomatis!

Headway Server: Headway-Real / Headway-Demo / Headway-Real2
Symbol Headway: GOLD (bukan XAUUSD)
"""

import os, json, random, time, hashlib, requests, pandas as pd
from collections import deque
from datetime import datetime, timezone, timedelta
import numpy as np

CONFIG={
    "OFFSET": -2.25,
    "DNA_FILE": ".dna_tani_v8.json",
    "MEMORY_FILE": ".memory_tani_v8.json",
    "LAST_FILE": ".last_tani_v8.json",
    "OFFSET_FILE": ".offset_history.json",
    "TRADE_HISTORY_FILE": ".trade_history_headway.json",
    "PEMETIK": 10, "MANDOR": 5, "PEMBAJAK": 5, "PENUAI": 5,
    "QUORUM_KECIL": 32, "QUORUM_RAYA": 55,
    "MAX_SPREAD": 9.0, "MIN_FVG": 0.4,
    "MAX_SIGNALS_PER_HOUR": 4, "CONF_THRESHOLD": 0.68,
    "COOLDOWN_KECIL": 900, "COOLDOWN_RAYA": 1800,
    "AUTO_TRADE_ENABLED": os.getenv("AUTO_TRADE_ENABLED", "false").lower() == "true",
    "AUTO_TRADE_MIN_CONF": 70,  # Conf 70% baru auto OP (lu bisa ubah 75/80)
    "AUTO_TRADE_MIN_COLONY": 50,
    "AUTO_TRADE_LOT_KECIL": 0.05,
    "AUTO_TRADE_LOT_RAYA": 0.10,
}

random.seed(int(time.time())%99999)

def is_weekend_off():
    now_utc = datetime.now(timezone.utc)
    now_wib = now_utc + timedelta(hours=7)
    wd = now_utc.weekday()
    h_utc = now_utc.hour
    if wd == 4 and h_utc >= 21: return True, f"Weekend OFF - Jumat {h_utc}:00 UTC = Sabtu 04:00 WIB tutup"
    if wd == 5: return True, f"Weekend OFF - Sabtu, pasar XAUUSD tutup"
    if wd == 6 and h_utc < 22: return True, f"Weekend OFF - Minggu {h_utc}:00 UTC, buka Senin 05:00 WIB"
    return False, f"Market ON - {now_wib.strftime('%A %H:%M')} WIB"

def load_json(path, default):
    if os.path.exists(path):
        try: return json.load(open(path))
        except: return default
    return default
def save_json(path, data):
    try: json.dump(data, open(path,'w'))
    except: pass

class AntiBlokirFetcher:
    def __init__(self):
        self.cache = {}; self.cache_time = {}
        self.ua_list = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36","Mozilla/5.0 (iPhone)","Mozilla/5.0 (X11; Linux x86_64)"]
        self.endpoints_paxg_depth = ["https://api.binance.com/api/v3/depth?symbol=PAXGUSDT&limit=20","https://api1.binance.com/api/v3/depth?symbol=PAXGUSDT&limit=20","https://data-api.binance.vision/api/v3/depth?symbol=PAXGUSDT&limit=20","https://data-api.binance.vision/api/v3/depth?symbol=PAXGUSDT&limit=20"]
        self.endpoints_paxg_klines = ["https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=100","https://api1.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=100","https://data-api.binance.vision/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=100"]
        self.endpoints_gold = ["https://api.gold-api.com/price/XAU"]
    def _get(self, url, cache_key, ttl=2):
        now = time.time()
        if cache_key in self.cache and now - self.cache_time.get(cache_key,0) < ttl: return self.cache[cache_key]
        try:
            headers = {"User-Agent": random.choice(self.ua_list), "Accept": "application/json"}
            time.sleep(random.uniform(0.1,0.4))
            r = requests.get(url, headers=headers, timeout=7)
            if r.status_code==200:
                data=r.json(); self.cache[cache_key]=data; self.cache_time[cache_key]=now; return data
        except: pass
        return None
    def get_ofi(self):
        random.shuffle(self.endpoints_paxg_depth)
        for url in self.endpoints_paxg_depth:
            data=self._get(url,"ofi",2)
            if data and 'bids' in data:
                try:
                    bids=data['bids']; asks=data['asks']
                    bv=sum(float(q) for _,q in bids[:5]); av=sum(float(q) for _,q in asks[:5])
                    ofi=(bv-av)/(bv+av+1e-9); price=(float(bids[0][0])+float(asks[0][0]))/2
                    return price+CONFIG["OFFSET"], ofi
                except: continue
        return None,0
    def get_gold_and_klines(self):
        random.shuffle(self.endpoints_gold); gold_price=None
        for url in self.endpoints_gold:
            data=self._get(url,"gold",3)
            if data and isinstance(data,dict) and 'price' in data:
                try: gold_price=float(data['price']); break
                except: continue
        random.shuffle(self.endpoints_paxg_klines)
        for url in self.endpoints_paxg_klines:
            data=self._get(url,"klines",5)
            if isinstance(data,list) and len(data)>20:
                try:
                    df=pd.DataFrame(data,columns=["ot","Open","High","Low","Close","Vol","c","d","e","f","g","h"])
                    for c in ["Open","High","Low","Close"]: df[c]=pd.to_numeric(df[c],errors='coerce')+CONFIG["OFFSET"]
                    df["Time"]=pd.to_datetime(df["ot"],unit='ms',utc=True); df=df.set_index("Time")
                    return gold_price, df
                except: continue
        return gold_price, None

def get_paxg_safe_hybrid(fetcher, limit=300):
    gold_price, df_klines = fetcher.get_gold_and_klines()
    if df_klines is not None and not df_klines.empty and len(df_klines)>20:
        print(f"✅ Klines AntiBlokir: {len(df_klines)} candle"); return df_klines.tail(limit)
    for attempt in range(3):
        try:
            if attempt==0 and gold_price:
                p=float(gold_price)+CONFIG["OFFSET"]
                df=pd.DataFrame([{"ot":int(time.time()*1000)-i*300000,"Close":p,"High":p+random.uniform(0.3,1.2),"Low":p-random.uniform(0.3,1.2),"Open":p+random.uniform(-0.5,0.5)} for i in range(limit)])
                df["Time"]=pd.to_datetime(df["ot"],unit='ms',utc=True); return df.set_index("Time")
            else:
                import yfinance as yf; time.sleep(0.8); sym="PAXG-USD" if attempt==1 else "GC=F"
                df=yf.download(sym,period="5d",interval="5m",progress=False,auto_adjust=True)
                if not df.empty:
                    if hasattr(df.columns,'get_level_values'):
                        try: df.columns=df.columns.get_level_values(0)
                        except: pass
                    for c in ["Open","High","Low","Close"]:
                        if c in df.columns: df[c]+=CONFIG["OFFSET"]
                    df.index=pd.to_datetime(df.index,utc=True); return df.tail(limit)
        except: continue
    return pd.DataFrame()

def get_yf_safe(sym):
    try:
        import yfinance as yf; time.sleep(0.6)
        df=yf.download(sym,period="10d",interval="60m",progress=False,auto_adjust=True)
        if hasattr(df.columns,'get_level_values'):
            try: df.columns=df.columns.get_level_values(0)
            except: pass
        return df.dropna()
    except: return pd.DataFrame()

class EnsembleV8:
    def __init__(self): self.prices=deque(maxlen=200)
    def preload(self, m5_df):
        try:
            for p in m5_df['Close'].tail(200).tolist(): self.prices.append(float(p))
        except: pass
    def update(self, price): self.prices.append(price)
    def engine_1_ma_trend(self):
        if len(self.prices)<50: return 0.5,"RANGING"
        prices=np.array(self.prices); ma20=np.mean(prices[-20:]); ma50=np.mean(prices[-50:]); ma200=np.mean(prices[-200:]) if len(prices)>=200 else np.mean(prices)
        if ma20>ma50>ma200: strength=min((ma20-ma200)/ma200*100/5,1.0); return 0.5+strength*0.4,"STRONG_UP" if strength>0.7 else "UP"
        elif ma20<ma50<ma200: strength=min((ma200-ma20)/ma200*100/5,1.0); return 0.5-strength*0.4,"STRONG_DOWN" if strength>0.7 else "DOWN"
        else: return 0.5,"RANGING"
    def engine_2_macd_real(self):
        if len(self.prices)<35: return 0.5
        prices=pd.Series(list(self.prices)); ema12=prices.ewm(span=12).mean().iloc[-1]; ema26=prices.ewm(span=26).mean().iloc[-1]
        return 0.62 if ema12>ema26 else 0.38 if ema12<ema26 else 0.5
    def engine_3_ofi(self, ofi): return 0.5+np.clip(ofi*0.6,-0.4,0.4)
    def engine_4_tvi(self):
        if len(self.prices)<20: return 0.5
        diffs=np.diff(list(self.prices)[-20:]); up=np.sum(diffs>0); down=np.sum(diffs<0); return 0.5+(up-down)/(up+down+1e-9)*0.35
    def engine_5_vol_regime(self):
        if len(self.prices)<20: return 0.5,2.5
        atr=float(np.std(list(self.prices)[-20:])*2.2)
        return (0.58,atr) if atr>5 else (0.48,atr) if atr<1.5 else (0.52,atr)
    def final_prob(self, ofi, colony_pct):
        p1,trend=self.engine_1_ma_trend(); p2=self.engine_2_macd_real(); p3=self.engine_3_ofi(ofi); p4=self.engine_4_tvi(); p5,atr=self.engine_5_vol_regime()
        final=p1*0.30+p2*0.20+p3*0.25+p4*0.15+p5*0.10
        conf=max(abs(final-0.5)*2, colony_pct/100.0)
        if ofi<-0.3 and final>0.4: final-=0.15
        if ofi>0.3 and final<0.6: final+=0.15
        return final,trend,atr,conf,(p1,p2,p3,p4,p5)

def get_tp_sl_runner(price, signal, trend, atr, m5):
    sl_dist=max(8,min(atr*2.8+5.0 if "STRONG" in trend else atr*2.2+3.0,25))
    tp1_dist=max(8,min(sl_dist*1.8,60)); tp2_dist=max(20,min(sl_dist*4.5,150)); tp3_dist=max(40,min(sl_dist*7.0,300))
    if signal==1: return price-sl_dist, price+tp1_dist, price+tp2_dist, price+tp3_dist, sl_dist, tp1_dist, tp2_dist, tp3_dist
    else: return price+sl_dist, price-tp1_dist, price-tp2_dist, price-tp3_dist, sl_dist, tp1_dist, tp2_dist, tp3_dist

class AntiSpamV8:
    def __init__(self): self.last_sent=0; self.hour_count=deque(maxlen=20); self.sent_hashes=set()
    def allow(self, price, signal, conf, trend, final_prob, colony_pct):
        now=time.time(); is_strong=colony_pct>=CONFIG["QUORUM_RAYA"]
        if is_strong: conf=max(conf,0.75)
        self.hour_count=deque([t for t in self.hour_count if now-t<3600],maxlen=20)
        if len(self.hour_count)>=CONFIG["MAX_SIGNALS_PER_HOUR"]: return False,"Max/jam"
        if final_prob>0.42 and final_prob<0.58 and colony_pct<CONFIG["QUORUM_KECIL"]: return False,"Ranging low"
        if conf<CONFIG["CONF_THRESHOLD"] and not is_strong: return False,f"Conf {conf*100:.0f}%"
        h=hashlib.md5(f"{price:.1f}-{signal}-{trend}-{final_prob:.2f}".encode()).hexdigest()
        if h in self.sent_hashes: return False,"Duplicate"
        self.last_sent=now; self.hour_count.append(now); self.sent_hashes.add(h)
        return True,"PASS"

def send_foto(jenis, keputusan, buy_pct, sell_pct, entry, sl, tp1, tp2, tp3, lot, gudang, memory, lp, lm, lb, ln, price, top_str, atr, kondisi, sl_dist, tp1_dist, tp2_dist, tp3_dist, final_prob, trend, ofi, conf, breakdown, auto_result=None):
    token=os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN"); chat=os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat: print(f"{jenis} {keputusan} ENTRY {entry:.2f}"); return
    try:
        p1,p2,p3,p4,p5=breakdown; pct=buy_pct if keputusan=="BUY" else sell_pct
        emoji="🌾👑🔥" if jenis=="PANEN RAYA" else "🌿"; bar="🟩"*min(10,memory['gudang']//15)+"⬜"*(10-min(10,memory['gudang']//15))
        auto_text=""
        if auto_result:
            if auto_result.get("success"):
                auto_text=f"\n🤖 AUTO OP HEADWAY SUKSES!\n🎫 Ticket {auto_result.get('ticket')} | {auto_result.get('msg')}\n💰 Langsung OP di MT5 lu!"
            else:
                auto_text=f"\n⚠️ AUTO OP: {auto_result.get('msg')}"
        caption=f"{emoji} V8.9 {jenis} {keputusan} {pct:.0f}%\n{'BUY 🟢' if keputusan=='BUY' else 'SELL 🔴'} {trend} Conf {conf*100:.0f}% Prob {final_prob*100:.0f}% OFI {ofi:+.2f}\nENTRY {entry:.2f} SL {sl:.2f} TP1 {tp1:.2f} TP2 {tp2:.2f} TP3 {tp3:.2f} Lot {lot}\nGUDANG {bar} {gudang}$ {auto_text}"
        requests.post(f"https://api.telegram.org/bot{token}/sendPhoto",json={"chat_id":chat,"photo":"https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800","caption":caption},timeout=15)
    except Exception as e: print(f"Gagal foto {e}")

def send_weekend_check(price_paxg, price_mt5_est, ofi, memory, dna, offset_history):
    token=os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN"); chat=os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat: return
    try:
        gudang=memory.get('gudang',0); avg_offset=sum([x['offset'] for x in offset_history[-10:]])/len(offset_history[-10:]) if offset_history else CONFIG["OFFSET"]
        caption=f"🌴 V8.9 WEEKEND HEADWAY\nGudang {gudang}$ PAXG {price_paxg:.2f} MT5 {price_mt5_est:.2f} OFI {ofi:+.2f} Offset {avg_offset:.2f}\nOFF Sabtu 04:00 - Senin 05:00 WIB"
        requests.post(f"https://api.telegram.org/bot{token}/sendPhoto",json={"chat_id":chat,"photo":"https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800","caption":caption},timeout=15)
    except: pass

def auto_trade_headway_direct(keputusan, lot, sl, tp1, entry_price, conf, colony_pct, jenis):
    """GitHub LANGSUNG OP ke Headway MT5 pakai ID+Password - gak perlu on terus!"""
    result={"success": False, "ticket": None, "msg": "Not attempted"}
    if not CONFIG["AUTO_TRADE_ENABLED"]:
        result["msg"]="AUTO_TRADE_ENABLED=false - set true di GitHub Secrets buat auto OP kayak manual"
        print(f"💡 {result['msg']}")
        return result
    if jenis!="PANEN RAYA":
        result["msg"]=f"Skip auto - hanya PANEN RAYA auto, ini {jenis}"
        print(f"🤖 {result['msg']}")
        return result
    if conf*100 < CONFIG["AUTO_TRADE_MIN_CONF"]:
        result["msg"]=f"Conf {conf*100:.0f}% < {CONFIG['AUTO_TRADE_MIN_CONF']}%"
        print(f"🤖 {result['msg']}")
        return result
    
    try:
        import MetaTrader5 as mt5
        login=os.getenv("MT5_LOGIN")
        password=os.getenv("MT5_PASSWORD")
        server=os.getenv("MT5_SERVER","Headway-Real")
        symbol=os.getenv("MT5_SYMBOL","GOLD")
        
        if not login or not password:
            result["msg"]="MT5_LOGIN / MT5_PASSWORD belum diisi di Secrets"
            print(f"❌ {result['msg']}")
            return result
        
        print(f"🤖 HEADWAY DIRECT AUTO: Login {login} ke {server} symbol {symbol} - OP {keputusan} {lot}")
        
        # Init MT5
        if not mt5.initialize(login=int(login), password=password, server=server):
            result["msg"]=f"MT5 init gagal {server}: {mt5.last_error()} - cek ID/pass/server"
            print(f"❌ {result['msg']}")
            mt5.shutdown()
            return result
        
        # Cari symbol Headway
        for sym in [symbol, "GOLD", "XAUUSD", "GOLD.a", "XAUUSD.a", "XAUUSD.b"]:
            info=mt5.symbol_info(sym)
            if info:
                if not info.visible: mt5.symbol_select(sym, True)
                symbol=sym
                print(f"✅ Symbol Headway ketemu: {sym}")
                break
        else:
            result["msg"]="Symbol GOLD/XAUUSD gak ketemu di Headway"
            mt5.shutdown()
            return result
        
        tick=mt5.symbol_info_tick(symbol)
        if not tick:
            result["msg"]=f"Tick {symbol} None"
            mt5.shutdown()
            return result
        
        price=tick.ask if keputusan=="BUY" else tick.bid
        
        req={
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(lot),
            "type": mt5.ORDER_TYPE_BUY if keputusan=="BUY" else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": float(sl),
            "tp": float(tp1),
            "deviation": 100,
            "magic": 8909,
            "comment": f"TANI V8.9 HEADWAY {keputusan}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        print(f"📤 OP HEADWAY: {keputusan} {symbol} {lot} @ {price} SL {sl} TP {tp1}")
        res=mt5.order_send(req)
        
        if res is None:
            result["msg"]=f"order_send None: {mt5.last_error()}"
        elif res.retcode!=mt5.TRADE_RETCODE_DONE:
            result["msg"]=f"Gagal retcode {res.retcode}: {res.comment}"
        else:
            result["success"]=True
            result["ticket"]=res.order
            result["msg"]=f"{keputusan} {lot} {symbol} @ {price} ticket {res.order} - SUKSES AUTO OP!"
            print(f"✅ {result['msg']}")
        
        mt5.shutdown()
        
        # Save history
        hist=load_json(CONFIG["TRADE_HISTORY_FILE"], [])
        hist.append({"time": datetime.now(timezone.utc).isoformat(), "keputusan": keputusan, "symbol": symbol, "lot": lot, "entry": price, "sl": sl, "tp": tp1, "conf": conf, "colony": colony_pct, "jenis": jenis, "result": result})
        if len(hist)>100: hist=hist[-100:]
        save_json(CONFIG["TRADE_HISTORY_FILE"], hist)
        return result
        
    except ImportError:
        result["msg"]="MetaTrader5 module gak ada - ganti runs-on: windows-latest di tani.yml!"
        print(f"⚠️ {result['msg']}")
        return result
    except Exception as e:
        result["msg"]=f"Error: {str(e)[:300]}"
        print(f"❌ {result['msg']}")
        return result

def init_dna():
    dna={}
    for i in range(CONFIG["PEMETIK"]): dna[f"pemetik_{i}"]={"jabatan":"Pemetik","kekuatan":random.randint(50,70),"ketajaman":random.randint(55,75),"stamina_max":100,"keberuntungan":random.randint(50,70),"skor":0,"panen":0,"alat_lv":1,"tenaga":100}
    for i in range(CONFIG["MANDOR"]): dna[f"mandor_{i}"]={"jabatan":"Mandor","kekuatan":random.randint(65,80),"ketajaman":random.randint(70,85),"stamina_max":120,"keberuntungan":random.randint(60,80),"skor":5,"panen":0,"alat_lv":2,"tenaga":120}
    for i in range(CONFIG["PEMBAJAK"]): dna[f"pembajak_{i}"]={"jabatan":"Pembajak","kekuatan":random.randint(75,90),"ketajaman":random.randint(80,90),"stamina_max":150,"keberuntungan":random.randint(65,85),"skor":10,"panen":0,"alat_lv":2,"tenaga":150}
    for i in range(CONFIG["PENUAI"]): dna[f"penuai_{i}"]={"jabatan":"Penuai","kekuatan":random.randint(80,95),"ketajaman":random.randint(85,95),"stamina_max":200,"keberuntungan":random.randint(70,90),"skor":15,"panen":0,"alat_lv":3,"tenaga":200}
    return dna

def logic_pemetik(m5, idx, alat_lv, tenaga):
    if tenaga<10: return "NEUTRAL"
    try:
        e20=m5['Close'].ewm(20).mean().iloc[-1]; e50=m5['Close'].ewm(50).mean().iloc[-1]; e10=m5['Close'].ewm(10).mean().iloc[-1]; e30=m5['Close'].ewm(30).mean().iloc[-1]
        if idx==0:
            last=m5.tail(15)
            for j in range(len(last)-3,1,-1):
                if last['Low'].iloc[j]-last['High'].iloc[j-2]>=CONFIG["MIN_FVG"]: return "BUY"
                if last['Low'].iloc[j-2]-last['High'].iloc[j]>=CONFIG["MIN_FVG"]: return "SELL"
            return "BUY" if e20>e50 else "SELL"
        else: return "BUY" if e20>e50 else "SELL" if idx<=4 else "BUY" if e10>e30 else "SELL"
    except: return random.choice(["BUY","SELL"])
def logic_mandor(m5, idx, lp):
    try: e20=m5['Close'].ewm(20).mean().iloc[-1]; e50=m5['Close'].ewm(50).mean().iloc[-1]; trend="BUY" if e20>e50 else "SELL"; return "BUY" if lp["BUY"]>lp["SELL"] else "SELL" if lp["SELL"]>lp["BUY"] else trend
    except: return random.choice(["BUY","SELL"])
def logic_pembajak(m5, h4, dxy, idx, lm):
    try: e20=m5['Close'].ewm(20).mean().iloc[-1]; e50=m5['Close'].ewm(50).mean().iloc[-1]; trend="BUY" if e20>e50 else "SELL"; spread=m5['High'].iloc[-1]-m5['Low'].iloc[-1]; return "BLOCK" if spread>CONFIG["MAX_SPREAD"] and idx==2 else trend
    except: return random.choice(["BUY","SELL"])
def logic_penuai(m5, idx, lb):
    try: e20=m5['Close'].ewm(20).mean().iloc[-1]; e50=m5['Close'].ewm(50).mean().iloc[-1]; trend="BUY" if e20>e50 else "SELL"; return "BUY" if lb["BUY"]>lb["SELL"] else "SELL" if lb["SELL"]>lb["BUY"] else trend
    except: return random.choice(["BUY","SELL"])

def ratu_tani_v8():
    print(f"=== 🌾👑 TANI V8.9 HEADWAY DIRECT AUTO {datetime.now()} ===")
    is_off, reason = is_weekend_off(); print(f"⏰ {reason}")
    print(f"🤖 Direct Auto Headway: {CONFIG['AUTO_TRADE_ENABLED']} - Login dari Secrets, OP langsung kayak manual!")
    fetcher=AntiBlokirFetcher(); ensemble=EnsembleV8(); antispam=AntiSpamV8()
    dna=load_json(CONFIG["DNA_FILE"], init_dna()); memory=load_json(CONFIG["MEMORY_FILE"], {"wins":0,"losses":0,"panen_kecil":0,"panen_raya":0,"gudang":0,"evolutions":0}); last=load_json(CONFIG["LAST_FILE"], {}); offset_hist=load_json(CONFIG["OFFSET_FILE"], [])
    m5=get_paxg_safe_hybrid(fetcher,300); h4=get_paxg_safe_hybrid(fetcher,120); dxy=get_yf_safe("DX-Y.NYB")
    if m5.empty: print("🌾 Sawah kosong"); return
    ensemble.preload(m5); price_for_ensemble=float(m5['Close'].iloc[-1]); ensemble.update(price_for_ensemble)
    ofi_price, ofi = fetcher.get_ofi()
    if ofi_price is None: ofi=0; ofi_price=price_for_ensemble
    print(f"📊 OFI {ofi:+.2f} PAXG {ofi_price:.2f}")
    if is_off:
        print(f"🌴 WEEKEND MODE: evaluasi + cek harga - GAK OP")
        offset_hist.append({"time": datetime.now(timezone.utc).isoformat(),"paxg": float(ofi_price),"mt5_est": float(price_for_ensemble),"offset": CONFIG["OFFSET"],"ofi": float(ofi),"is_weekend": True})
        if len(offset_hist)>100: offset_hist=offset_hist[-100:]
        save_json(CONFIG["OFFSET_FILE"], offset_hist); save_json(CONFIG["DNA_FILE"], dna); save_json(CONFIG["MEMORY_FILE"], memory)
        if not os.path.exists(CONFIG["LAST_FILE"]):
            save_json(CONFIG["LAST_FILE"], {"keputusan":"WEEKEND","jenis":"EVALUASI","time":time.time(),"price":price_for_ensemble,"conf":0,"trend":"WEEKEND_OFF"})
        last_weekend=last.get("last_weekend_check",0)
        if time.time()-last_weekend>21600:
            send_weekend_check(ofi_price, price_for_ensemble, ofi, memory, dna, offset_hist)
            last["last_weekend_check"]=time.time(); save_json(CONFIG["LAST_FILE"], last)
        else: save_json(CONFIG["LAST_FILE"], last)
        print(f"💾 DNA {len(dna)} Gudang {memory.get('gudang',0)}$")
        return
    lp={"BUY":0,"SELL":0,"NEUTRAL":0}; lm={"BUY":0,"SELL":0,"NEUTRAL":0}; lb={"BUY":0,"SELL":0,"NEUTRAL":0,"BLOCK":0}; ln={"BUY":0,"SELL":0,"NEUTRAL":0}
    for i in range(CONFIG["PEMETIK"]):
        k=f"pemetik_{i}"
        if k not in dna: dna[k]=init_dna()[k]
        v=logic_pemetik(m5,i,dna[k].get("alat_lv",1),dna[k].get("tenaga",100)); lp[v]+=1; dna[k]["tenaga"]=max(0,dna[k].get("tenaga",100)-5)
    for i in range(CONFIG["MANDOR"]):
        k=f"mandor_{i}"
        if k not in dna: dna[k]=init_dna()[k]
        v=logic_mandor(m5,i,lp); lm[v]+=1
    for i in range(CONFIG["PEMBAJAK"]):
        k=f"pembajak_{i}"
        if k not in dna: dna[k]=init_dna()[k]
        v=logic_pembajak(m5,h4,dxy,i,lm); lb[v]+=1
    for i in range(CONFIG["PENUAI"]):
        k=f"penuai_{i}"
        if k not in dna: dna[k]=init_dna()[k]
        v=logic_penuai(m5,i,lb); ln[v]+=1
    if lb["BLOCK"]>=3: print(f"🚫 BLOCK"); return
    total=25; tb=lp["BUY"]+lm["BUY"]+lb["BUY"]+ln["BUY"]; ts=lp["SELL"]+lm["SELL"]+lb["SELL"]+ln["SELL"]; buy_pct=tb/total*100; sell_pct=ts/total*100; colony_pct=max(buy_pct,sell_pct)
    print(f"👑 BUY {tb}/{total}={buy_pct:.0f}% SELL {ts}/{total}={sell_pct:.0f}%")
    final_prob,trend,atr,conf,breakdown=ensemble.final_prob(ofi,colony_pct)
    print(f"🧠 Prob {final_prob*100:.0f}% {trend} Conf {conf*100:.0f}%")
    keputusan=None; jenis=None
    if buy_pct>=CONFIG["QUORUM_KECIL"] or final_prob>0.58: keputusan="BUY"; jenis="PANEN KECIL"
    if sell_pct>=CONFIG["QUORUM_KECIL"] or final_prob<0.42: keputusan="SELL"; jenis="PANEN KECIL"
    if buy_pct>=CONFIG["QUORUM_RAYA"] or final_prob>0.68: keputusan="BUY"; jenis="PANEN RAYA"
    if sell_pct>=CONFIG["QUORUM_RAYA"] or final_prob<0.32: keputusan="SELL"; jenis="PANEN RAYA"
    if not keputusan: print(f"Quorum belum"); return
    allow,reason=antispam.allow(price_for_ensemble,1 if keputusan=="BUY" else -1,conf,trend,final_prob,colony_pct)
    if not allow: print(f"🚫 SKIP {reason}"); return
    if last.get("keputusan")==keputusan and last.get("jenis")==jenis and abs(time.time()-last.get("time",0))<(CONFIG["COOLDOWN_KECIL"] if jenis=="PANEN KECIL" else CONFIG["COOLDOWN_RAYA"]): print(f"Cooldown {jenis} {keputusan}"); return
    for k in dna:
        try:
            if "pemetik" in k: v=logic_pemetik(m5,int(k.split("_")[1]),dna[k].get("alat_lv",1),dna[k].get("tenaga",100))
            elif "mandor" in k: v=logic_mandor(m5,int(k.split("_")[1]),lp)
            elif "pembajak" in k: v=logic_pembajak(m5,h4,dxy,int(k.split("_")[1]),lm)
            else: v=logic_penuai(m5,int(k.split("_")[1]),lb)
            if v==keputusan: dna[k]["skor"]=dna[k].get("skor",0)+(2 if jenis=="PANEN RAYA" else 1); dna[k]["panen"]=dna[k].get("panen",0)+1
            if dna[k]["panen"]%3==0 and dna[k].get("alat_lv",1)<5: dna[k]["alat_lv"]=dna[k].get("alat_lv",1)+1; memory["evolutions"]=memory.get("evolutions",0)+1
        except: pass
    save_json(CONFIG["DNA_FILE"],dna)
    price=float(m5['Close'].iloc[-1]); sl,tp1,tp2,tp3,sl_dist,tp1_dist,tp2_dist,tp3_dist=get_tp_sl_runner(price,1 if keputusan=="BUY" else -1,trend,atr,m5)
    lot=CONFIG["AUTO_TRADE_LOT_KECIL"] if jenis=="PANEN KECIL" else CONFIG["AUTO_TRADE_LOT_RAYA"]
    kondisi="SEPI 😐" if atr<1.5 else "NORMAL 🙂" if atr<3 else "RAME 🔥" if atr<5 else "NEWS 🌪️"
    memory["gudang"]+=15 if jenis=="PANEN KECIL" else 32
    if jenis=="PANEN KECIL": memory["panen_kecil"]+=1
    else: memory["panen_raya"]+=1
    save_json(CONFIG["MEMORY_FILE"],memory)
    top3=sorted(dna.items(),key=lambda x: x[1].get("skor",0),reverse=True)[:3]; top_str=" | ".join([f"{k}:{v.get('skor',0):.0f} Lv{v.get('alat_lv',1)}" for k,v in top3])
    
    auto_result=None
    if CONFIG["AUTO_TRADE_ENABLED"]:
        auto_result=auto_trade_headway_direct(keputusan, lot, sl, tp1, price, conf, colony_pct, jenis)
    
    send_foto(jenis,keputusan,buy_pct,sell_pct,price,sl,tp1,tp2,tp3,lot,memory['gudang'],memory,lp,lm,lb,ln,price,top_str,atr,kondisi,sl_dist,tp1_dist,tp2_dist,tp3_dist,final_prob,trend,ofi,conf,breakdown, auto_result)
    save_json(CONFIG["LAST_FILE"],{"keputusan":keputusan,"jenis":jenis,"time":time.time(),"price":price,"conf":conf,"trend":trend})

if __name__=="__main__":
    ratu_tani_v8()
