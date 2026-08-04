import urllib.request
import urllib.error
import json
import time
import concurrent.futures

API_URL = "http://localhost:8000/api/v1/compounds/autocomplete?q=ace&limit=5"
CONCURRENT_REQUESTS = 50

def fetch_url(url: str):
    start_time = time.time()
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = response.read()
            process_time = response.headers.get("X-Process-Time", "N/A")
            cache_control = response.headers.get("Cache-Control", "N/A")
            duration = (time.time() - start_time) * 1000
            return True, duration, process_time, cache_control
    except urllib.error.URLError as e:
        duration = (time.time() - start_time) * 1000
        return False, duration, "N/A", "N/A"

def main():
    print(f"Menguji endpoint: {API_URL}")
    print(f"Jumlah request bersamaan: {CONCURRENT_REQUESTS}")
    
    # Pemanasan / Cache Miss Test (Request pertama)
    print("\n--- TEST CACHE MISS ---")
    success, dur, ptime, cache_ctrl = fetch_url(API_URL)
    print(f"Status: {'Success' if success else 'Failed'}, Total Latency: {dur:.2f} ms, X-Process-Time: {ptime} ms, Cache-Control: {cache_ctrl}")
    
    # Cache Hit Test (Request kedua)
    print("\n--- TEST CACHE HIT (SINGLE) ---")
    success, dur, ptime, cache_ctrl = fetch_url(API_URL)
    print(f"Status: {'Success' if success else 'Failed'}, Total Latency: {dur:.2f} ms, X-Process-Time: {ptime} ms, Cache-Control: {cache_ctrl}")
    
    # Concurrent Test (Thundering Herd test)
    print(f"\n--- TEST CONCURRENT ({CONCURRENT_REQUESTS} requests) ---")
    results = []
    start_all = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        futures = [executor.submit(fetch_url, API_URL) for _ in range(CONCURRENT_REQUESTS)]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    end_all = time.time()
    successes = [r for r in results if r[0]]
    durations = [r[1] for r in successes]
    
    if successes:
        avg_dur = sum(durations) / len(successes)
        max_dur = max(durations)
        print(f"Total waktu eksekusi batch: {(end_all - start_all) * 1000:.2f} ms")
        print(f"Berhasil: {len(successes)}/{CONCURRENT_REQUESTS}")
        print(f"Rata-rata latensi: {avg_dur:.2f} ms")
        print(f"Latensi maksimal: {max_dur:.2f} ms")
        print("Sampel X-Process-Time:", [r[2] for r in successes[:5]])
    else:
        print("Semua request gagal.")

if __name__ == "__main__":
    main()
