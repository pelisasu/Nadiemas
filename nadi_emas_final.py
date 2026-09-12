# NADI EMAS FINAL - BEST SETUP
import os, json, random, time, requests, pandas as pd
from datetime import datetime
import pytz
CONFIG={"MT5_OFFSET":-2.25,"MIN_FVG":0.8,"SL_BUF":1.5,"SWEEP_PCT":0.0002,"KILLZONE_UTC":(7,16),"VIX_MAX":28}
LAST_FILE=".last_signal.json"
def get_paxg(limit=300,interval="5m"):
 try:
  r=requests.get("https://api.binance.com/api/v3/klines",params={"symbol":"PAXGUSDT","interval":interval,"limit":limit},headers={"User-Agent":f"Mozilla/5.0 {random.randint(1,99)}"},timeout=8).json()
  if isinstance(r,dict): raise Exception("blocked")
  df=pd.DataFrame(r,columns=["ot","Open","High","Low","Close","Vol","c","d","e","f","g","h"])
  for c in ["Open","High","Low","Close"]: df[c]=df[c].astype(float)+CONFIG["MT5_OFFSET"]
  df["Time"]=pd.to_datetime(df["ot"],unit='ms',utc=True)
  return df.set_index("Time")
 except:
  r=requests.get("https://api.coingecko.com/api/v3/coins/pax-gold/market_chart?vs_currency=usd&days=2&interval=5m",timeout=10).json()
  df=pd.DataFrame(r['prices'],columns=['ot','Close'])
  df['Time']=pd.to_datetime(df['ot'],unit='ms',utc=True)
  df=df.set_index('Time')
  df['High']=df['Close']*1.0005+CONFIG["MT5_OFFSET"];df['Low']=df['Close']*0.9995+CONFIG["MT5_OFFSET"];df['Open']=df['Close'].shift(1).fillna(df['Close'])+CONFIG["MT5_OFFSET"];df['Close']+=CONFIG["MT5_OFFSET"]
  return df.tail(300)
def get_yf(sym,period="5d",interval="60m"):
 try:
  import yfinance as yf;time.sleep(0.8)
  df=yf.download(sym,period=period,interval=interval,progress=False,auto_adjust=True)
  if hasattr(df.columns,'get_level_values'):
   try: df.columns=df.columns.get_level_values(0)
   except: pass
  return df.dropna()
 except: return pd.DataFrame()
def in_killzone():
 h=datetime.now(pytz.UTC).hour;return CONFIG["KILLZONE_UTC"][0]<=h<=CONFIG["KILLZONE_UTC"][1]
def check_filters():
 if not in_killzone(): return {"ok":False,"reason":f"Outside Killzone {CONFIG['KILLZONE_UTC']} UTC"}
 vix=get_yf("^VIX",period="5d",interval="60m")
 if not vix.empty and vix['Close'].iloc[-1]>CONFIG["VIX_MAX"]: return {"ok":False,"reason":f"VIX {vix['Close'].iloc[-1]:.1f} panic"}
 dxy=get_yf("DX-Y.NYB",period="5d",interval="4h");gold=get_paxg(limit=200,interval="1h")
 if dxy.empty or gold.empty: return {"ok":False,"reason":"Data kosong"}
 ch=(dxy['Close'].iloc[-1]-dxy['Close'].iloc[-3])/dxy['Close'].iloc[-3];ema=gold['Close'].ewm(span=20).mean().iloc[-1];price=gold['Close'].iloc[-1]
 if ch<-0.002 and price>ema: return {"ok":True,"side":"BUY","reason":f"DXY {ch*100:.2f}% >EMA Killzone OK"}
 elif ch>0.002 and price<ema: return {"ok":True,"side":"SELL","reason":f"DXY {ch*100:.2f}% <EMA Killzone OK"}
 else: return {"ok":False,"reason":f"DXY {ch*100:.2f}% belum sinkron"}
def find_fvg(df,bull=True):
 for i in range(len(df)-3,len(df)-15,-1):
  c1=df.iloc[i-2];c3=df.iloc[i]
  if bull:
   if c3['Low']>c1['High'] and (c3['Low']-c1['High'])>=CONFIG["MIN_FVG"]: return {"b":c1['High'],"t":c3['Low'],"size":c3['Low']-c1['High']}
  else:
   if c1['Low']>c3['High'] and (c1['Low']-c3['High'])>=CONFIG["MIN_FVG"]: return {"b":c3['High'],"t":c1['Low'],"size":c1['Low']-c3['High']}
 return None
def detect():
 m5=get_paxg(limit=300,interval="5m")
 if len(m5)<60: return None
 asia_h=m5['High'].tail(84).max();asia_l=m5['Low'].tail(84).min()
 d1=get_paxg(limit=10,interval="1d");ph=d1['High'].iloc[-2] if len(d1)>=2 else asia_h;pl=d1['Low'].iloc[-2] if len(d1)>=2 else asia_l
 last=m5.tail(25);now=m5['Close'].iloc[-1]
 for lvl,name in [(asia_l,"Low Asia"),(pl,"Low Kemarin")]:
  if not last[last['Low']<lvl*(1-CONFIG["SWEEP_PCT"])].empty and now>lvl:
   fvg=find_fvg(m5,True)
   if fvg: entry=(fvg['t']+fvg['b'])/2;sl=fvg['b']-1.5;risk=entry-sl;tp1=entry+(asia_h-entry)*0.5;tp2=ph;tp3=round((entry+risk*3.5)/5)*5;return {"type":"BUY","name":name,"lvl":lvl,"fvg":fvg,"entry":entry,"sl":sl,"tp1":tp1,"tp2":tp2,"tp3":tp3,"now":now,"ah":asia_h,"al":asia_l,"ph":ph,"pl":pl}
 for lvl,name in [(asia_h,"High Asia"),(ph,"High Kemarin")]:
  if not last[last['High']>lvl*(1+CONFIG["SWEEP_PCT"])].empty and now<lvl:
   fvg=find_fvg(m5,False)
   if fvg: entry=(fvg['t']+fvg['b'])/2;sl=fvg['t']+1.5;risk=sl-entry;tp1=entry-(entry-asia_l)*0.5;tp2=pl;tp3=round((entry-risk*3.5)/5)*5;return {"type":"SELL","name":name,"lvl":lvl,"fvg":fvg,"entry":entry,"sl":sl,"tp1":tp1,"tp2":tp2,"tp3":tp3,"now":now,"ah":asia_h,"al":asia_l,"ph":ph,"pl":pl}
 return None
def is_new(fvg):
 import os,json
 if not os.path.exists(LAST_FILE): return True
 try:
  with open(LAST_FILE) as f:last=json.load(f)
  return abs(last['b']-fvg['b'])>0.15
 except: return True
def save(fvg):
 import json;json.dump({"b":fvg['b'],"t":fvg['t']},open(LAST_FILE,'w'))
def send(msg):
 import os,requests;token=os.getenv("TELEGRAM_TOKEN");chat=os.getenv("TELEGRAM_CHAT_ID")
 if not token or not chat: print(msg);return
 try: requests.post(f"https://api.telegram.org/bot{token}/sendMessage",json={"chat_id":chat,"text":msg,"parse_mode":"Markdown"},timeout=10)
 except: pass
def main():
 filt=check_filters()
 if not filt.get("ok"): print(filt['reason']);return
 sig=detect()
 if not sig: print("No signal");return
 if sig['type']!=filt['side']: print("Beda arah");return
 if not is_new(sig['fvg']): print("Spam skip");return
 msg=f"""🔥 *NADI EMAS FINAL - {sig['type']}*
Presisi MT5 {CONFIG['MT5_OFFSET']} | {filt['reason']}
NGASAK {sig['name']} {sig['lvl']:.2f}->{sig['now']:.2f}
FVG {sig['fvg']['b']:.2f}-{sig['fvg']['t']:.2f}
ENTRY {sig['entry']:.2f} | SL {sig['sl']:.2f}
TP1 {sig['tp1']:.2f} | TP2 {sig['tp2']:.2f} | TP3 {sig['tp3']:.2f}
OP MANUAL TP1 50% BE TP2 70% TP3 runner"""
 print(msg);send(msg);save(sig['fvg'])
if __name__=="__main__": main()
