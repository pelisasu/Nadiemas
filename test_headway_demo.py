"""
TEST KONEKSI HEADWAY DEMO - Cek ID + Password benar gak
Jalankan di GitHub Actions windows-latest
"""

import os
import sys

def test_headway_demo():
    try:
        import MetaTrader5 as mt5
    except ImportError as e:
        print(f"❌ Module MetaTrader5 belum install: {e}")
        print(f"💡 pip install MetaTrader5")
        sys.exit(1)
    
    login = os.getenv("MT5_LOGIN")
    password = os.getenv("MT5_PASSWORD")
    server = os.getenv("MT5_SERVER") or "Headway-Demo"
    
    # VALIDASI SECRETS - jangan pakai input() di GitHub Actions!
    if not login or not password:
        print(f"❌ MT5_LOGIN atau MT5_PASSWORD belum di set di GitHub Secrets!")
        print(f"")
        print(f"🔧 CARA FIX:")
        print(f"1. GitHub repo → Settings → Secrets and variables → Actions")
        print(f"2. New secret:")
        print(f"   MT5_LOGIN = 4731137 (ID demo lu)")
        print(f"   MT5_PASSWORD = password MT5 lu")
        print(f"   MT5_SERVER = Headway-Demo")
        print(f"   MT5_SYMBOL = GOLD")
        print(f"   AUTO_TRADE_ENABLED = true")
        print(f"")
        print(f"Login yang terdeteksi: login={login} server={server} password={'SET' if password else 'BELUM SET'}")
        sys.exit(1)
    
    print(f"🔌 Coba konek ke {server} login {login}...")
    print(f"📊 Balance akun lu di screenshot: $604.15 STANDARD MT5")
    
    # Initialize dengan timeout
    if not mt5.initialize(login=int(login), password=password, server=server, timeout=15000):
        err = mt5.last_error()
        print(f"❌ Gagal konek: {err}")
        print(f"")
        print(f"💡 CEK:")
        print(f"1. ID benar? Lu punya 4731137")
        print(f"2. Password benar? Cek di Headway app")
        print(f"3. Server benar? Headway-Demo (bukan Headway-Real untuk demo)")
        print(f"4. IP Server: mt5.demo.trade-hw.online")
        mt5.shutdown()
        sys.exit(1)
    
    print(f"✅ SUKSES KONEK KE HEADWAY {server}!")
    
    account = mt5.account_info()
    if account:
        print(f"👤 Akun: {account.login} | Balance: {account.balance} {account.currency} | Leverage: 1:{account.leverage}")
        print(f"📊 Server: {account.server}")
    
    # Cek symbol GOLD (Headway pakai GOLD bukan XAUUSD)
    found_symbol = None
    for sym in ["GOLD", "XAUUSD", "GOLD.a", "XAUUSD.a", "GOLD.b", "XAUUSD.b"]:
        info = mt5.symbol_info(sym)
        if info:
            print(f"✅ Symbol ketemu: {sym} - Spread: {info.spread} points - Visible: {info.visible}")
            if not info.visible:
                mt5.symbol_select(sym, True)
                print(f"   → Diaktifkan: {sym}")
            if not found_symbol:
                found_symbol = sym
        else:
            print(f"   Symbol gak ada: {sym}")
    
    if not found_symbol:
        print(f"❌ GOLD/XAUUSD gak ketemu di {server} - cek Market Watch Headway")
    else:
        tick = mt5.symbol_info_tick(found_symbol)
        if tick:
            print(f"💰 {found_symbol} Ask: {tick.ask} Bid: {tick.bid}")
            print(f"📅 Time: {tick.time}")
        else:
            print(f"⚠️ {found_symbol} tick None (wajar weekend market tutup, Senin baru ada harga)")
    
    mt5.shutdown()
    print(f"")
    print(f"✅ Test selesai - Koneksi Headway Demo OK!")
    print(f"💡 Next: Senin 05:00 WIB market buka, bot auto OP demo 0.01 lot!")

if __name__ == "__main__":
    test_headway_demo()
