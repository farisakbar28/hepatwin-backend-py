import sys
import os
import time

# Ensure the root path is in PYTHONPATH so we can import 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal, engine
from app.repositories.compound_repository import CompoundRepository
from sqlalchemy import text

def test_connection_and_pooler():
    print("=== Menguji Koneksi ke Supabase Transaction Pooler ===")
    try:
        # 1. Uji koneksi dasar dan pooler
        with engine.connect() as conn:
            # Jika ini gagal karena prepared statement di PgBouncer, 
            # akan terjadi exception 'PREPARE is not supported' atau OperationalError.
            result = conn.execute(text("SELECT 1")).scalar()
            assert result == 1, "Hasil SELECT 1 tidak valid"
            print("[OK] Koneksi Pooler berhasil. (Tidak ada error PREPARE)")
    except Exception as e:
        print(f"[ERROR] Gagal terhubung ke Pooler: {e}")
        sys.exit(1)

def test_count_simulatable():
    print("\n=== Menguji Kueri COUNT simulatable ===")
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT count(*) FROM public.hepatwin_compounds WHERE is_simulatable = true;")).scalar()
        print(f"[OK] Kueri count berhasil dijalankan. Jumlah senyawa simulatable: {result}")
    except Exception as e:
        print(f"[ERROR] Kueri count gagal: {e}")
        sys.exit(1)
    finally:
        db.close()

def test_autocomplete_performance():
    print("\n=== Menguji Performa dan Resiliensi Autocomplete ===")
    db = SessionLocal()
    repo = CompoundRepository(db)
    
    queries = ["aa", "pi", "piso", "as"]
    
    try:
        for q in queries:
            start_time = time.perf_counter()
            results = repo.search_by_name(query=q, limit=10)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            # Print latensi dan jumlah kembalian
            status = "OK" if elapsed_ms < 500 else "WARNING (>500ms)"
            # Target NFR < 50ms untuk pencarian cache, tapi query pertama mungkin lebih lambat.
            # Kita cuma menyorot jika sangat cepat.
            if elapsed_ms < 50:
                status = "EXCELLENT (<50ms)"
            
            print(f"Kueri '{q}': Ditemukan {len(results)} hasil dalam {elapsed_ms:.2f} ms [{status}]")
    except Exception as e:
        print(f"[ERROR] Autocomplete gagal pada kueri: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    test_connection_and_pooler()
    test_count_simulatable()
    test_autocomplete_performance()
    print("\n[SUCCESS] Semua skenario uji Transaction Pooler & Cache lolos dengan baik!")
