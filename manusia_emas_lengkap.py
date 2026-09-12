"""
MANUSIA EMAS LENGKAP - FINAL FIX ANTI KeyError
Offset bener lu: -2.25 (MT5 4347.45 - Gold-API 4349.70)
4 Warung, kalo tutup semua gak crash, cuma puasa
"""
import os,json,random,time,requests,pandas as pd
from datetime import datetime
import pytz

CONFIG={"OFFSET":-2.25,"MIN_FVG":0.8,"SWEEP":0.0002,"KILLZONE":(7,16),"MAX_SPREAD":8.0}
LAST=".last_manusia.json"

def get_paxg(interval="5m",limit=300):
    # WARUNG 1: Binance
    try:
        m={"5m":"5m","15m":"15m","60m":"1h","1h":"1h","4h":"4h","1d":"1d"}.get(interval,"5m")
        url="https://api.binance.com/api/v3/klines"
        r=requests.get(url,params={"symbol":"PAXGUSDT","interval":m,"limit":limit},headers={"User-Agent":f"Mozilla/5.0 Chrome/{random.randint(100,999)}"},timeout=12)
        j=r.json()
        if isinstance(j, list) and len(j)>20:
            df=pd.DataFrame(j,columns=["ot","Open","High","Low","Close","Vol","c","d","e","f","g","h"])
            for c in ["Open","High","Low","Close"]:
                df[c]=pd.to_numeric(df[c],errors='coerce')+CONFIG["OFFSET"]
            df["Time"]=pd.to_datetime(df["ot"],unit='ms',utc=True)
            print("🍚 Binance OK")
            return df.set_index("Time").dropna()
    except Exception as e:
        print(f"Binance tutup: {e}")

    # WARUNG 2: Gold-API spot murni (paling plek MT5 lu)
    try:
        r=requests.get("https://api.gold-api.com/price/XAU",timeout=10).json()
        if isinstance(r, dict) and "price" in r and r["price"]:
            p=float(r["price"])+CONFIG["OFFSET"]
            print(f"🍚 Gold-API OK {p:.2f}")
            now=int(time.time()*1000)
            df=pd.DataFrame([{"ot":now-i*300000,"Open":p,"High":p+1,"Low":p-1,"Close":p} for i in range(limit)])
            df["Time"]=pd.to_datetime(df["ot"],unit='ms',utc=True)
            return df.set_index("Time")
    except Exception as e:
        print(f"Gold-API tutup: {e}")

    # WARUNG 3: CoinGecko - ANTI KeyError FIX
    try:
        days="2" if interval=="5m" else "10"
        r=requests.get(f"https://api.coingecko.com/api/v3/coins/pax-gold/market_chart",params={"vs_currency":"usd","days":days},timeout=12).json()
        if isinstance(r, dict) and "prices" in r and len(r["prices"])>10:
            df=pd.DataFrame(r['prices'],columns=['ot','Close'])
            df['Time']=pd.to_datetime(df['ot'],unit='ms',utc=True)
            df=df.set_index('Time')
            df['Close']=pd.to_numeric(df['Close'],errors='coerce')+CONFIG["OFFSET"]
            df['High']=df['Close']+1
            df['Low']=df['Close']-1
            df['Open']=df['Close'].shift(1).fillna(df['Close'])
            print("🍚 CoinGecko OK")
            return df.tail(limit).dropna()
        else:
            print(f"CoinGecko gak ada prices: {str(r)[:200]}")
    except Exception as e:
        print(f"CoinGecko tutup: {e}")

    # WARUNG 4: Yahoo PAXG-USD (paling kebal blokir GitHub)
    try:
        import yfinance as yf
        # yfinance kadang rate-limit, sleep dulu
        time.sleep(1)
        per="5d" if interval in ["5m","15m","1h"] else "20d"
        iv="5m" if interval=="5m" else "60m" if interval=="1h" else "1d" if interval=="1d" else "60m"
        df=yf.download("PAXG-USD",period=per,interval=iv,progress=False,auto_adjust=True)
        if not df.empty and len(df)>10:
            if hasattr(df.columns,'get_level_values'):
                try: df.columns=df.columns.get_level_values(0)
                except: pass
            for c in ["Open","High","Low","Close"]:
                if c in df.columns:
                    df[c]=pd.to_numeric(df[c],errors='coerce')+CONFIG["OFFSET"]
            df.index=pd.to_datetime(df.index,utc=True)
            print("🍚 Yahoo PAXG-USD OK")
            return df.tail(limit).dropna()
    except Exception as e:
        print(f"Yahoo tutup: {e}")

    print("💀 Semua warung tutup - puasa, gak crash")
    return pd.DataFrame()

def get_yf(sym,period="5d",interval="60m"):
    try:
        import yfinance as yf
        time.sleep(1)
        df=yf.download(sym,period=period,interval=interval,progress=False,auto_adjust=True)
        if hasattr(df.columns,'get_level_values'):
            try: df.columns=df.columns.get_level_values(0)
            except: pass
        return df.dropna()
    except:
        return pd.DataFrame()

def cek_pakaian(m5):
    if m5.empty or len(m5)<5:
        return True,"Pakaian skip data kurang"
    try:
        spread=float(m5['High'].iloc[-1]-m5['Low'].iloc[-1])
        if spread>CONFIG["MAX_SPREAD"]:
            return False,f"👕 Spread {spread:.1f} brutal > {CONFIG['MAX_SPREAD']}"
        return True,f"👕 OK spread {spread:.1f}"
    except:
        return True,"Pakaian skip"

def send(msg):
    token=os.getenv("TELEGRAM_TOKEN")
    chat=os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("Telegram secret kosong - print aja")
        print(msg)
        return
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",json={"chat_id":chat,"text":msg,"parse_mode":"Markdown"},timeout=10)
    except Exception as e:
        print(f"Telegram gagal: {e}")

def manusia_lengkap():
    # Cek nutrisi dulu biar gak crash
    gold_h4=get_paxg("4h",200)
    gold_h1=get_paxg("1h",200)
    if gold_h4.empty or gold_h1.empty:
        return None,"💀 Nasi abis semua warung tutup - bot puasa (bukan error, nanti coba lagi 20 menit)"

    dxy=get_yf("DX-Y.NYB","20d","4h")
    try:
        ema50=gold_h4['Close'].ewm(50).mean().iloc[-1]
        ema200=gold_h4['Close'].ewm(200).mean().iloc[-1]
        price_h4=float(gold_h4['Close'].iloc[-1])
    except:
        return None,"Jantung data error - puasa"

    dxy_ch=0
    if not dxy.empty and len(dxy)>=6:
        try:
            dxy_ch=(float(dxy['Close'].iloc[-1])-float(dxy['Close'].iloc[-5]))/float(dxy['Close'].iloc[-5])
        except:
            dxy_ch=0

    jantung="NEUTRAL"
    if price_h4>ema50 and ema50>ema200 and dxy_ch<-0.005:
        jantung="BUY"
    elif price_h4<ema50 and ema50<ema200 and dxy_ch>0.005:
        jantung="SELL"
    else:
        return None,f"JANTUNG NEUTRAL H4 {price_h4:.1f} EMA50 {ema50:.1f} DXY {dxy_ch*100:.2f}% - nunggu arah"

    m5=get_paxg("5m",300)
    if m5.empty or len(m5)<60:
        return None,"M5 kosong - puasa"

    ok,msg_pak=cek_pakaian(m5)
    if not ok:
        return None,msg_pak

    try:
        asia_h=float(m5['High'].tail(84).max())
        asia_l=float(m5['Low'].tail(84).min())
        d1=get_paxg("1d",10)
        if not d1.empty and len(d1)>=2:
            ph=float(d1['High'].iloc[-2]); pl=float(d1['Low'].iloc[-2])
        else:
            ph=asia_h; pl=asia_l
        last=m5.tail(25)
        now=float(m5['Close'].iloc[-1])
    except Exception as e:
        return None,f"Hitung Asia error: {e}"

    def fvg(df,bull):
        for i in range(len(df)-3,len(df)-15,-1):
            try:
                c1=df.iloc[i-2]; c3=df.iloc[i]
                if bull and float(c3['Low'])>float(c1['High']) and float(c3['Low'])-float(c1['High'])>=CONFIG["MIN_FVG"]:
                    return {"b":float(c1['High']),"t":float(c3['Low'])}
                if not bull and float(c1['Low'])>float(c3['High']) and float(c1['Low'])-float(c3['High'])>=CONFIG["MIN_FVG"]:
                    return {"b":float(c3['High']),"t":float(c1['Low'])}
            except:
                continue
        return None

    sig=None
    if jantung=="BUY":
        for lvl,name in [(asia_l,"Low Asia"),(pl,"Low Kemarin")]:
            try:
                if not last[last['Low']<lvl*(1-CONFIG["SWEEP"])].empty and now>lvl:
                    f=fvg(m5,True)
                    if f:
                        entry=(f['t']+f['b'])/2; sl=f['b']-1.5; tp1=entry+(asia_h-entry)*0.5; tp2=ph; tp3=round((entry+(entry-sl)*3.5)/5)*5
                        sig={"type":"BUY","name":name,"lvl":lvl,"fvg":f,"entry":entry,"sl":sl,"tp1":tp1,"tp2":tp2,"tp3":tp3,"now":now,"ah":asia_h,"al":asia_l,"ph":ph,"pl":pl,"msg":msg_pak}
                        break
            except: continue
    else:
        for lvl,name in [(asia_h,"High Asia"),(ph,"High Kemarin")]:
            try:
                if not last[last['High']>lvl*(1+CONFIG["SWEEP"])].empty and now<lvl:
                    f=fvg(m5,False)
                    if f:
                        entry=(f['t']+f['b'])/2; sl=f['t']+1.5; tp1=entry-(entry-asia_l)*0.5; tp2=pl; tp3=round((entry-(sl-entry)*3.5)/5)*5
                        sig={"type":"SELL","name":name,"lvl":lvl,"fvg":f,"entry":entry,"sl":sl,"tp1":tp1,"tp2":tp2,"tp3":tp3,"now":now,"ah":asia_h,"al":asia_l,"ph":ph,"pl":pl,"msg":msg_pak}
                        break
            except: continue

    if not sig:
        return None,f"NGASAK belum sweep searah {jantung} - nunggu"
    return sig,f"MANUSIA HIDUP {jantung} {msg_pak}"

def main():
    print(f"=== MANUSIA LENGKAP FINAL FIX {datetime.now()} ===")
    sig,reason=manusia_lengkap()
    print(reason)
    if not sig:
        # gak crash, cuma print puasa = succeeded ijo
        return
    if os.path.exists(LAST):
        try:
            last=json.load(open(LAST))
            if abs(last['b']-sig['fvg']['b'])<0.15 and last['type']==sig['type']:
                print("Anti pusing skip sinyal sama")
                return
        except:
            pass

    msg=f"""🧍 *MANUSIA {sig['type']}* {sig['name']} {sig['lvl']:.2f}
{reason}
ENTRY {sig['entry']:.2f} SL {sig['sl']:.2f}
TP1 {sig['tp1']:.2f} TP2 {sig['tp2']:.2f} TP3 {sig['tp3']:.2f}
FVG {sig['fvg']['b']:.2f}-{sig['fvg']['t']:.2f}
Offset {CONFIG['OFFSET']} MT5 plek 4347.45"""
    print(msg)
    send(msg)
    try:
        json.dump({"b":sig['fvg']['b'],"type":sig['type']},open(LAST,'w'))
    except:
        pass

if __name__=="__main__":
    main()
