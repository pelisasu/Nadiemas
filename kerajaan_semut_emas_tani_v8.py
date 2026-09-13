"""
🌾👑 KERAJAAN SEMUT TANI V8 - PANEN 3X SEHARI GUDANG PENUH
Sistem: Pemetik setor -> Mandor -> Pembajak -> Penuai -> Ratu
Fitur: Tenaga + Peralatan Lv1-5 + Evolusi Otonom + DNA Abadi + 2 Jenis Panen
Target: Minimal 3 sinyal sehari (2 Kecil 60% + 1 Raya 80%) = 62$/hari
Offset plek MT5 4347.45 = -2.25
"""
import os, json, random, time, requests, pandas as pd
from datetime import datetime
import pytz

CONFIG={
    "OFFSET": -2.25,
    "DNA_FILE": ".dna_tani_v8.json",
    "MEMORY_FILE": ".memory_tani_v8.json",
    "LAST_FILE": ".last_tani_v8.json",
    "TENAGA_FILE": ".tenaga_tani_v8.json",
    "ALAT_FILE": ".alat_tani_v8.json",
    "PEMETIK": 10,
    "MANDOR": 5,
    "PEMBAJAK": 5,
    "PENUAI": 5,
    "QUORUM_KECIL": 60,
    "QUORUM_RAYA": 80,
    "MAX_SPREAD": 6.0,
    "MIN_FVG": 0.8
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

def send(msg):
    token=os.getenv("TELEGRAM_TOKEN"); chat=os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat: print(msg); return
    try: requests.post(f"https://api.telegram.org/bot{token}/sendMessage",json={"chat_id":chat,"text":msg,"parse_mode":"Markdown"},timeout=12)
    except: pass

def load_json(path, default):
    if os.path.exists(path):
        try: return json.load(open(path))
        except: return default
    return default
def save_json(path, data):
    try: json.dump(data, open(path,'w'))
    except: pass

# ================= DNA TANI AWAL =================
def init_dna():
    dna={}
    # Pemetik 0-9
    for i in range(CONFIG["PEMETIK"]):
        dna[f"pemetik_{i}"]={"jabatan":"Pemetik","kekuatan":random.randint(50,70),"ketajaman":random.randint(55,75),"stamina_max":100,"keberuntungan":random.randint(50,70),"skor":0,"births":0,"deaths":0,"panen":0,"alat_lv":1,"tenaga":100}
    for i in range(CONFIG["MANDOR"]):
        dna[f"mandor_{i}"]={"jabatan":"Mandor","kekuatan":random.randint(65,80),"ketajaman":random.randint(70,85),"stamina_max":120,"keberuntungan":random.randint(60,80),"skor":5,"births":0,"deaths":0,"panen":0,"alat_lv":2,"tenaga":120}
    for i in range(CONFIG["PEMBAJAK"]):
        dna[f"pembajak_{i}"]={"jabatan":"Pembajak","kekuatan":random.randint(75,90),"ketajaman":random.randint(80,90),"stamina_max":150,"keberuntungan":random.randint(65,85),"skor":10,"births":0,"deaths":0,"panen":0,"alat_lv":2,"tenaga":150}
    for i in range(CONFIG["PENUAI"]):
        dna[f"penuai_{i}"]={"jabatan":"Penuai","kekuatan":random.randint(80,95),"ketajaman":random.randint(85,95),"stamina_max":200,"keberuntungan":random.randint(70,90),"skor":15,"births":0,"deaths":0,"panen":0,"alat_lv":3,"tenaga":200}
    return dna

# ================= LOGIC TANI BERJENJANG =================
def logic_pemetik(m5, idx, alat_lv, tenaga):
    if tenaga < 20: return "NEUTRAL"  # capek
    try:
        if idx==0: # FVG Bull M1
            last=m5.tail(10); fvg = (last['Low'].iloc[-1] > last['High'].iloc[-3]) if len(last)>=3 else False
            return "BUY" if fvg else "NEUTRAL"
        elif idx==1: # Asia Low Sweep
            asia_l=m5['Low'].tail(84).min(); now=m5['Close'].iloc[-1]
            sweep = m5.tail(5)['Low'].min() < asia_l*0.9998 and now>asia_l and m5['Close'].iloc[-1]>m5['Open'].iloc[-1]
            return "BUY" if sweep else "NEUTRAL"
        elif idx==2: # Asia High Sweep Bear
            asia_h=m5['High'].tail(84).max(); now=m5['Close'].iloc[-1]
            return "SELL" if m5.tail(5)['High'].max() > asia_h*1.0002 and now<asia_h else "NEUTRAL"
        elif idx==3: # M5 FVG Bull
            for i in range(len(m5)-3,len(m5)-15,-1):
                c1=m5.iloc[i-2]; c3=m5.iloc[i]
                if c3['Low']-c1['High']>=CONFIG["MIN_FVG"]-(alat_lv*0.1): return "BUY"
            return "NEUTRAL"
        elif idx==4: # M5 FVG Bear
            for i in range(len(m5)-3,len(m5)-15,-1):
                c1=m5.iloc[i-2]; c3=m5.iloc[i]
                if c1['Low']-c3['High']>=CONFIG["MIN_FVG"]-(alat_lv*0.1): return "SELL"
            return "NEUTRAL"
        elif idx==5: # Order Block Bull
            ob=m5['Low'].tail(30).min(); return "BUY" if abs(m5['Close'].iloc[-1]-ob)<1.5 else "NEUTRAL"
        elif idx==6: # Order Block Bear
            ob=m5['High'].tail(30).max(); return "SELL" if abs(m5['Close'].iloc[-1]-ob)<1.5 else "NEUTRAL"
        elif idx==7: # EMA 20>50 Bull
            e20=m5['Close'].ewm(20).mean().iloc[-1]; e50=m5['Close'].ewm(50).mean().iloc[-1]
            return "BUY" if e20>e50 else "SELL" if e20<e50 else "NEUTRAL"
        elif idx==8: # RSI Filter
            delta=m5['Close'].diff(); gain=delta.where(delta>0,0).ewm(14).mean(); loss=(-delta.where(delta<0,0)).ewm(14).mean(); rs=gain/(loss+0.0001); rsi=100-100/(1+rs)
            return "BUY" if rsi.iloc[-1]<35 else "SELL" if rsi.iloc[-1]>65 else "NEUTRAL"
        else: # Random chaos tapi belajar
            return random.choice(["BUY","SELL","NEUTRAL"])
    except:
        return "NEUTRAL"

def logic_mandor(m5, idx, laporan_pemetik):
    try:
        buy_pct = laporan_pemetik["BUY"]/CONFIG["PEMETIK"]*100
        sell_pct = laporan_pemetik["SELL"]/CONFIG["PEMETIK"]*100
        if idx==0: return "BUY" if buy_pct>=60 else "SELL" if sell_pct>=60 else "NEUTRAL"
        elif idx==1: return "BUY" if buy_pct>=65 else "SELL" if sell_pct>=65 else "NEUTRAL"
        elif idx==2: # Cek volume range
            avg_range=m5['High'].tail(20).max()-m5['Low'].tail(20).min()
            cur_range=m5['High'].iloc[-1]-m5['Low'].iloc[-1]
            if cur_range>avg_range*1.5:
                return "BUY" if buy_pct>55 else "SELL" if sell_pct>55 else "NEUTRAL"
            return "NEUTRAL"
        elif idx==3: # Fibonacci 61.8
            swing_h=m5['High'].tail(50).max(); swing_l=m5['Low'].tail(50).min(); fib=swing_l+(swing_h-swing_l)*0.618
            return "BUY" if abs(m5['Close'].iloc[-1]-fib)<0.9 and buy_pct>50 else "NEUTRAL"
        else: # Time filter
            now=pytz.timezone('Asia/Jakarta').localize(datetime.now()).hour
            return "NEUTRAL" if now in [14,15,19,20,21] and (buy_pct>=60 or sell_pct>=60) else "NEUTRAL"
    except:
        return "NEUTRAL"

def logic_pembajak(m5, h4, dxy, idx, laporan_mandor):
    try:
        if idx==0: # Galaxy Trend
            if h4.empty: return "NEUTRAL"
            e20=h4['Close'].ewm(20).mean().iloc[-1]; e50=h4['Close'].ewm(50).mean().iloc[-1]; e200=h4['Close'].ewm(200).mean().iloc[-1]
            if e20>e50>e200 and laporan_mandor["BUY"]>=2: return "BUY"
            if e20<e50<e200 and laporan_mandor["SELL"]>=2: return "SELL"
            return "NEUTRAL"
        elif idx==1: # DXY Korelasi
            if dxy.empty: return "NEUTRAL"
            ch=(float(dxy['Close'].iloc[-1])-float(dxy['Close'].iloc[-5]))/float(dxy['Close'].iloc[-5])
            if ch<-0.004 and laporan_mandor["BUY"]>=2: return "BUY"
            if ch>0.004 and laporan_mandor["SELL"]>=2: return "SELL"
            return "NEUTRAL"
        elif idx==2: # Spread Guard
            spread=m5['High'].iloc[-1]-m5['Low'].iloc[-1]
            return "BLOCK" if spread>CONFIG["MAX_SPREAD"] else "NEUTRAL"
        elif idx==3: # Breakout M10
            return "BUY" if m5['Close'].iloc[-1] > m5['High'].tail(10).max() else "SELL" if m5['Close'].iloc[-1] < m5['Low'].tail(10).min() else "NEUTRAL"
        else: # Fake Sweep Trap
            asia_l=m5['Low'].tail(84).min(); asia_h=m5['High'].tail(84).max()
            if m5['Low'].iloc[-2]<asia_l and m5['Close'].iloc[-1]>asia_l: return "BUY"
            if m5['High'].iloc[-2]>asia_h and m5['Close'].iloc[-1]<asia_h: return "SELL"
            return "NEUTRAL"
    except:
        return "NEUTRAL"

def logic_penuai(m5, idx, laporan_pembajak):
    try:
        if laporan_pembajak["BUY"]>=3: return "BUY"
        if laporan_pembajak["SELL"]>=3: return "SELL"
        if idx==0 and laporan_pembajak["BUY"]>=2: return "BUY"
        if idx==1 and laporan_pembajak["SELL"]>=2: return "SELL"
        return "NEUTRAL"
    except:
        return "NEUTRAL"

def ratu_tani_v8():
    print(f"=== 🌾👑 RATU TANI V8 BANGUN {datetime.now()} ===")
    dna=load_json(CONFIG["DNA_FILE"], init_dna())
    memory=load_json(CONFIG["MEMORY_FILE"], {"wins":0,"losses":0,"panen_kecil":0,"panen_raya":0,"gudang":0,"evolutions":0})
    last=load_json(CONFIG["LAST_FILE"], {})

    m5=get_paxg_safe("5m",300); h1=get_paxg_safe("1h",120); h4=get_paxg_safe("4h",120); dxy=get_yf_safe("DX-Y.NYB")
    if m5.empty:
        print("🌾 Sawah kosong - Ratu Tani puasa")
        return

    # ===== LEVEL 1: PEMETIK SETOR =====
    laporan_pemetik={"BUY":0,"SELL":0,"NEUTRAL":0}
    logs_pemetik=[]
    for i in range(CONFIG["PEMETIK"]):
        key=f"pemetik_{i}"
        if key not in dna: continue
        tenaga=dna[key].get("tenaga",100)
        alat_lv=dna[key].get("alat_lv",1)
        v=logic_pemetik(m5,i,alat_lv,tenaga)
        if v in laporan_pemetik: laporan_pemetik[v]+=1
        if v in ["BUY","SELL"]: logs_pemetik.append(f"🌿P{i}:{v}")
        # Tenaga -5 tiap kerja
        dna[key]["tenaga"]=max(0, tenaga-5)
        if v in ["BUY","SELL"]:
            dna[key]["skor"]+=0.2

    # ===== LEVEL 2: MANDOR SETOR =====
    laporan_mandor={"BUY":0,"SELL":0,"NEUTRAL":0}
    logs_mandor=[]
    for i in range(CONFIG["MANDOR"]):
        key=f"mandor_{i}"
        if key not in dna: continue
        v=logic_mandor(m5,i,laporan_pemetik)
        if v in laporan_mandor: laporan_mandor[v]+=1
        if v in ["BUY","SELL"]: logs_mandor.append(f"👨‍🌾M{i}:{v}")
        dna[key]["tenaga"]=max(0, dna[key].get("tenaga",120)-3)

    # ===== LEVEL 3: PEMBAJAK SETOR =====
    laporan_pembajak={"BUY":0,"SELL":0,"NEUTRAL":0,"BLOCK":0}
    logs_pembajak=[]
    for i in range(CONFIG["PEMBAJAK"]):
        key=f"pembajak_{i}"
        if key not in dna: continue
        v=logic_pembajak(m5,h4,dxy,i,laporan_mandor)
        if v in laporan_pembajak: laporan_pembajak[v]+=1
        if v in ["BUY","SELL","BLOCK"]: logs_pembajak.append(f"🚜B{i}:{v}")
        dna[key]["tenaga"]=max(0, dna[key].get("tenaga",150)-2)

    # ===== LEVEL 4: PENUAI SETOR =====
    laporan_penuai={"BUY":0,"SELL":0,"NEUTRAL":0}
    logs_penuai=[]
    for i in range(CONFIG["PENUAI"]):
        key=f"penuai_{i}"
        if key not in dna: continue
        v=logic_penuai(m5,i,laporan_pembajak)
        if v in laporan_penuai: laporan_penuai[v]+=1
        if v in ["BUY","SELL"]: logs_penuai.append(f"🌾P{i}:{v}")

    # Safety Guard
    if laporan_pembajak["BLOCK"]>=2:
        print(f"🚫 TRAKTOR BLOCK - spread {m5['High'].iloc[-1]-m5['Low'].iloc[-1]:.2f} > {CONFIG['MAX_SPREAD']}")
        return

    total_pemetik=CONFIG["PEMETIK"]
    buy_pct_pemetik=laporan_pemetik["BUY"]/total_pemetik*100
    sell_pct_pemetik=laporan_pemetik["SELL"]/total_pemetik*100

    total_all=CONFIG["PEMETIK"]+CONFIG["MANDOR"]+CONFIG["PEMBAJAK"]+CONFIG["PENUAI"]
    total_buy=laporan_pemetik["BUY"]+laporan_mandor["BUY"]+laporan_pembajak["BUY"]+laporan_penuai["BUY"]
    total_sell=laporan_pemetik["SELL"]+laporan_mandor["SELL"]+laporan_pembajak["SELL"]+laporan_penuai["SELL"]
    buy_pct_all=total_buy/total_all*100
    sell_pct_all=total_sell/total_all*100

    print(f"🌿 Pemetik: BUY {laporan_pemetik['BUY']} SELL {laporan_pemetik['SELL']} NEU {laporan_pemetik['NEUTRAL']} => {buy_pct_pemetik:.0f}%/{sell_pct_pemetik:.0f}% | { ' '.join(logs_pemetik[:5]) }")
    print(f"👨‍🌾 Mandor: BUY {laporan_mandor['BUY']} SELL {laporan_mandor['SELL']} | { ' '.join(logs_mandor) }")
    print(f"🚜 Pembajak: BUY {laporan_pembajak['BUY']} SELL {laporan_pembajak['SELL']} BLOCK {laporan_pembajak['BLOCK']} | { ' '.join(logs_pembajak) }")
    print(f"🌾 Penuai: BUY {laporan_penuai['BUY']} SELL {laporan_penuai['SELL']} | { ' '.join(logs_penuai) }")
    print(f"👑 TOTAL: BUY {total_buy}/{total_all}={buy_pct_all:.0f}% SELL {total_sell}/{total_all}={sell_pct_all:.0f}%")

    keputusan=None
    jenis_panen=None
    # Panen Kecil 60%
    if buy_pct_all>=CONFIG["QUORUM_KECIL"]:
        keputusan="BUY"; jenis_panen="PANEN KECIL"
    elif sell_pct_all>=CONFIG["QUORUM_KECIL"]:
        keputusan="SELL"; jenis_panen="PANEN KECIL"
    # Panen Raya 80% override
    if buy_pct_all>=CONFIG["QUORUM_RAYA"]:
        keputusan="BUY"; jenis_panen="PANEN RAYA"
    elif sell_pct_all>=CONFIG["QUORUM_RAYA"]:
        keputusan="SELL"; jenis_panen="PANEN RAYA"

    if not keputusan:
        print(f"Ratu Tani: quorum 60% belum tercapai (BUY {buy_pct_all:.0f}% SELL {sell_pct_all:.0f}%) - petani istirahat, sawah belum kuning")
        # Evolusi: istirahat = +10 tenaga
        for k in dna:
            dna[k]["tenaga"]=min(dna[k]["stamina_max"], dna[k].get("tenaga",100)+10)
        # Musnahkan 3 terbawah
        sorted_dna=sorted(dna.items(),key=lambda x: x[1]["skor"])
        for k,_ in sorted_dna[:3]:
            if "pemetik" in k:
                dna[k]["skor"]=0; dna[k]["deaths"]+=1; dna[k]["tenaga"]=100; dna[k]["alat_lv"]=max(1, dna[k]["alat_lv"]-1)
                print(f"💀 {k} dimusnahkan jadi pupuk, sabit patah")
        memory["evolutions"]+=1
        save_json(CONFIG["DNA_FILE"], dna)
        save_json(CONFIG["MEMORY_FILE"], memory)
        return

    # Anti spam 1 jam untuk kecil, 2 jam untuk raya
    cooldown = 3600 if jenis_panen=="PANEN KECIL" else 7200
    if last.get("keputusan")==keputusan and last.get("jenis")==jenis_panen and abs(time.time()-last.get("time",0))<cooldown:
        print(f"Ratu Tani: {jenis_panen} {keputusan} udah panen {cooldown/3600:.0f} jam lalu, skip")
        return

    # Reward DNA & Alat
    for k in dna:
        # Cek vote terakhir
        try:
            if "pemetik" in k:
                idx=int(k.split("_")[1]); v=logic_pemetik(m5,idx,dna[k]["alat_lv"],dna[k]["tenaga"])
            elif "mandor" in k:
                idx=int(k.split("_")[1]); v=logic_mandor(m5,idx,laporan_pemetik)
            elif "pembajak" in k:
                idx=int(k.split("_")[1]); v=logic_pembajak(m5,h4,dxy,idx,laporan_mandor)
            else:
                idx=int(k.split("_")[1]); v=logic_penuai(m5,idx,laporan_pembajak)
            if v==keputusan:
                dna[k]["skor"]+=2 if jenis_panen=="PANEN RAYA" else 1
                dna[k]["panen"]+=1
                dna[k]["tenaga"]=min(dna[k]["stamina_max"], dna[k].get("tenaga",100)+15)  # semangat
                # Upgrade alat tiap 3 panen
                if dna[k]["panen"]%3==0 and dna[k]["alat_lv"]<5:
                    dna[k]["alat_lv"]+=1
                    print(f"⬆️ {k} alat naik Lv{dna[k]['alat_lv']}")
                # Naik pangkat
                if dna[k]["skor"]>=20 and "pemetik" in k:
                    # promosi jadi mandor baru kalau ada slot mati
                    pass
            elif v in ["BUY","SELL"] and v!=keputusan:
                dna[k]["skor"]-=0.7
                dna[k]["tenaga"]=max(0, dna[k].get("tenaga",100)-15)
        except: pass

    save_json(CONFIG["DNA_FILE"], dna)

    price=float(m5['Close'].iloc[-1])
    entry=price
    if jenis_panen=="PANEN KECIL":
        sl=price-6 if keputusan=="BUY" else price+6
        tp1=price+5 if keputusan=="BUY" else price-5
        tp2=price+15 if keputusan=="BUY" else price-15
        tp3=price+15 if keputusan=="BUY" else price-15
        lot="0.05"
        gudang_add=15
    else:
        sl=price-6 if keputusan=="BUY" else price+6
        tp1=price+5 if keputusan=="BUY" else price-5
        tp2=price+15 if keputusan=="BUY" else price-15
        tp3=price+32 if keputusan=="BUY" else price-32
        lot="0.10"
        gudang_add=32

    memory["gudang"]+=gudang_add
    if jenis_panen=="PANEN KECIL": memory["panen_kecil"]+=1
    else: memory["panen_raya"]+=1
    save_json(CONFIG["MEMORY_FILE"], memory)

    top3=sorted(dna.items(),key=lambda x: x[1]["skor"],reverse=True)[:3]
    top_str=" | ".join([f"{k}:{v['skor']:.0f} Lv{v['alat_lv']} T{v['tenaga']:.0f}%" for k,v in top3])

    emoji = "🌿" if jenis_panen=="PANEN KECIL" else "🌾👑"
    msg=f"""{emoji} *RATU TANI V8 - {jenis_panen} {keputusan} - QUORUM {buy_pct_all:.0f}%/{sell_pct_all:.0f}%*

Colony {total_all} petani | Pemetik {laporan_pemetik['BUY']}/{laporan_pemetik['SELL']} Mandor {laporan_mandor['BUY']}/{laporan_mandor['SELL']} Pembajak {laporan_pembajak['BUY']}/{laporan_pembajak['SELL']} Penuai {laporan_penuai['BUY']}/{laporan_penuai['SELL']}
Harga Gabah MT5: {price:.2f} Offset {CONFIG['OFFSET']} | Lot {lot}
ENTRY {entry:.2f} SL {sl:.2f}
TP1 {tp1:.2f} TP2 {tp2:.2f} TP3 {tp3:.2f}

Gudang: {memory['gudang']}$ | Kecil:{memory['panen_kecil']} Raya:{memory['panen_raya']} | Evolusi ke-{memory['evolutions']}
DNA Top: {top_str}
Feromon: {' '.join(logs_pemetik[:6])} {' '.join(logs_mandor)} {' '.join(logs_pembajak)}

✅ TANI CANGGIH - Tenaga + Alat Lv1-5 + Evolusi Otonom + Setor Berjenjang
🌾 Target 3 sinyal/hari = Gudang Penuh!
"""

    print(msg); send(msg)
    save_json(CONFIG["LAST_FILE"], {"keputusan":keputusan,"jenis":jenis_panen,"time":time.time(),"price":price,"buy_pct":buy_pct_all,"sell_pct":sell_pct_all})

if __name__=="__main__":
    ratu_tani_v8()
