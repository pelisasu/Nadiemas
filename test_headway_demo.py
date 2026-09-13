"""
TEST KONEKSI HEADWAY DEMO - Cek ID + Password benar gak
Jalankan di GitHub Actions windows-latest atau di laptop Windows
"""

import os

def test_headway_demo():
    try:
        import MetaTrader5 as mt5
    except:
        print("❌ Module MetaTrader5 belum install - pip install MetaTrader5")
        return
    
    # AMBIL DARI SECRETS ATAU ISI MANUAL BUAT TEST LOKAL
    login = os.getenv("MT5_LOGIN") or input("Masukin MT5 LOGIN Demo: ")
    password = os.getenv("MT5_PASSWORD") or input("Masukin MT5 PASSWORD Demo: ")
    server = os.getenv("MT5_SERVER") or "Headway-Demo"
    
    print(f"🔌 Coba konek ke {server} login {login}...")
    
    if not mt5.initialize(login=int(login), password=password, server=server):
        print(f"❌ Gagal konek: {mt5.last_error()}")
        print(f"💡 Cek: 1. ID benar? 2. Password benar? 3. Server Headway-Demo / Headway-Real?")
        mt5.shutdown()
        return
    
    print(f"✅ SUKSES KONEK KE HEADWAY {server}!")
    
    account = mt5.account_info()
    if account:
        print(f"👤 Akun: {account.login} | Balance: {account.balance} {account.currency}")
        print(f"📊 Server: {account.server} | Leverage: 1:{account.leverage}")
    
    # Cek symbol GOLD
    for sym in ["GOLD", "XAUUSD", "GOLD.a", "XAUUSD.a"]:
        info = mt5.symbol_info(sym)
        if info:
            print(f"✅ Symbol ketemu: {sym} - Spread: {info.spread} - Visible: {info.visible}")
            if not info.visible:
                mt5.symbol_select(sym, True)
                print(f"   → Diaktifkan: {sym}")
        else:
            print(f"❌ Symbol gak ada: {sym}")
    
    # Cek harga sekarang (weekend market tutup, harga freeze)
    tick = mt5.symbol_info_tick("GOLD")
    if tick:
        print(f"💰 GOLD Ask: {tick.ask} Bid: {tick.bid} - Time: {tick.time}")
    else:
        print(f"⚠️ GOLD tick None (wajar weekend market tutup)")
    
    mt5.shutdown()
    print(f"✅ Test selesai - Koneksi Headway Demo OK! Siap auto trade Senin!")

if __name__ == "__main__":
    test_headway_demo()
