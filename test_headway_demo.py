"""
TEST KONEKSI HEADWAY DEMO - Cek ID + Password benar gak
Windows runner cp1252 safe - no emoji
"""

import os
import sys

def test_headway_demo():
    try:
        import MetaTrader5 as mt5
    except ImportError as e:
        print(f"[ERROR] Module MetaTrader5 belum install: {e}")
        print(f"pip install MetaTrader5")
        sys.exit(1)
    
    login = os.getenv("MT5_LOGIN")
    password = os.getenv("MT5_PASSWORD")
    server = os.getenv("MT5_SERVER") or "Headway-Demo"
    
    if not login or not password:
        print(f"[ERROR] MT5_LOGIN atau MT5_PASSWORD belum di set di GitHub Secrets!")
        print(f"")
        print(f"CARA FIX:")
        print(f"1. GitHub repo -> Settings -> Secrets and variables -> Actions")
        print(f"2. New secret:")
        print(f"   MT5_LOGIN = 4731137")
        print(f"   MT5_PASSWORD = password MT5 lu")
        print(f"   MT5_SERVER = Headway-Demo")
        print(f"   MT5_SYMBOL = GOLD")
        print(f"")
        print(f"Login terdeteksi: login={login} server={server} password={'SET' if password else 'BELUM SET'}")
        sys.exit(1)
    
    print(f"[INFO] Coba konek ke {server} login {login}...")
    print(f"[INFO] Balance di screenshot: $604.15 STANDARD MT5")
    
    if not mt5.initialize(login=int(login), password=password, server=server, timeout=15000):
        err = mt5.last_error()
        print(f"[ERROR] Gagal konek: {err}")
        print(f"")
        print(f"CEK:")
        print(f"1. ID benar? 4731137")
        print(f"2. Password benar? Cek di Headway app")
        print(f"3. Server benar? Headway-Demo (bukan Real)")
        print(f"4. IP: mt5.demo.trade-hw.online")
        mt5.shutdown()
        sys.exit(1)
    
    print(f"[OK] SUKSES KONEK KE HEADWAY {server}!")
    
    account = mt5.account_info()
    if account:
        print(f"[ACCOUNT] Akun: {account.login} | Balance: {account.balance} {account.currency} | Leverage: 1:{account.leverage}")
        print(f"[ACCOUNT] Server: {account.server}")
    
    found_symbol = None
    for sym in ["GOLD", "XAUUSD", "GOLD.a", "XAUUSD.a", "GOLD.b", "XAUUSD.b"]:
        info = mt5.symbol_info(sym)
        if info:
            print(f"[OK] Symbol ketemu: {sym} - Spread: {info.spread} points - Visible: {info.visible}")
            if not info.visible:
                mt5.symbol_select(sym, True)
                print(f"     -> Diaktifkan: {sym}")
            if not found_symbol:
                found_symbol = sym
        else:
            print(f"[INFO] Symbol gak ada: {sym}")
    
    if not found_symbol:
        print(f"[ERROR] GOLD/XAUUSD gak ketemu di {server}")
    else:
        tick = mt5.symbol_info_tick(found_symbol)
        if tick:
            print(f"[PRICE] {found_symbol} Ask: {tick.ask} Bid: {tick.bid}")
        else:
            print(f"[WARN] {found_symbol} tick None (wajar weekend market tutup, Senin baru ada harga)")
    
    mt5.shutdown()
    print(f"")
    print(f"[OK] Test selesai - Koneksi Headway Demo OK! Siap auto trade Senin!")

if __name__ == "__main__":
    test_headway_demo()
