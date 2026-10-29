import time

def list_approach(rows, v4_base):
    allocated_v4 = []
    for row in rows:
        try: allocated_v4.append(int(row[0].split('.')[-1]))
        except: pass
    next_offset = v4_base
    while next_offset in allocated_v4:
        next_offset += 1
    return next_offset

def set_approach(rows, v4_base):
    allocated_v4 = set()
    for row in rows:
        try: allocated_v4.add(int(row[0].split('.')[-1]))
        except: pass
    next_offset = v4_base
    while next_offset in allocated_v4:
        next_offset += 1
    return next_offset

def run_benchmark():
    num_items = 10000
    v4_base = 10
    # Simulate DB rows with IP addresses where offsets 10 to 10000+ are allocated
    rows = [(f"10.0.0.{i}",) for i in range(v4_base, v4_base + num_items)]

    # Benchmark List Approach
    start_time = time.perf_counter()
    res_list = list_approach(rows, v4_base)
    list_duration = time.perf_counter() - start_time

    # Benchmark Set Approach
    start_time = time.perf_counter()
    res_set = set_approach(rows, v4_base)
    set_duration = time.perf_counter() - start_time

    print(f"Num Allocated IPs: {num_items}")
    print(f"List approach result: {res_list}, time taken: {list_duration:.6f} seconds")
    print(f"Set approach result: {res_set}, time taken: {set_duration:.6f} seconds")
    if set_duration > 0:
        print(f"Speedup: {list_duration / set_duration:.2f}x")

if __name__ == "__main__":
    run_benchmark()
