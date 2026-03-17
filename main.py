import gc
import time
import psutil
import os

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def cleanup_memory():
    gc.collect()
    
def memory_monitor():
    while True:
        mem = get_memory_usage()
        if mem > 400:
            gc.collect()
        time.sleep(60)

def main():
    print("FB Comment Tool - Memory Optimized")
    print(f"Current Memory: {get_memory_usage():.1f} MB")

if __name__ == "__main__":
    main()
