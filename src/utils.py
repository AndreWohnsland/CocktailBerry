import http.client as httplib


def has_connection() -> bool:
    """Checks if can connect to internet (google) and returns success"""
    conn = httplib.HTTPSConnection("8.8.8.8", timeout=3)
    try:
        conn.request("HEAD", "/")
        return True
    # Will throw OSError on no connection
    except OSError:
        return False
    finally:
        conn.close()
