# MANUSIA EMAS LENGKAP - ORGAN+NUTRISI+PAKAIAN+KENDARAAN+GERAK
import os,json,random,time,requests,pandas as pd
from datetime import datetime
import pytz
CONFIG={"MT5_OFFSET":-2.25,"MIN_FVG":0.8,"SWEEP":0.0002,"KILLZONE":(7,16),"VIX_MAX":28,"MAX_SPREAD":8.0,"RISK_PCT":1}
LAST=".last_manusia.json"

def cek_nutrisi():
    try:
        requests.get("https://api.binance.com/api/v3/ping",timeout=5)
        return True
    except:
        try: requests.get("https://api.coingecko.com/api/v3/ping",timeout=5); return True
        except: return False

def cek_pakaian(m5):
    # Baju: spread filter
    spread = m5['High'].iloc[-1] - m5['Low'].iloc[-1]
    if spread > CONFIG["MAX_SPREAD"]:
        return False, f"👕 Baju kekecilan spread {spread:.1f} > {CONFIG['MAX_SPREAD']} - market brutal skip"
    # Jas hujan: jam news merah 13:30 & 19:30 WIB (NFP/CPI)
    now_wib = datetime.now(pytz.timezone('Asia/Jakarta'))
    if now_wib.hour in [19,20] and now_wib.minute<40: # 19:30-20:30 WIB = 12:30 UTC news
        return False, f"🌧️ Pake jas hujan news merah {now_wib.hour}:{now_wib.minute} WIB - skip"
    return True, f"👕 Pakaian OK spread {spread:.1f} USD"

def get_paxg(interval="5m",limit=300):
    try:
        m={"5m":"5m","60m":"1h","1h":"1h","4h":"4h","1d":"1d"}.get(interval,"5m")
        r=requests.get("https://api.binance.com/api/v3/klines",params={"symbol":"PAXGUSDT","interval":m,"limit":limit},headers={"User-Agent":f"Mozilla {random.randint(1,99)}"},timeout=8).json()
        if isinstance(r,dict): raise Exception("blocked")
        df=pd.DataFrame(r,columns=["ot","Open","High","Low","Close","Vol","c","d","e","f","g","h"])
        for c in ["Open","High","Low","Close"]: df[c]=df[c].astype(float)+CONFIG["MT5_OFFSET"]
        df["Time"]=pd.to_datetime(df["ot"],unit='ms',utc=True)
        return df.set_index("Time")
    except:
        r=requests.get("https://api.coingecko.com/api/v3/coins/pax-gold/market_chart?vs_currency=usd&days=2&interval=5m",timeout=10).json()
        df=pd.DataFrame(r['prices'],columns=['ot','Close']);df['Time']=pd.to_datetime(df['ot'],unit='ms',utc=True);df=df.set_index('Time')
        df['High']=df['Close']*1.0005+CONFIG["MT5_OFFSET"];df['Low']=df['Close']*0.9995+CONFIG["MT5_OFFSET"];df['Open']=df['Close'].shift(1).fillna(df['Close'])+CONFIG["MT5_OFFSET"];df['Close']+=CONFIG["MT5_OFFSET"]
        return df.tail(limit)

def get_yf(sym,period="5d",interval="60m"):
    try:
        import yfinance as yf;time.sleep(0.8)
        df=yf.download(sym,period=period,interval=interval,progress=False,auto_adjust=True)
        if hasattr(df.columns,'get_level_values'):
            try: df.columns=df.columns.get_level_values(0)
            except: pass
        return df.dropna()
    except: return pd.DataFrame()

def send(msg):
    token=os.getenv("TELEGRAM_TOKEN");chat=os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat: print(msg);return
    try: requests.post(f"https://api.telegram.org/bot{token}/sendMessage",json={"chat_id":chat,"text":msg,"parse_mode":"Markdown"},timeout=10)
    except: pass

def manusia_lengkap():
    # NUTRISI
    if not cek_nutrisi(): return None, "💀 Mati lemas gak ada nasi"
    # JANTUNG
    gold_h4=get_paxg("4h",200);gold_h1=get_paxg("1h",200);dxy=get_yf("DX-Y.NYB","20d","4h")
    if gold_h4.empty: return None,"Jantung kosong"
    ema50=gold_h4['Close'].ewm(50).mean().iloc[-1];ema200=gold_h4['Close'].ewm(200).mean().iloc[-1];price_h4=gold_h4['Close'].iloc[-1]
    dxy_ch=(dxy['Close'].iloc[-1]-dxy['Close'].iloc[-5])/dxy['Close'].iloc[-5] if not dxy.empty else 0
    jantung="BUY" if price_h4>ema50 and ema50>ema200 and dxy_ch<-0.005 else "SELL" if price_h4<ema50 and ema50<ema200 and dxy_ch>0.005 else "NEUTRAL"
    if jantung=="NEUTRAL": return None, f"JANTUNG NEUTRAL"
    # NADI+NGASAK
    m5=get_paxg("5m",300)
    pakaian_ok, pakaian_msg = cek_pakaian(m5)
    if not pakaian_ok: return None, pakaian_msg
    asia_h=m5['High'].tail(84).max();asia_l=m5['Low'].tail(84).min();d1=get_paxg("1d",10);ph=d1['High'].iloc[-2] if len(d1)>=2 else asia_h;pl=d1['Low'].iloc[-2] if len(d1)>=2 else asia_l
    last=m5.tail(25);now=m5['Close'].iloc[-1]
    def fvg(df,bull):
        for i in range(len(df)-3,len(df)-15,-1):
            c1=df.iloc[i-2];c3=df.iloc[i]
            if bull and c3['Low']>c1['High'] and c3['Low']-c1['High']>=0.8: return {"b":c1['High'],"t":c3['Low']}
            if not bull and c1['Low']>c3['High'] and c1['Low']-c3['High']>=0.8: return {"b":c3['High'],"t":c1['Low']}
        return None
    sig=None
    if jantung=="BUY":
        for lvl,name in [(asia_l,"Low Asia"),(pl,"Low Kemarin")]:
            if not last[last['Low']<lvl*(1-0.0002)].empty and now>lvl:
                f=find_fvg(m5,True)
                if f: entry=(f['t']+f['b'])/2;sl=f['b']-1.5;tp1=entry+(asia_h-entry)*0.5;tp2=ph;tp3=round((entry+(entry-sl)*3.5)/5)*5;sig={"type":"BUY","name":name,"lvl":lvl,"fvg":f,"entry":entry,"sl":sl,"tp1":tp1,"tp2":tp2,"tp3":tp3,"now":now,"ah":asia_h,"al":asia_l,"ph":ph,"pl":pl,"msg":pakaian_msg};break
    else:
        for lvl,name in [(asia_h,"High Asia"),(ph,"High Kemarin")]:
            if not last[last['High']>lvl*(1+0.0002)].empty and now<lvl:
                f=fvg(m5,False)
                if f: entry=(f['t']+f['b'])/2;sl=f['t']+1.5;tp1=entry-(entry-asia_l)*0.5;tp2=pl;tp3=round((entry-(sl-entry)*3.5)/5)*5;sig={"type":"SELL","name":name,"lvl":lvl,"fvg":f,"entry":entry,"sl":sl,"tp1":tp1,"tp2":tp2,"tp3":tp3,"now":now,"ah":asia_h,"al":asia_l,"ph":ph,"pl":pl,"msg":pakaian_msg};break
    if not sig: return None, f"NGASAK belum sweep searah JANTUNG {jantung}"
    return sig, f"MANUSIA HIDUP {jantung} {pakaian_msg} GERAK {sig['name']}"

def main():
    sig,reason=manusia_lengkap()
    print(reason)
    if not sig: return
    if os.path.exists(LAST):
        try:
            if abs(json.load(open(LAST))['b']-sig['fvg']['b'])<0.15: print("Anti pusing skip");return
        except: pass
    msg=f"""🧍 *MANUSIA EMAS LENGKAP HIDUP 100% - {sig['type']}*

🍚 Nasi kenyang 3 warung
💧 Air DXY OK
👕 {sig['msg']} + Helm BE + Jas hujan news
🏍️ Kendaraan GitHub 5/24 jalan
🏃 Gerakan {sig['name']} {sig['lvl']:.2f}

ENTRY {sig['entry']:.2f} SL {sig['sl']:.2f}
TP1 {sig['tp1']:.2f} TP2 {sig['tp2']:.2f} TP3 {sig['tp3']:.2f}
FVG {sig['fvg']['b']:.2f}-{sig['fvg']['t']:.2f}

Manusia kalo udah makan, pake baju, punya motor, ya harus gerak!"""
    print(msg);send(msg);json.dump({"b":sig['fvg']['b']},open(LAST,'w'))

if __name__=="__main__": main()
