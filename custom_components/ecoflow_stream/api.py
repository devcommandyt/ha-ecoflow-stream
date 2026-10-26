"""EcoFlow Open API credentials + a minimal MQTT 3.1.1 client (no third-party packages).

STREAM devices do not answer the REST quota endpoint; they only publish over MQTT.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import random
import ssl
import time
from collections.abc import Callable

import aiohttp

_LOGGER = logging.getLogger(__name__)
API_HOST = "api-e.ecoflow.com"


class EcoflowError(Exception):
    """API or MQTT error."""


async def get_certification(session: aiohttp.ClientSession, access_key: str, secret_key: str) -> dict:
    """Fetch the MQTT credentials for this developer account (signed GET)."""
    nonce = str(random.randint(100000, 999999))
    ts = str(int(time.time() * 1000))
    to_sign = f"accessKey={access_key}&nonce={nonce}&timestamp={ts}"
    sign = hmac.new(secret_key.encode(), to_sign.encode(), hashlib.sha256).hexdigest()
    headers = {"accessKey": access_key, "nonce": nonce, "timestamp": ts, "sign": sign}
    async with session.get(
        f"https://{API_HOST}/iot-open/sign/certification",
        headers=headers,
        timeout=aiohttp.ClientTimeout(total=15),
    ) as resp:
        data = await resp.json(content_type=None)
    if str(data.get("code")) != "0":
        raise EcoflowError(data.get("message", "unknown error"))
    return data["data"]


def _str(s: str) -> bytes:
    b = s.encode()
    return len(b).to_bytes(2, "big") + b


def _packet(first: int, body: bytes) -> bytes:
    n = len(body)
    out = bytearray([first])
    while True:
        d, n = n % 128, n // 128
        out.append(d | 0x80 if n else d)
        if not n:
            break
    return bytes(out) + body


class EcoflowStreamClient:
    """Keeps one MQTT subscription open and hands every JSON update to `on_data`."""

    def __init__(self, session, ssl_context: ssl.SSLContext, access_key: str, secret_key: str,
                 sn: str, on_data: Callable[[dict], None], on_state: Callable[[bool], None] | None = None) -> None:
        self._session = session
        self._ssl = ssl_context
        self._access_key = access_key
        self._secret_key = secret_key
        self._sn = sn
        self._on_data = on_data
        self._on_state = on_state or (lambda _c: None)

    async def run(self) -> None:
        """Run until cancelled; reconnects with a growing pause."""
        delay = 5
        while True:
            try:
                await self._connection()
                delay = 5
            except asyncio.CancelledError:
                raise
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("EcoFlow connection lost: %s", err)
            self._on_state(False)
            await asyncio.sleep(delay)
            delay = min(delay * 2, 300)

    async def _connection(self) -> None:
        cert = await get_certification(self._session, self._access_key, self._secret_key)
        user = cert["certificateAccount"]
        reader, writer = await asyncio.open_connection(cert["url"], int(cert["port"]), ssl=self._ssl)
        try:
            connect = (_str("MQTT") + bytes([4, 0xC2, 0, 60]) + _str(f"HA_{random.randint(0, 999999)}")
                       + _str(user) + _str(cert["certificatePassword"]))
            writer.write(_packet(0x10, connect))
            await writer.drain()
            ack = await asyncio.wait_for(reader.readexactly(4), 15)
            if ack[0] >> 4 != 2 or ack[3] != 0:
                raise EcoflowError(f"MQTT connect refused ({ack[3]})")
            writer.write(_packet(0x82, b"\x00\x01" + _str(f"/open/{user}/{self._sn}/quota") + b"\x00"))
            await writer.drain()
            self._on_state(True)
            while True:
                try:
                    first = (await asyncio.wait_for(reader.readexactly(1), 30))[0]
                except asyncio.TimeoutError:
                    writer.write(b"\xC0\x00")  # keep-alive
                    await writer.drain()
                    continue
                length, mul = 0, 1
                while True:
                    b = (await reader.readexactly(1))[0]
                    length += (b & 0x7F) * mul
                    mul *= 128
                    if not b & 0x80:
                        break
                body = await reader.readexactly(length)
                if first >> 4 == 3:  # PUBLISH
                    tl = int.from_bytes(body[:2], "big")
                    off = 2 + tl + (2 if (first >> 1) & 3 else 0)
                    try:
                        data = json.loads(body[off:])
                    except ValueError:
                        continue
                    if isinstance(data, dict):
                        self._on_data(data)
        finally:
            writer.close()
