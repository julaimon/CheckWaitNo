import requests

def get_current_data(url: str) -> str:
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.text.strip()
    except Exception as e:
        print(f"Error fetching data from {url}: {e}")
        return ""
