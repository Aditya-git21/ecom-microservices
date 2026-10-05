import os
from decimal import Decimal

import httpx
from dotenv import load_dotenv

load_dotenv()

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL")
if not PRODUCT_SERVICE_URL:
    raise RuntimeError("PRODUCT_SERVICE_URL is not set")

# fail fast if it can't connect, allow a bit longer for the response
TIMEOUT = httpx.Timeout(5.0, connect=2.0)


class ProductNotFound(Exception):
    pass


class InsufficientStock(Exception):
    pass


class ProductServiceUnavailable(Exception):
    """Couldn't connect, or got an unexpected response."""


class ProductServiceTimeout(ProductServiceUnavailable):
    """Request sent but no answer in time, so the outcome is UNKNOWN."""


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            return client.request(method, f"{PRODUCT_SERVICE_URL}{path}", **kwargs)
    except httpx.TimeoutException:          # must come before TransportError
        raise ProductServiceTimeout()
    except httpx.TransportError:            # connection refused, DNS failure, etc.
        raise ProductServiceUnavailable()


def get_product(product_id: int) -> dict:
    resp = _request("GET", f"/products/{product_id}")
    if resp.status_code == 404:
        raise ProductNotFound()
    if resp.status_code != 200:
        raise ProductServiceUnavailable(f"unexpected status {resp.status_code}")
    data = resp.json()
    data["price"] = Decimal(data["price"])   # arrives as a string, never use float
    return data


def reduce_stock(product_id: int, quantity: int) -> dict:
    resp = _request("POST", f"/products/{product_id}/reduce-stock",
                    json={"quantity": quantity})
    if resp.status_code == 404:
        raise ProductNotFound()
    if resp.status_code == 400:
        raise InsufficientStock()
    if resp.status_code != 200:
        raise ProductServiceUnavailable(f"unexpected status {resp.status_code}")
    return resp.json()
