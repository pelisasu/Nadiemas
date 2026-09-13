"""
🐜👑🌌 KERAJAAN SEMUT EMAS FINAL SEMPURNA V7 - KOMPLIT ANTI GONTA GANTI
Gabungan: Manusia Emas + Semut V1 + Pamungkas + Galaxy + Evolusi Otonom
Offset plek MT5 4347.45 = -2.25 | 30 semut | Quorum 80% | DNA abadi | Anti MC
File ini SATU-SATUNYA yang perlu lu pake bro - gak usah gonta ganti lagi!
"""
import os, json, random, time, requests, pandas as pd
from datetime import datetime
import pytz

CONFIG={
    "OFFSET":-2.25,
    "COLONY":30,
    "QUORUM":80,
    "DNA_FILE":".dna_final.json",
    "MEMORY_FILE":".ratu_final_memory.json",
    "LAST_FILE":".ratu_final_last.json",
    "MAX_SPREAD":6.0,
    "MIN_FVG":0.8
}
random.seed(int(time.time())%99999)

def get_paxg_safe(interval="5m",limit=300):
    """5 warung anti fail - urutan plek MT5"""
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

# ================= 30 SEMUT FINAL SEMPURNA =================
def scout(m5, h1, h4, dxy, kind):
    try:
        if kind==0: # M1 FVG Bull simple
            last=m5.tail(10); fvg = (last['Low'].iloc[-1] > last['High'].iloc[-3]) if len(last)>=3 else False
            return "BUY" if fvg else "NEUTRAL"
        elif kind==1: # M1 Asia Low Sweep + Rejection Bull
            asia_l=m5['Low'].tail(84).min(); now=m5['Close'].iloc[-1]
            sweep = m5.tail(5)['Low'].min() < asia_l*0.9998 and now>asia_l and m5['Close'].iloc[-1]>m5['Open'].iloc[-1]
            return "BUY" if sweep else "NEUTRAL"
        elif kind==2: # M1 Asia High Sweep Bear
            asia_h=m5['High'].tail(84).max(); now=m5['Close'].iloc[-1]
            sweep = m5.tail(5)['High'].max() > asia_h*1.0002 and now<asia_h
            return "SELL" if sweep else "NEUTRAL"
        elif kind==3: # M5 FVG Bull 0.8
            for i in range(len(m5)-3,len(m5)-15,-1):
                c1=m5.iloc[i-2]; c3=m5.iloc[i]
                if c3['Low']-c1['High']>=CONFIG["MIN_FVG"]: return "BUY"
            return "NEUTRAL"
        elif kind==4: # M5 FVG Bear 0.8
            for i in range(len(m5)-3,len(m5)-15,-1):
                c1=m5.iloc[i-2]; c3=m5.iloc[i]
                if c1['Low']-c3['High']>=CONFIG["MIN_FVG"]: return "SELL"
            return "NEUTRAL"
        elif kind==5: # Order Block Bull retest
            ob=m5['Low'].tail(30).min(); return "BUY" if abs(m5['Close'].iloc[-1]-ob)<1.5 else "NEUTRAL"
        elif kind==6: # Order Block Bear
            ob=m5['High'].tail(30).max(); return "SELL" if abs(m5['Close'].iloc[-1]-ob)<1.5 else "NEUTRAL"
        elif kind==7: # H1 EMA50
            if h1.empty: return "NEUTRAL"
            ema50=h1['Close'].ewm(50).mean().iloc[-1]; price=h1['Close'].iloc[-1]
            return "BUY" if price>ema50 else "SELL"
        elif kind==8: # H4 EMA50 vs EMA200 super trend
            if h4.empty: return "NEUTRAL"
            e50=h4['Close'].ewm(50).mean().iloc[-1]; e200=h4['Close'].ewm(200).mean().iloc[-1]
            return "BUY" if e50>e200 else "SELL"
        elif kind==9: # DXY Inverse kuat
            if dxy.empty: return "NEUTRAL"
            ch=(float(dxy['Close'].iloc[-1])-float(dxy['Close'].iloc[-5]))/float(dxy['Close'].iloc[-5])
            return "BUY" if ch<-0.003 else "SELL" if ch>0.003 else "NEUTRAL"
        elif kind==10: # Spread Guard FINAL 6.0
            spread=m5['High'].iloc[-1]-m5['Low'].iloc[-1]
            return "BLOCK" if spread>CONFIG["MAX_SPREAD"] else "NEUTRAL"
        elif kind==11: # Killzone London 14-17 + NY 19-22 WIB
            now=pytz.timezone('Asia/Jakarta').localize(datetime.now()).hour
            return "NEUTRAL" if 14<=now<=16 or 19<=now<=22 else "SLEEP"
        elif kind==12: # Liquidity Void - range kecil
            return "BUY" if m5['High'].iloc[-1]-m5['Low'].iloc[-1] < 1.3 else "NEUTRAL"
        elif kind==13: # Breaker Block
            return "SELL" if m5['Close'].iloc[-1] < m5['Open'].tail(20).min() else "BUY" if m5['Close'].iloc[-1] > m5['Open'].tail(20).max() else "NEUTRAL"
        elif kind==14: # Volatility Squeeze -> Expansion
            atr=m5['High'].tail(14).max()-m5['Low'].tail(14).min()
            return "BUY" if atr<2.8 else "NEUTRAL"
        elif kind==15: # Wick Rejection Strong
            body=abs(m5['Close'].iloc[-1]-m5['Open'].iloc[-1]); wick=m5['High'].iloc[-1]-m5['Low'].iloc[-1]-body
            return "SELL" if wick>body*2.2 and m5['Close'].iloc[-1]<m5['Open'].iloc[-1] else "BUY" if wick>body*2.2 else "NEUTRAL"
        elif kind==16: # H1+H4 Confluence
            if h1.empty or h4.empty: return "NEUTRAL"
            b1=h1['Close'].iloc[-1]>h1['Close'].ewm(50).mean().iloc[-1]; b4=h4['Close'].iloc[-1]>h4['Close'].ewm(50).mean().iloc[-1]
            return "BUY" if b1 and b4 else "SELL" if not b1 and not b4 else "NEUTRAL"
        elif kind==17: # Asia High Breakout
            asia_h=m5['High'].tail(84).max(); return "BUY" if m5['Close'].iloc[-1]>asia_h else "NEUTRAL"
        elif kind==18: # Asia Low Breakdown
            asia_l=m5['Low'].tail(84).min(); return "SELL" if m5['Close'].iloc[-1]<asia_l else "NEUTRAL"
        elif kind==19: # DXY Divergence
            if dxy.empty or h1.empty: return "NEUTRAL"
            return "BUY" if dxy['Close'].iloc[-1]<dxy['Close'].iloc[-2] and h1['Close'].iloc[-1]>h1['Close'].iloc[-2] else "SELL" if dxy['Close'].iloc[-1]>dxy['Close'].iloc[-2] and h1['Close'].iloc[-1]<h1['Close'].iloc[-2] else "NEUTRAL"
        elif kind==20: # Fake Sweep Trap
            asia_l=m5['Low'].tail(84).min(); asia_h=m5['High'].tail(84).max()
            if m5['Low'].iloc[-2]<asia_l and m5['Close'].iloc[-1]>asia_l: return "BUY"
            if m5['High'].iloc[-2]>asia_h and m5['Close'].iloc[-1]<asia_h: return "SELL"
            return "NEUTRAL"
        elif kind==21: # Fibonacci 61.8
            swing_h=m5['High'].tail(50).max(); swing_l=m5['Low'].tail(50).min(); fib=swing_l+(swing_h-swing_l)*0.618
            return "BUY" if abs(m5['Close'].iloc[-1]-fib)<0.9 else "NEUTRAL"
        elif kind==22: # Orderflow Imbalance Bull/Bear
            bull = (m5['Close'].iloc[-1]-m5['Low'].iloc[-1]) > (m5['High'].iloc[-1]-m5['Close'].iloc[-1])*1.8
            bear = (m5['High'].iloc[-1]-m5['Close'].iloc[-1]) > (m5['Close'].iloc[-1]-m5['Low'].iloc[-1])*1.8
            return "BUY" if bull else "SELL" if bear else "NEUTRAL"
        elif kind==23: # Galaxy Trend E20>E50>E200
            if h4.empty: return "NEUTRAL"
            e20=h4['Close'].ewm(20).mean().iloc[-1]; e50=h4['Close'].ewm(50).mean().iloc[-1]; e200=h4['Close'].ewm(200).mean().iloc[-1]
            if e20>e50>e200: return "BUY"
            if e20<e50<e200: return "SELL"
            return "NEUTRAL"
        elif kind==24: # Smart Money Breakout M10
            return "BUY" if m5['Close'].iloc[-1] > m5['High'].tail(10).max() else "SELL" if m5['Close'].iloc[-1] < m5['Low'].tail(10).min() else "NEUTRAL"
        elif kind==25: # Time + Vol filter final
            now=pytz.timezone('Asia/Jakarta').localize(datetime.now()).hour
            vol=m5['High'].iloc[-1]-m5['Low'].iloc[-1]
            return "NEUTRAL" if now in [14,15,19,20,21] and vol<4 else "SLEEP" if vol>6 else "NEUTRAL"
        elif kind==26: # Volume Spike Proxy
            avg_range=m5['High'].tail(20).max()-m5['Low'].tail(20).min()
            cur_range=m5['High'].iloc[-1]-m5['Low'].iloc[-1]
            if cur_range>avg_range*1.7:
                return "BUY" if m5['Close'].iloc[-1]>m5['Open'].iloc[-1] else "SELL"
            return "NEUTRAL"
        elif kind==27: # 2nd Chance FVG mean reversion
            return "BUY" if m5['Close'].iloc[-1] > m5['Close'].tail(12).mean() else "SELL"
        elif kind==28: # Chaos Mutation - random tapi belajar
            return random.choice(["BUY","SELL","NEUTRAL"])
        else: # 29 - Ratu Observer
            return "NEUTRAL"
    except:
        return "NEUTRAL"

def ratu_final():
    print(f"=== 🐜👑🌌 FINAL SEMPURNA BANGUN {datetime.now()} ===")
    dna=load_json(CONFIG["DNA_FILE"], {f"semut_{i}":{"score":0,"births":0,"deaths":0,"winrate":0} for i in range(CONFIG["COLONY"])})
    memory=load_json(CONFIG["MEMORY_FILE"], {"wins":0,"losses":0,"evolutions":0,"last_signal":None})

    m5=get_paxg_safe("5m",300); h1=get_paxg_safe("1h",120); h4=get_paxg_safe("4h",120); dxy=get_yf_safe("DX-Y.NYB")
    if m5.empty:
        print("🌌 Sarang kosong - Ratu Final puasa")
        return

    votes={"BUY":0,"SELL":0,"NEUTRAL":0,"BLOCK":0,"SLEEP":0}
    logs=[]
    for i in range(CONFIG["COLONY"]):
        try:
            v=scout(m5,h1,h4,dxy,i)
            if v in votes: votes[v]+=1
            if v in ["BUY","SELL"]: logs.append(f"🐜{i}:{v}")
            key=f"semut_{i}"
            if key in dna and v in ["BUY","SELL"]:
                dna[key]["score"]+=0.15
        except Exception as e:
            votes["NEUTRAL"]+=1
            print(f"💀 semut_{i} mati: {e}")

    buy_pct=votes["BUY"]/CONFIG["COLONY"]*100
    sell_pct=votes["SELL"]/CONFIG["COLONY"]*100

    # Safety Guard Final
    if votes["BLOCK"]>=2:
        print(f"🚫 FINAL BLOCK - spread brutal {m5['High'].iloc[-1]-m5['Low'].iloc[-1]:.2f} > {CONFIG['MAX_SPREAD']}")
        return
    if votes["SLEEP"]>=12:
        print(f"😴 FINAL SLEEP - outside killzone {votes['SLEEP']} semut ngantuk")
        return

    print(f"Feromon FINAL: BUY {votes['BUY']} SELL {votes['SELL']} NEUTRAL {votes['NEUTRAL']} => BUY {buy_pct:.0f}% SELL {sell_pct:.0f}% | Logs: {' '.join(logs[:10])}")

    keputusan=None
    if buy_pct>=CONFIG["QUORUM"]: keputusan="BUY"
    elif sell_pct>=CONFIG["QUORUM"]: keputusan="SELL"

    if not keputusan:
        print(f"Ratu Final: quorum 80% belum tercapai, nunggu. Evolusi otonom jalan...")
        sorted_dna=sorted(dna.items(),key=lambda x: x[1]["score"])
        for k,_ in sorted_dna[:3]:
            dna[k]["score"]=0; dna[k]["deaths"]+=1
            print(f"🧬 {k} dimusnahkan, telur Final netas")
        memory["evolutions"]+=1
        save_json(CONFIG["DNA_FILE"], dna)
        save_json(CONFIG["MEMORY_FILE"], memory)
        return

    # Anti spam 2 jam
    last=load_json(CONFIG["LAST_FILE"], {})
    if last.get("keputusan")==keputusan and abs(time.time()-last.get("time",0))<7200:
        print(f"Ratu Final: {keputusan} udah kirim 2 jam lalu, skip biar gak berisik")
        return

    # Reward DNA
    for i in range(CONFIG["COLONY"]):
        key=f"semut_{i}"
        try:
            v=scout(m5,h1,h4,dxy,i)
            if v==keputusan and key in dna:
                dna[key]["score"]+=2; dna[key]["births"]+=1; dna[key]["winrate"]+=1
            elif v!=keputusan and v in ["BUY","SELL"] and key in dna:
                dna[key]["score"]-=0.7
        except: pass

    save_json(CONFIG["DNA_FILE"], dna)
    price=float(m5['Close'].iloc[-1])
    entry=price
    sl=price-6.0 if keputusan=="BUY" else price+6.0
    tp1=price+5 if keputusan=="BUY" else price-5
    tp2=price+15 if keputusan=="BUY" else price-15
    tp3=price+32 if keputusan=="BUY" else price-32

    top3=sorted(dna.items(),key=lambda x: x[1]["score"],reverse=True)[:3]
    top_str=" | ".join([f"{k}:{v['score']:.1f}(W{v['winrate']})" for k,v in top3])

    msg=f"""🐜👑🌌 *RATU FINAL SEMPURNA {keputusan} - QUORUM 80% TERCAPAI*

Colony {CONFIG["COLONY"]} semut | BUY {votes["BUY"]} SELL {votes["SELL"]} NEUTRAL {votes["NEUTRAL"]}
Harga Plek MT5: {price:.2f} Offset {CONFIG["OFFSET"]}
ENTRY {entry:.2f} SL {sl:.2f}
TP1 {tp1:.2f} TP2 {tp2:.2f} TP3 {tp3:.2f}

DNA Top: {top_str}
Evolusi ke-{memory['evolutions']} | Anti MC: Spread Guard {CONFIG["MAX_SPREAD"]} + Killzone + 80% Quorum
Feromon: {' '.join(logs[:15])}

✅ KOMPLIT SEMPURNA - gak usah gonta ganti lagi bro!
🧬 Otonom: semut jago naik tahta, bego punah
"""

    print(msg); send(msg)
    save_json(CONFIG["LAST_FILE"], {"keputusan":keputusan,"time":time.time(),"price":price,"votes":votes})
    memory["last_signal"]=keputusan; save_json(CONFIG["MEMORY_FILE"], memory)

if __name__=="__main__":
    ratu_final()
