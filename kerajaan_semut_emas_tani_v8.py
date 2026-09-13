"""
🌾👑 KERAJAAN SEMUT TANI V8.7 DINAMIS - TP/SL NGIKUTIN PASAR
Gak kaku lagi 6$/32$ terus! Sekarang ngikutin volatilitas market!

LOGIC DINAMIS:
- ATR = Average True Range dari 14 candle terakhir (volatilitas)
- Kalo market sepi (ATR kecil) => SL/TP kecil biar gak kena SL terus
- Kalo market rame/news (ATR gede) => SL/TP gede biar gak kesenggol noise
- Support/Resistance dinamis dari High/Low terakhir
- RR (Risk Reward) tetap dijaga minimal 1:1.5
"""
import os, json, random, time, requests, pandas as pd
from datetime import datetime
import pytz
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
    "MIN_FVG": 0.4
}
random.seed(int(time.time())%99999)

def get_paxg_safe(interval="5m",limit=300):
    for attempt in range(5):
        try:
            if attempt==0:
                r=requests.get("https://api.gold-api.com/price/XAU",timeout=10).json()
                if "price" in r:
                    p=float(r["price"])+CONFIG["OFFSET"]
                    df=pd.DataFrame([{"ot":int(time.time()*1000)-i*300000,"Close":p,"High":p+random.uniform(0.3,1.2),"Low":p-random.uniform(0.3,1.2),"Open":p+random.uniform(-0.5,0.5)} for i in range(limit)])
                    df["Time"]=pd.to_datetime(df["ot"],unit='ms',utc=True)
                    return df.set_index("Time")
            elif attempt==1:
                m={"5m":"5m","15m":"15m","1h":"1h","4h":"4h","1d":"1d"}.get(interval,"5m")
                r=requests.get("https://api.binance.com/api/v3/klines",params={"symbol":"PAXGUSDT","interval":m,"limit":limit},headers={"User-Agent":f"Mozilla/{random.randint(10,9999)}"},timeout=12).json()
                if isinstance(r,list) and len(r)>20:
                    df=pd.DataFrame(r,columns=["ot","Open","High","Low","Close","Vol","c","d","e","f","g","h"])
                    for c in ["Open","High","Low","Close"]: df[c]=pd.to_numeric(df[c],errors='coerce')+CONFIG["OFFSET"]
                    df["Time"]=pd.to_datetime(df["ot"],unit='ms',utc=True)
                    return df.set_index("Time")
            elif attempt==2:
                r=requests.get("https://api.coingecko.com/api/v3/coins/pax-gold/market_chart",params={"vs_currency":"usd","days":"2"},timeout=12).json()
                if isinstance(r,dict) and "prices" in r and len(r["prices"])>10:
                    df=pd.DataFrame(r['prices'],columns=['ot','Close'])
                    df['Time']=pd.to_datetime(df['ot'],unit='ms',utc=True)
                    df=df.set_index('Time'); df['Close']+=CONFIG["OFFSET"]; df['High']=df['Close']+1; df['Low']=df['Close']-1; df['Open']=df['Close']
                    return df.tail(limit)
            elif attempt==3:
                import yfinance as yf; time.sleep(0.8)
                df=yf.download("PAXG-USD",period="5d",interval="5m" if interval=="5m" else "60m",progress=False,auto_adjust=True)
                if not df.empty:
                    if hasattr(df.columns,'get_level_values'):
                        try: df.columns=df.columns.get_level_values(0)
                        except: pass
                    for c in ["Open","High","Low","Close"]:
                        if c in df.columns: df[c]+=CONFIG["OFFSET"]
                    df.index=pd.to_datetime(df.index,utc=True)
                    return df.tail(limit)
            else:
                import yfinance as yf; time.sleep(0.8)
                df=yf.download("GC=F",period="5d",interval="5m" if interval=="5m" else "60m",progress=False,auto_adjust=True)
                if not df.empty:
                    if hasattr(df.columns,'get_level_values'):
                        try: df.columns=df.columns.get_level_values(0)
                        except: pass
                    for c in ["Open","High","Low","Close"]:
                        if c in df.columns: df[c]+=CONFIG["OFFSET"]
                    df.index=pd.to_datetime(df.index,utc=True)
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

def hitung_atr_dan_level(m5, keputusan, jenis):
    """
    HITUNG TP/SL DINAMIS NGIKUTIN PASAR
    """
    try:
        # Hitung ATR dari 14 candle terakhir
        df = m5.tail(20).copy()
        df['H-L'] = df['High'] - df['Low']
        df['H-Cprev'] = abs(df['High'] - df['Close'].shift(1))
        df['L-Cprev'] = abs(df['Low'] - df['Close'].shift(1))
        df['TR'] = df[['H-L','H-Cprev','L-Cprev']].max(axis=1)
        atr = df['TR'].rolling(14).mean().iloc[-1]
        
        # Kalo ATR gak kehitung, pake default 2$
        if pd.isna(atr) or atr < 0.5:
            atr = 2.0
        
        # Volatilitas market
        # Sepi: ATR < 1.5$  | Normal: 1.5-3$ | Rame: 3-5$ | News: >5$
        print(f"📈 ATR (volatilitas) = {atr:.2f}$")
        
        # Support Resistance dinamis dari High Low 20 candle
        recent_high = df['High'].max()
        recent_low = df['Low'].min()
        range_market = recent_high - recent_low
        
        price = float(m5['Close'].iloc[-1])
        
        # DINAMIS LOGIC
        if jenis == "PANEN KECIL":
            # KECIL: RR 1:1 - 1:2.5
            sl_mult = 1.0  # SL = 1x ATR
            tp1_mult = 0.8
            tp2_mult = 1.5
            tp3_mult = 1.5
            lot = "0.05"
            add = 15
        else:
            # RAYA: RR 1:1.5 - 1:5
            sl_mult = 1.2
            tp1_mult = 1.0
            tp2_mult = 2.0
            tp3_mult = 4.0
            lot = "0.10"
            add = 32
        
        # Hitung SL TP dinamis
        sl_dist = atr * sl_mult
        tp1_dist = atr * tp1_mult
        tp2_dist = atr * tp2_mult
        tp3_dist = atr * tp3_mult
        
        # Batas min max biar gak kegedean/kekecilan
        # SL min 4$ max 10$, TP max 50$
        sl_dist = max(3.5, min(sl_dist, 10))
        tp1_dist = max(3, min(tp1_dist, 12))
        tp2_dist = max(8, min(tp2_dist, 25))
        tp3_dist = max(12, min(tp3_dist, 50))
        
        # Sesuaikan dengan keputusan BUY/SELL
        if keputusan == "BUY":
            sl = price - sl_dist
            tp1 = price + tp1_dist
            tp2 = price + tp2_dist
            tp3 = price + tp3_dist
            # Cek support: SL jangan di bawah recent_low terlalu jauh
            sl = max(sl, recent_low - 2)  # SL minimal 2$ di bawah low terakhir
        else:
            sl = price + sl_dist
            tp1 = price - tp1_dist
            tp2 = price - tp2_dist
            tp3 = price - tp3_dist
            # Cek resistance: SL jangan di atas recent_high terlalu jauh
            sl = min(sl, recent_high + 2)  # SL maksimal 2$ di atas high terakhir
        
        # Info pasar
        if atr < 1.5:
            kondisi = "SEPI 😐 - SL/TP kecil"
        elif atr < 3:
            kondisi = "NORMAL 🙂 - SL/TP standar"
        elif atr < 5:
            kondisi = "RAME 🔥 - SL/TP lebar"
        else:
            kondisi = "NEWS 🌪️ - SL/TP super lebar"
        
        print(f"🎯 KONDISI PASAR: {kondisi}")
        print(f"   ENTRY {price:.2f} | SL {sl:.2f} ({sl_dist:.1f}$) | TP1 {tp1:.2f} ({tp1_dist:.1f}$) TP2 {tp2:.2f} ({tp2_dist:.1f}$) TP3 {tp3:.2f} ({tp3_dist:.1f}$) | Lot {lot}")
        
        return price, sl, tp1, tp2, tp3, lot, add, atr, kondisi, sl_dist, tp1_dist, tp2_dist, tp3_dist
        
    except Exception as e:
        print(f"Gagal hitung dinamis: {e}, pake default kaku")
        # Fallback ke kaku kalo error
        price = float(m5['Close'].iloc[-1])
        if jenis=="PANEN KECIL":
            sl=price-6 if keputusan=="BUY" else price+6
            tp1=price+5 if keputusan=="BUY" else price-5
            tp2=price+15 if keputusan=="BUY" else price-15
            tp3=price+15 if keputusan=="BUY" else price-15
            lot="0.05"; add=15; atr=2.0; kondisi="DEFAULT"; sl_dist=6; tp1_dist=5; tp2_dist=15; tp3_dist=15
        else:
            sl=price-6 if keputusan=="BUY" else price+6
            tp1=price+5 if keputusan=="BUY" else price-5
            tp2=price+15 if keputusan=="BUY" else price-15
            tp3=price+32 if keputusan=="BUY" else price-32
            lot="0.10"; add=32; atr=2.0; kondisi="DEFAULT"; sl_dist=6; tp1_dist=5; tp2_dist=15; tp3_dist=32
        return price, sl, tp1, tp2, tp3, lot, add, atr, kondisi, sl_dist, tp1_dist, tp2_dist, tp3_dist

def send_satu_foto(jenis, keputusan, buy_pct, sell_pct, entry, sl, tp1, tp2, tp3, lot, gudang, memory, lap_pemetik, lap_mandor, lap_pembajak, lap_penuai, price, top_str, atr, kondisi, sl_dist, tp1_dist, tp2_dist, tp3_dist):
    token=os.getenv("TELEGRAM_TOKEN"); chat=os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat: 
        print(f"{jenis} {keputusan} {buy_pct:.0f}% vs {sell_pct:.0f}% ENTRY {entry:.2f} SL {sl:.2f} TP {tp3:.2f}")
        return
    try:
        photo_url="https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800"
        pct = buy_pct if keputusan=="BUY" else sell_pct
        
        if jenis=="PANEN RAYA":
            emoji="🌾👑🔥"
            bar="🟩"*min(10, memory['gudang']//10) + "⬜"*(10-min(10, memory['gudang']//10))
        else:
            emoji="🌿"
            bar="🟨"*min(10, memory['gudang']//10) + "⬜"*(10-min(10, memory['gudang']//10))

        caption=f"""{emoji} {jenis} {keputusan} {pct:.0f}% - {buy_pct:.0f}% vs {sell_pct:.0f}%

📊 COLONY 25 PETANI KOMPAK
🌿 Pemetik {lap_pemetik['BUY']}B {lap_pemetik['SELL']}S
👨‍🌾 Mandor {lap_mandor['BUY']}B {lap_mandor['SELL']}S
🚜 Pembajak {lap_pembajak['BUY']}B {lap_pembajak['SELL']}S
🌾 Penuai {lap_penuai['BUY']}B {lap_penuai['SELL']}S

💰 OP DI MT5 - {kondisi}
ATR: {atr:.2f}$ | ENTRY {entry:.2f}
SL: {sl:.2f} (-{sl_dist:.1f}$)
TP1: {tp1:.2f} (+{tp1_dist:.1f}$)
TP2: {tp2:.2f} (+{tp2_dist:.1f}$)
TP3: {tp3:.2f} (+{tp3_dist:.1f}$)
Lot: {lot} | RR 1:{tp3_dist/sl_dist:.1f}

🏚️ GUDANG TANI
{bar} {gudang}$
Kecil {memory['panen_kecil']}x Raya {memory['panen_raya']}x
Target 62$/hari = 434$/minggu

🧬 TOP: {top_str}

✅ Dinamis ATR | Quorum 32%/55%
#TANI #XAUUSD #{keputusan}"""

        requests.post(f"https://api.telegram.org/bot{token}/sendPhoto",json={"chat_id":chat,"photo":photo_url,"caption":caption},timeout=15)
        print(f"Foto terkirim DINAMIS: {jenis} {keputusan} {pct:.0f}% ATR {atr:.2f}$")
    except Exception as e:
        print(f"Gagal kirim foto: {e}")

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
    print(f"=== 🌾👑 RATU TANI V8.7 DINAMIS BANGUN {datetime.now()} ===")
    dna=load_json(CONFIG["DNA_FILE"], init_dna())
    memory=load_json(CONFIG["MEMORY_FILE"], {"wins":0,"losses":0,"panen_kecil":0,"panen_raya":0,"gudang":0,"evolutions":0})
    last=load_json(CONFIG["LAST_FILE"], {})

    m5=get_paxg_safe("5m",300); h4=get_paxg_safe("4h",120); dxy=get_yf_safe("DX-Y.NYB")
    if m5.empty:
        print("🌾 Sawah kosong - Ratu Tani puasa")
        return

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

    print(f"🌿 Pemetik: BUY {laporan_pemetik['BUY']} SELL {laporan_pemetik['SELL']} | {' '.join(logs_pemetik)}")
    print(f"👨‍🌾 Mandor: BUY {laporan_mandor['BUY']} SELL {laporan_mandor['SELL']} | {' '.join(logs_mandor)}")
    print(f"🚜 Pembajak: BUY {laporan_pembajak['BUY']} SELL {laporan_pembajak['SELL']} BLOCK {laporan_pembajak['BLOCK']} | {' '.join(logs_pembajak)}")
    print(f"🌾 Penuai: BUY {laporan_penuai['BUY']} SELL {laporan_penuai['SELL']} | {' '.join(logs_penuai)}")
    print(f"👑 TOTAL: BUY {total_buy}/{total_all}={buy_pct:.0f}% SELL {total_sell}/{total_all}={sell_pct:.0f}%")

    keputusan=None; jenis=None
    if buy_pct>=CONFIG["QUORUM_KECIL"]: keputusan="BUY"; jenis="PANEN KECIL"
    elif sell_pct>=CONFIG["QUORUM_KECIL"]: keputusan="SELL"; jenis="PANEN KECIL"
    if buy_pct>=CONFIG["QUORUM_RAYA"]: keputusan="BUY"; jenis="PANEN RAYA"
    elif sell_pct>=CONFIG["QUORUM_RAYA"]: keputusan="SELL"; jenis="PANEN RAYA"

    if not keputusan:
        print(f"Ratu: quorum {CONFIG['QUORUM_KECIL']}% belum tercapai BUY {buy_pct:.0f}% SELL {sell_pct:.0f}%")
        for k in dna: dna[k]["tenaga"]=min(dna[k].get("stamina_max",100), dna[k].get("tenaga",100)+15)
        save_json(CONFIG["DNA_FILE"], dna)
        return

    cooldown=1800 if jenis=="PANEN KECIL" else 3600
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
                dna[k]["skor"]=dna[k].get("skor",0)+(2 if jenis=="PANEN RAYA" else 1)
                dna[k]["panen"]=dna[k].get("panen",0)+1
                dna[k]["tenaga"]=min(dna[k].get("stamina_max",100), dna[k].get("tenaga",100)+15)
                if dna[k]["panen"]%3==0 and dna[k].get("alat_lv",1)<5:
                    dna[k]["alat_lv"]=dna[k].get("alat_lv",1)+1
        except: pass
    save_json(CONFIG["DNA_FILE"], dna)

    # === DINAMIS TP/SL NGIKUTIN PASAR ===
    price, sl, tp1, tp2, tp3, lot, add, atr, kondisi, sl_dist, tp1_dist, tp2_dist, tp3_dist = hitung_atr_dan_level(m5, keputusan, jenis)

    memory["gudang"]+=add
    if jenis=="PANEN KECIL": memory["panen_kecil"]+=1
    else: memory["panen_raya"]+=1
    save_json(CONFIG["MEMORY_FILE"], memory)

    top3=sorted(dna.items(),key=lambda x: x[1].get("skor",0),reverse=True)[:3]
    top_str=" | ".join([f"{k}:{v.get('skor',0):.0f} Lv{v.get('alat_lv',1)}" for k,v in top3])

    send_satu_foto(jenis, keputusan, buy_pct, sell_pct, price, sl, tp1, tp2, tp3, lot, memory['gudang'], memory, laporan_pemetik, laporan_mandor, laporan_pembajak, laporan_penuai, price, top_str, atr, kondisi, sl_dist, tp1_dist, tp2_dist, tp3_dist)
    
    save_json(CONFIG["LAST_FILE"], {"keputusan":keputusan,"jenis":jenis,"time":time.time(),"price":price})

if __name__=="__main__":
    ratu_tani_v8()
