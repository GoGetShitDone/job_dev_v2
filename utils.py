import threading
import time
import schedule
from cachetools import TTLCache
from functools import wraps

scrape_ttl_cache = TTLCache(maxsize=256, ttl=60 * 60 * 6)


def cached(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in scrape_ttl_cache:
            result = func(*args, **kwargs)
            scrape_ttl_cache[key] = result
        return scrape_ttl_cache[key]
    return wrapper


def clear_ttl_cache():
    print("start cache clear...")
    scrape_ttl_cache.clear()
    print("done cache clear!")


def run_clear_cache_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)


def init_cache():
    schedule.every(6).hours.do(clear_ttl_cache)
    scheduler_thread = threading.Thread(target=run_clear_cache_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
