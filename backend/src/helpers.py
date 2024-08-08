import time
import requests
from functools import wraps

def retry(num_retries=3, delay=2, backoff_factor=2):
    def decorator_retry(func):
        @wraps(func)
        def wrapper_retry(*args, **kwargs):
            retries = 0
            current_delay = delay
            while retries < num_retries:
                try:
                    response = func(*args, **kwargs)
                    if response.status_code == 200:
                        return response
                    else:
                        print(f"Request failed with status code {response.status_code}. Retrying...")
                except requests.RequestException as e:
                    print(f"Request failed due to {e}. Retrying...")
                time.sleep(current_delay)
                retries += 1
                current_delay *= backoff_factor
            return func(*args, **kwargs)
        return wrapper_retry
    return decorator_retry
