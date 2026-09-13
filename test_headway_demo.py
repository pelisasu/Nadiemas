"""
TEST KONEKSI HEADWAY DEMO - Cek ID + Password
Fix IPC error -10003: install MT5 terminal dulu!
"""

import os
import sys
import time
import glob

def find_mt5_terminal():
    """Cari terminal64.exe Headway di Windows"""
    possible_paths = [
        r"C:\Program Files\Headway MetaTrader 5\terminal64.exe",
        r"C:\Program Files\MetaTrader 5\terminal64.exe",
        r"C:\Program Files\MetaTrader 5 Terminal\terminal64.exe",
        r"C:\Program Files (x86)\Headway MetaTrader 5\terminal64.exe",
        r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
    ]
    # Cari di AppData juga
    for p in possible_paths:
        if os.path.exists(p):
            return p
    # Cari via glob
    for base in [r"C:\Program Files", r"C:\Program Files (x86)"]:
        try:
            for exe in glob.glob(base + r"\**\terminal64.exe", recursive=True):
                if "headway" in exe.lower() or "metatrader" in exe.lower():
                    return exe
        except:
            pass
    return None

def test_headway_demo():
    try:
        import MetaTrader5 as mt5
    except ImportError as e:
        print(f"[ERROR] MetaTrader5 belum install: {e}")
        sys.exit(1)
    
    login = os.getenv("MT5_LOGIN")
    password = os.getenv("MT5_PASSWORD")
    server = os.getenv("MT5_SERVER") or "Headway-Demo"
    mt5_path = os.getenv("MT5_PATH") or find_mt5_terminal()
    
    if not login or not password:
        print(f"[ERROR] MT5_LOGIN / MT5_PASSWORD belum set di Secrets!")
        print(f"Set di: Settings -> Secrets -> MT5_LOGIN=4731137 MT5_PASSWORD=xxx MT5_SERVER=Headway-Demo")
        sys.exit(1)
    
    print(f"[INFO] Coba konek ke {server} login {login}...")
    print(f"[INFO] MT5 Terminal path: {mt5_path if mt5_path else 'auto detect'}")
    
    # Initialize dengan path explicit biar gak error -10003
    init_kwargs = {
        "login": int(login),
        "password": password,
        "server": server,
        "timeout": 30000
    }
    if mt5_path and os.path.exists(mt5_path):
        init_kwargs["path"] = mt5_path
        print(f"[INFO] Pakai terminal path: {mt5_path}")
    
    if not mt5.initialize(**init_kwargs):
        err = mt5.last_error()
        print(f"[ERROR] Gagal konek: {err}")
        print(f"")
        print(f"CEK:")
        print(f"1. MT5 terminal ke-install? Cek C:\Program Files\Headway MetaTrader 5\terminal64.exe")
        print(f"2. ID 4731137 benar? Balance $604.15 di screenshot")
        print(f"3. Server Headway-Demo? IP mt5.demo.trade-hw.online")
        print(f"4. Error -10003 = terminal64.exe tidak ketemu - install dulu!")
        # Coba initialize tanpa login (cek terminal aja)
        print(f"")
        print(f"[INFO] Coba initialize tanpa login (cek terminal)...")
        mt5.shutdown()
        time.sleep(2)
        if mt5.initialize(path=mt5_path) if mt5_path else mt5.initialize():
            print(f"[OK] Terminal MT5 OK, tapi login gagal - cek ID/password/server")
            ver = mt5.version()
            print(f"[INFO] MT5 version: {ver}")
            mt5.shutdown()
        else:
            print(f"[ERROR] Terminal MT5 tetap gagal: {mt5.last_error()}")
            print(f"[INFO] Download MT5 Headway: https://www.headway.global/")
        sys.exit(1)
    
    print(f"[OK] SUKSES KONEK KE HEADWAY {server}!")
    
    account = mt5.account_info()
    if account:
        print(f"[ACCOUNT] Login: {account.login} Balance: {account.balance} {account.currency} Leverage: 1:{account.leverage}")
        print(f"[ACCOUNT] Server: {account.server} Name: {account.name}")
    
    found = None
    for sym in ["GOLD", "XAUUSD", "GOLD.a", "XAUUSD.a", "GOLD.b"]:
        info = mt5.symbol_info(sym)
        if info:
            print(f"[OK] Symbol: {sym} Spread: {info.spread} Visible: {info.visible}")
            if not info.visible:
                mt5.symbol_select(sym, True)
            if not found:
                found = sym
        else:
            print(f"[INFO] Symbol tidak ada: {sym}")
    
    if found:
        tick = mt5.symbol_info_tick(found)
        if tick:
            print(f"[PRICE] {found} Ask: {tick.ask} Bid: {tick.bid} Time: {tick.time}")
        else:
            print(f"[WARN] {found} tick None - weekend tutup, Senin baru ada harga")
    
    mt5.shutdown()
    print(f"[OK] Test selesai - Koneksi Headway Demo 4731137 OK!")

if __name__ == "__main__":
    test_headway_demo()
