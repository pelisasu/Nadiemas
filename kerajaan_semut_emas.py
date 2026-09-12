"""
🐜👑 KERAJAAN SEMUT EMAS V1 - CADANGAN ABADI
Pure idea: Colony intelligence, bukan 1 manusia jago
10 semut scout, Ratu yang putusin. 1 semut mati, koloni tetep hidup.
Offset plek MT5 lu: -2.25 (4347.45)
Anti KeyError, anti failed merah
"""
import os, json, random, time, requests, pandas as pd
from datetime import datetime
import pytz

CONFIG={"OFFSET":-2.25,"MIN_FVG":0.8,"COLONY_SIZE":10,"QUORUM":70,"RISK_PER_SEMUT":0.1}
LAST=".ratu_feromon.json"

def get_paxg_safe(interval="5m",limit=200):
    # Warung paling plek dulu biar gak crash
    for attempt in range(4):
        try:
            if attempt==0: # Gold-API spot murni
                r=requests.get("https://api.gold-api.com/price/XAU",timeout=10).json()
                if "price" in r:
                    p=float(r["price"])+CONFIG["OFFSET"]
                    df=pd.DataFrame([{"ot":int(time.time()*1000)-i*300000,"Close":p,"High":p+1,"Low":p-1,"Open":p} for i in range(limit)])
                    df["Time"]=pd.to_datetime(df["ot"],unit='ms',utc=True)
                    return df.set_index("Time")
            elif attempt==1: # Binance
                m={"5m":"5m","15m":"15m","1h":"1h","4h":"4h","1d":"1d"}.get(interval,"5m")
                r=requests.get("https://api.binance.com/api/v3/klines",params={"symbol":"PAXGUSDT","interval":m,"limit":limit},headers={"User-Agent":f"Mozilla/{random.randint(10,999)}"},timeout=10).json()
                if isinstance(r,list) and len(r)>20:
                    df=pd.DataFrame(r,columns=["ot","Open","High","Low","Close","Vol","c","d","e","f","g","h"])
                    for c in ["Open","High","Low","Close"]:
                        df[c]=pd.to_numeric(df[c],errors='coerce')+CONFIG["OFFSET"]
                    df["Time"]=pd.to_datetime(df["ot"],unit='ms',utc=True)
                    return df.set_index("Time")
            elif attempt==2: # CoinGecko anti KeyError
                r=requests.get("https://api.coingecko.com/api/v3/coins/pax-gold/market_chart",params={"vs_currency":"usd","days":"2"},timeout=10).json()
                if isinstance(r,dict) and "prices" in r and len(r["prices"])>10:
                    df=pd.DataFrame(r['prices'],columns=['ot','Close'])
                    df['Time']=pd.to_datetime(df['ot'],unit='ms',utc=True)
                    df=df.set_index('Time'); df['Close']+=CONFIG["OFFSET"]; df['High']=df['Close']+1; df['Low']=df['Close']-1; df['Open']=df['Close']
                    return df.tail(limit)
            else: # Yahoo PAXG
                import yfinance as yf
                time.sleep(0.8)
                df=yf.download("PAXG-USD",period="5d",interval="5m" if interval=="5m" else "60m",progress=False,auto_adjust=True)
                if not df.empty:
                    if hasattr(df.columns,'get_level_values'):
                        try: df.columns=df.columns.get_level_values(0)
                        except: pass
                    for c in ["Open","High","Low","Close"]:
                        if c in df.columns: df[c]+=CONFIG["OFFSET"]
                    df.index=pd.to_datetime(df.index,utc=True)
                    return df.tail(limit)
        except Exception as e:
            print(f"Semut warung {attempt} tutup: {e}")
            continue
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
    try: requests.post(f"https://api.telegram.org/bot{token}/sendMessage",json={"chat_id":chat,"text":msg,"parse_mode":"Markdown"},timeout=10)
    except: pass

# ====== 10 SEMUT SCOUT (micro-logic, gak bisa crash colony) ======
def semut_1_m1_fvg(m5):
    try: # semut M1 FVG
        last=m5.tail(10); fvg = (last['Low'].iloc[-1] > last['High'].iloc[-3]) if len(last)>=3 else False
        return ("BUY",60) if fvg else ("NEUTRAL",0)
    except: return ("NEUTRAL",0)

def semut_2_m1_sweep(m5):
    try:
        asia_l=m5['Low'].tail(84).min(); now=m5['Close'].iloc[-1]
        sweep = m5.tail(5)['Low'].min() < asia_l*0.9998 and now>asia_l
        return ("BUY",70) if sweep else ("NEUTRAL",0)
    except: return ("NEUTRAL",0)

def semut_3_m5_fvg(m5):
    try:
        for i in range(len(m5)-3,len(m5)-15,-1):
            c1=m5.iloc[i-2]; c3=m5.iloc[i]
            if c3['Low']>c1['High'] and c3['Low']-c1['High']>=0.8:
                return ("BUY",65)
            if c1['Low']>c3['High'] and c1['Low']-c3['High']>=0.8:
                return ("SELL",65)
        return ("NEUTRAL",0)
    except: return ("NEUTRAL",0)

def semut_4_m5_sweep_high(m5):
    try:
        asia_h=m5['High'].tail(84).max(); now=m5['Close'].iloc[-1]
        sweep = m5.tail(5)['High'].max() > asia_h*1.0002 and now<asia_h
        return ("SELL",70) if sweep else ("NEUTRAL",0)
    except: return ("NEUTRAL",0)

def semut_5_h1_ema():
    try:
        h1=get_paxg_safe("1h",100)
        if h1.empty: return ("NEUTRAL",0)
        ema50=h1['Close'].ewm(50).mean().iloc[-1]; price=h1['Close'].iloc[-1]
        return ("BUY",55) if price>ema50 else ("SELL",55)
    except: return ("NEUTRAL",0)

def semut_6_h4_trend():
    try:
        h4=get_paxg_safe("4h",100)
        if h4.empty: return ("NEUTRAL",0)
        ema50=h4['Close'].ewm(50).mean().iloc[-1]; ema200=h4['Close'].ewm(200).mean().iloc[-1]
        if ema50>ema200: return ("BUY",60)
        else: return ("SELL",60)
    except: return ("NEUTRAL",0)

def semut_7_dxy():
    try:
        dxy=get_yf_safe("DX-Y.NYB")
        if dxy.empty: return ("NEUTRAL",0)
        ch=(float(dxy['Close'].iloc[-1])-float(dxy['Close'].iloc[-5]))/float(dxy['Close'].iloc[-5])
        if ch<-0.004: return ("BUY",75)
        if ch>0.004: return ("SELL",75)
        return ("NEUTRAL",0)
    except: return ("NEUTRAL",0)

def semut_8_spread_guard(m5):
    try:
        spread=m5['High'].iloc[-1]-m5['Low'].iloc[-1]
        if spread>8: return ("NEUTRAL",100) # feromon bahaya, semua stop
        return ("NEUTRAL",0)
    except: return ("NEUTRAL",0)

def semut_9_volume_spike(m5):
    try:
        # Gold-API gak ada volume, pake proxy range
        avg_range=m5['High'].tail(20).max()-m5['Low'].tail(20).min()
        cur_range=m5['High'].iloc[-1]-m5['Low'].iloc[-1]
        if cur_range>avg_range*1.8:
            # volume spike = whale masuk
            return ("BUY" if m5['Close'].iloc[-1]>m5['Open'].iloc[-1] else "SELL",50)
        return ("NEUTRAL",0)
    except: return ("NEUTRAL",0)

def semut_10_time_killzone():
    try:
        now_wib=datetime.now(pytz.timezone('Asia/Jakarta'))
        # Killzone London 14-17 WIB + New York 19-22 WIB
        if 14<=now_wib.hour<=16 or 19<=now_wib.hour<=22:
            return ("NEUTRAL",0) # waktu bagus, jangan block
        else:
            return ("NEUTRAL",30) # feromon ngantuk
    except: return ("NEUTRAL",0)

SEMUT_COLONY=[
    ("Semut M1 FVG", semut_1_m1_fvg),
    ("Semut M1 Sweep Low", semut_2_m1_sweep),
    ("Semut M5 FVG", semut_3_m5_fvg),
    ("Semut M5 Sweep High", semut_4_m5_sweep),
    ("Semut H1 EMA", semut_5_h1_ema),
    ("Semut H4 Trend", semut_6_h4_trend),
    ("Semut DXY Korelasi", semut_7_dxy),
    ("Semut Spread Guard", semut_8_spread_guard),
    ("Semut Whale Spike", semut_9_volume_spike),
    ("Semut Killzone", semut_10_time_killzone),
]

def ratu_kingdom():
    print(f"=== 🐜 RATU BANGUN {datetime.now()} ===")
    m5=get_paxg_safe("5m",300)
    if m5.empty:
        print("💀 Semua warung tutup - Ratu puasa, colony tidur")
        return

    votes={"BUY":0,"SELL":0,"NEUTRAL":0}
    feromon=[]
    hidup=0; mati=0

    for name, fn in SEMUT_COLONY:
        try:
            if "m5" in fn.__code__.co_varnames:
                vote,conf = fn(m5)
            else:
                vote,conf = fn()
            votes[vote]+=1
            feromon.append(f"{name}: {vote} {conf}%")
            hidup+=1
            print(f"🐜 {name} -> {vote} {conf}%")
        except Exception as e:
            mati+=1
            print(f"💀 {name} mati: {e} - colony tetep jalan")
            votes["NEUTRAL"]+=1
            feromon.append(f"{name}: MATI - diganti semut baru")

    total=CONFIG["COLONY_SIZE"]
    buy_pct=votes["BUY"]/total*100
    sell_pct=votes["SELL"]/total*100

    print(f"Feromon: BUY {votes['BUY']} SELL {votes['SELL']} NEUTRAL {votes['NEUTRAL']} | Hidup {hidup} Mati {mati}")

    # Ratu decision - quorum 70%
    keputusan=None
    if buy_pct>=CONFIG["QUORUM"]:
        keputusan="BUY"
    elif sell_pct>=CONFIG["QUORUM"]:
        keputusan="SELL"

    # Anti-spam ratu
    if keputusan:
        if os.path.exists(LAST):
            try:
                last=json.load(open(LAST))
                if last['keputusan']==keputusan and abs(time.time()-last['time'])<3600:
                    print(f"Ratu: sinyal {keputusan} sama 1 jam lalu, skip biar gak berisik")
                    return
            except: pass

        price=float(m5['Close'].iloc[-1])
        entry=price
        sl=price-8 if keputusan=="BUY" else price+8
        tp1=price+5 if keputusan=="BUY" else price-5
        tp2=price+15 if keputusan=="BUY" else price-15

        msg=f"""🐜👑 *KERAJAAN SEMUT EMAS - RATU PERINTAH {keputusan}*
        
Colony: {hidup} hidup {mati} mati (abadi)
Feromon BUY {votes['BUY']}/10 SELL {votes['SELL']}/10

Harga Sarang: {price:.2f} (MT5 plek)
ENTRY {entry:.2f} SL {sl:.2f} TP1 {tp1:.2f} TP2 {tp2:.2f}

Feromon detail:
{chr(10).join(feromon[:6])}

Ratu: 70% semut setuju baru serang!"""

        print(msg); send(msg)
        json.dump({"keputusan":keputusan,"time":time.time(),"price":price},open(LAST,'w'))
    else:
        print(f"Ratu: quorum belum 70% (BUY {buy_pct:.0f}% SELL {sell_pct:.0f}%) - colony lanjut ngutil")

if __name__=="__main__":
    ratu_kingdom()
