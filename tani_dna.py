"""
TANI DNA EVOLUSI - Jalan 1x sehari jam 23:00 UTC
Tugas: Evolusi 40 petani, update DNA, tuning QUORUM, kick petani bocor
File wajib: tani_dna.py di root
"""
import os, json, time, random, requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone

CONFIG = {
    "DNA_FILE": ".dna_tani_v12.json",
    "MEMORY_FILE": ".memory_tani_v12.json",
    "LAST_FILE": ".last_tani_v12.json",
    "OFFSET_FILE": ".offset_history.json",
    "CACHE_FILE": ".cache_binance.json",
    "QUORUM_KECIL": 45,
    "QUORUM_RAYA": 70,
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
    token=os.getenv("TELEGRAM_TOKEN"); chat=os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat: print(text); return
    try: requests.post(f"https://api.telegram.org/bot{token}/sendMessage",json={"chat_id":chat,"text":text,"parse_mode":"HTML"},timeout=8)
    except: pass

# 40 PETANI GARANG
def init_dna():
    dna={}
    for i in range(12):
        dna[f"pemetik_{i}"]={"skor": random.uniform(0,5), "wr": 50, "trades": 0, "profit": 0, "role": "pemetik", "ema_fast": random.choice([10,12,15,20]), "ema_slow": random.choice([40,50,60,80])}
    for i in range(8):
        dna[f"mandor_{i}"]={"skor": random.uniform(0,5), "wr": 50, "trades": 0, "profit": 0, "role": "mandor", "rsi_over": random.choice([68,70,72]), "rsi_under": random.choice([28,30,32])}
    for i in range(10):
        dna[f"pembajak_{i}"]={"skor": random.uniform(0,5), "wr": 50, "trades": 0, "profit": 0, "role": "pembajak", "atr_mult": random.uniform(1.2,2.0)}
    for i in range(10):
        dna[f"pengepul_{i}"]={"skor": random.uniform(0,5), "wr": 50, "trades": 0, "profit": 0, "role": "pengepul", "tp_r": random.uniform(1.5,3.0)}
    return dna

def fetch_m5():
    import requests
    s=requests.Session()
    for url in [
        "https://data-api.binance.vision/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=500",
        "https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=500",
    ]:
        try:
            r=s.get(url,timeout=6)
            if r.status_code==200:
                data=r.json()
                df=pd.DataFrame(data,columns=["ot","Open","High","Low","Close","Vol","ct","q","n","tb","tq","ig"])
                for c in ["Open","High","Low","Close"]: df[c]=pd.to_numeric(df[c], errors='coerce')
                df["Time"]=pd.to_datetime(df["ot"], unit='ms', utc=True)
                df=df.set_index("Time").dropna()
                return df
        except: continue
    return pd.DataFrame()

def evaluate_petani(df, petani_cfg):
    try:
        close=df['Close']
        ema_f=close.ewm(petani_cfg.get('ema_fast',12)).mean().iloc[-1]
        ema_s=close.ewm(petani_cfg.get('ema_slow',50)).mean().iloc[-1]
        # Simulasi trade: BUY if ema_f > ema_s
        if ema_f>ema_s:
            kep="BUY"
            # cek 10 candle ke depan profit ga (backtest)
            entry=close.iloc[-11]
            future=close.iloc[-10:].max()
            profit=(future-entry)
            win=1 if profit>2 else 0
        else:
            kep="SELL"
            entry=close.iloc[-11]
            future=close.iloc[-10:].min()
            profit=(entry-future)
            win=1 if profit>2 else 0
        return win, profit, kep
    except:
        return 0,0,"HOLD"

def main():
    print(f"=== DNA EVOLUSI {datetime.now(timezone.utc)} ===")
    dna=load_json(CONFIG["DNA_FILE"], None)
    if dna is None:
        print("DNA belum ada, init 40 petani baru")
        dna=init_dna()
        save_json(CONFIG["DNA_FILE"], dna)
        send_tg("🌱 <b>DNA INIT</b> 40 petani garang baru lahir!")
        return

    df=fetch_m5()
    if df.empty:
        print("Gagal fetch M5")
        return

    # Evolusi
    total_win=0
    for name, cfg in dna.items():
        win, profit, kep = evaluate_petani(df, cfg)
        cfg['trades']=cfg.get('trades',0)+1
        cfg['profit']=cfg.get('profit',0)+profit
        # update WR
        prev_wr=cfg.get('wr',50)
        prev_trades=cfg.get('trades',1)
        # WR = (win_trades / total)
        # simpan win count di profit positif
        if 'wins' not in cfg: cfg['wins']=0
        cfg['wins']+=win
        cfg['wr']= (cfg['wins']/cfg['trades']*100) if cfg['trades']>0 else 50
        # skor = WR + profit/10
        cfg['skor']=cfg['wr']*0.6 + cfg['profit']*0.5 + random.uniform(-1,1)
        total_win+=win

    # Sorting & rekomendasi QUORUM
    sorted_dna=sorted(dna.items(), key=lambda x: x[1]['skor'], reverse=True)
    top3=sorted_dna[:3]
    bottom3=sorted_dna[-3:]

    avg_wr=sum(v['wr'] for v in dna.values())/len(dna)
    print(f"AVG WR: {avg_wr:.1f}%")

    # Tuning QUORUM logic
    if avg_wr>62:
        new_qk=55; new_qr=80
    elif avg_wr<48:
        new_qk=35; new_qr=60
    else:
        new_qk=45; new_qr=70

    # Kick petani bocor (WR <35% dan trades>10)
    kicked=[]
    for name,cfg in list(dna.items()):
        if cfg['trades']>10 and cfg['wr']<35:
            print(f"KICK {name} WR {cfg['wr']:.1f}%")
            kicked.append(name)
            # reset jadi petani baru
            dna[name]=init_dna()[random.choice(list(init_dna().keys()))]
            dna[name]['skor']=0
            dna[name]['trades']=0
            dna[name]['wins']=0
            dna[name]['wr']=50
            dna[name]['profit']=0

    save_json(CONFIG["DNA_FILE"], dna)

    # Laporan Telegram
    msg=f"🧬 <b>DNA EVOLUSI HARIAN</b>\n"
    msg+=f"AVG WR: {avg_wr:.1f}% | Total petani: {len(dna)}\n"
    msg+=f"QUORUM baru: {new_qk}/{new_qr}\n\n"
    msg+=f"TOP 3 GARANG:\n"
    for n,c in top3:
        msg+=f"• {n}: WR {c['wr']:.1f}% skor {c['skor']:.1f}\n"
    if kicked:
        msg+=f"\nKICK {len(kicked)} bocor: {', '.join(kicked[:3])}\n"
    msg+=f"\nBesok tuning lagi jam 23:00 UTC"

    # Simpan QUORUM rekomendasi
    save_json(".quorum_rekomendasi.json", {"qk":new_qk,"qr":new_qr,"avg_wr":avg_wr,"date":str(datetime.now(timezone.utc))})

    send_tg(msg)
    print(msg)
    print("DNA evolusi selesai")

if __name__=="__main__":
    main()
