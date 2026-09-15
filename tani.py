"""
TANI V12.3 FINAL - SEMPURNA TINGGAL COPAS
Nama file wajib: tani.py (di root repo)
"""
import os, json, time, random, requests
import pandas as pd
import numpy as np
from collections import deque
from datetime import datetime, timezone

CONFIG = {
    "OFFSET_BASE": -2.41,
    "CACHE_FILE": ".cache_binance.json",
    "CACHE_TTL": 90,
    "DNA_FILE": ".dna_tani_v12.json",
    "MEMORY_FILE": ".memory_tani_v12.json",
    "LAST_FILE": ".last_tani_v12.json",
    "OFFSET_FILE": ".offset_history.json",
    "POSITION_FILE": ".position_tani.json",
    "CONF_THRESHOLD": 0.80,
    "ATR_MIN": 0.8,
    "RISK_PCT": 1.5,
    "BE_TRIGGER_R": 1.0, "BE_PLUS": 0.5,
    "TRAIL_START_R": 2.0, "TRAIL_ATR_MULT": 1.2,
}

def load_json(p,d):
    if not os.path.exists(p): return d
    try:
        with open(p,'r') as f: return json.load(f)
    except: return d

def save_json(p,d):
    try:
        with open(p+'.tmp','w') as f: json.dump(f,d,indent=2)
        os.replace(p+'.tmp',p)
    except: pass

def send_tg(text):
    token=os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    chat=os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print(f"[DRY] {text[:200]}")
        return
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id":chat,"text":text,"parse_mode":"HTML"}, timeout=8)
    except: pass

class Fetcher:
    def __init__(self):
        self.s=requests.Session()
        self.s.headers.update({"User-Agent":"Mozilla/5.0"})
        self.cache=load_json(CONFIG["CACHE_FILE"],{})

    def _cache_get(self,k):
        c=self.cache.get(k)
        if c and time.time()-c.get('t',0) < CONFIG["CACHE_TTL"]:
            return c.get('data')
        return None

    def _cache_set(self,k,data):
        self.cache[k]={'t':time.time(),'data':data}
        save_json(CONFIG["CACHE_FILE"],self.cache)

    def _req(self,url):
        try:
            time.sleep(random.uniform(0.3,1.0))
            r=self.s.get(url,timeout=6)
            if r.status_code==200:
                return r.json()
        except: pass
        return None

    def get_klines(self,interval="5m",limit=300):
        key=f"klines_{interval}"
        cached=self._cache_get(key)
        if cached:
            try:
                df=pd.DataFrame(cached)
                df['Time']=pd.to_datetime(df['Time'],utc=True)
                df=df.set_index('Time')
                print(f"✅ Cache {interval}")
                return df
            except: pass

        urls=[
            f"https://data-api.binance.vision/api/v3/klines?symbol=PAXGUSDT&interval={interval}&limit={limit}",
            f"https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval={interval}&limit={limit}",
        ]
        for url in urls:
            data=self._req(url)
            if isinstance(data,list) and len(data)>20:
                try:
                    df=pd.DataFrame(data,columns=["ot","Open","High","Low","Close","Vol","ct","q","n","tb","tq","ig"])
                    for c in ["Open","High","Low","Close"]: df[c]=pd.to_numeric(df[c], errors='coerce')
                    df["Time"]=pd.to_datetime(df["ot"], unit='ms', utc=True)
                    df=df.set_index("Time").dropna()
                    to_cache=df.reset_index()[["Time","Open","High","Low","Close"]].tail(200).copy()
                    to_cache["Time"]=to_cache["Time"].astype(str)
                    self._cache_set(key,to_cache.to_dict(orient='records'))
                    print(f"✅ {url.split('/')[2]} {len(df)}")
                    return df
                except: continue

        try:
            import yfinance as yf
            for sym in ["PAXG-USD","GLD"]:
                df=yf.download(sym, period="5d", interval="5m" if interval=="5m" else "60m", progress=False, auto_adjust=True)
                if not df.empty and len(df)>20:
                    if hasattr(df.columns,'get_level_values'):
                        try: df.columns=df.columns.get_level_values(0)
                        except: pass
                    df.index=pd.to_datetime(df.index, utc=True)
                    print(f"✅ yfinance {sym}")
                    return df
        except: pass
        return pd.DataFrame()

class PosMan:
    def __init__(self,p): self.path=p; self.pos=load_json(p,None)
    def open(self,kep,entry,sl,tp1,tp2,tp3,sl_dist,lot,atr):
        self.pos={"open":True,"kep":kep,"entry":entry,"sl":sl,"sl0":sl,"tp1":tp1,"tp2":tp2,"tp3":tp3,"sl_dist":sl_dist,"lot":lot,"atr":atr,"be":False,"high":entry,"low":entry,"t":time.time(),"maxR":0}
        save_json(self.path,self.pos); send_tg(f"🔥 <b>OPEN {kep}</b> {entry:.2f} SL {sl:.2f} TP1 {tp1:.2f} Lot {lot}")
    def manage(self,price,atr):
        if not self.pos or not self.pos.get("open"): return False
        p=self.pos; kep=p["kep"]; entry=p["entry"]; sl_dist=p["sl_dist"]
        be_trig=entry+sl_dist*CONFIG["BE_TRIGGER_R"] if kep=="BUY" else entry-sl_dist*CONFIG["BE_TRIGGER_R"]
        trail_trig=entry+sl_dist*CONFIG["TRAIL_START_R"] if kep=="BUY" else entry-sl_dist*CONFIG["TRAIL_START_R"]
        if kep=="BUY":
            p["high"]=max(p["high"],price); r=(price-entry)/sl_dist; p["maxR"]=max(p["maxR"],r)
            if not p["be"] and price>=be_trig:
                new_sl=entry+CONFIG["BE_PLUS"]
                if new_sl>p["sl"]: p["sl"]=new_sl; p["be"]=True; send_tg(f"🔒 <b>BE BUY</b> {p['sl0']:.2f}->{new_sl:.2f} {r:.1f}R")
            elif p["be"] and price>=trail_trig:
                trail=p["high"]-atr*CONFIG["TRAIL_ATR_MULT"]
                if trail>p["sl"]+0.2: old=p["sl"]; p["sl"]=float(trail); send_tg(f"📈 <b>TRAIL BUY</b> {old:.2f}->{p['sl']:.2f} {r:.1f}R")
            if price<=p["sl"]: send_tg(f"❌ <b>SL HIT</b> {kep} {entry:.2f}->{price:.2f}"); self.pos=None; save_json(self.path,{"open":False}); return True
            if price>=p["tp3"]: send_tg(f"💰 <b>TP3 HIT</b> {kep} {r:.1f}R"); self.pos=None; save_json(self.path,{"open":False}); return True
        else:
            p["low"]=min(p["low"],price); r=(entry-price)/sl_dist; p["maxR"]=max(p["maxR"],r)
            if not p["be"] and price<=be_trig:
                new_sl=entry-CONFIG["BE_PLUS"]
                if new_sl<p["sl"]: p["sl"]=new_sl; p["be"]=True; send_tg(f"🔒 <b>BE SELL</b> {p['sl0']:.2f}->{new_sl:.2f} {r:.1f}R")
            elif p["be"] and price<=trail_trig:
                trail=p["low"]+atr*CONFIG["TRAIL_ATR_MULT"]
                if trail<p["sl"]-0.2: old=p["sl"]; p["sl"]=float(trail); send_tg(f"📉 <b>TRAIL SELL</b> {old:.2f}->{p['sl']:.2f} {r:.1f}R")
            if price>=p["sl"]: send_tg(f"❌ <b>SL HIT</b> {kep} {entry:.2f}->{price:.2f}"); self.pos=None; save_json(self.path,{"open":False}); return True
            if price<=p["tp3"]: send_tg(f"💰 <b>TP3 HIT</b> {kep} {r:.1f}R"); self.pos=None; save_json(self.path,{"open":False}); return True
        save_json(self.path,p); return False

def main():
    print(f"=== TANI V12.3 FINAL {datetime.now(timezone.utc)} ===")
    fetcher=Fetcher(); posman=PosMan(CONFIG["POSITION_FILE"])
    m5=fetcher.get_klines("5m",300)
    if m5.empty:
        print("Fail semua source"); return
    price=float(m5['Close'].iloc[-1]); atr=float((m5['High'].tail(14)-m5['Low'].tail(14)).mean())
    print(f"Price {price:.2f} ATR {atr:.2f}")

    if posman.pos and posman.pos.get("open"):
        closed=posman.manage(price,atr)
        if not closed:
            print("Posisi aktif, skip entry baru")
            return

    if atr < CONFIG["ATR_MIN"]:
        print("ATR kecil skip"); return

    e20=m5['Close'].ewm(20).mean().iloc[-1]; e50=m5['Close'].ewm(50).mean().iloc[-1]
    kep="BUY" if e20>e50 else "SELL"
    prob=0.68 if kep=="BUY" else 0.32
    print(f"Sinyal {kep} Prob {prob}")

    last=load_json(CONFIG["LAST_FILE"],{})
    if time.time()-last.get("time",0) < 1800:
        print("Cooldown 30m anti spam GitHub")
        return

    sl_dist=max(3.5,min(atr*1.6+1.0,12.0))
    if kep=="BUY": sl=price-sl_dist; tp1=price+sl_dist*1.8; tp2=price+sl_dist*3.2; tp3=price+sl_dist*5.5
    else: sl=price+sl_dist; tp1=price-sl_dist*1.8; tp2=price-sl_dist*3.2; tp3=price-sl_dist*5.5

    lot=0.02
    posman.open(kep,price,sl,tp1,tp2,tp3,sl_dist,lot,atr)
    save_json(CONFIG["LAST_FILE"],{"keputusan":kep,"time":time.time(),"price":price})
    send_tg(f"🔥👑 <b>V12.3 FINAL {kep}</b> {price:.2f} SL {sl:.2f} TP3 {tp3:.2f} ATR {atr:.2f}\nAnti Blokir Total GitHub+Binance")

if __name__=="__main__":
    main()
