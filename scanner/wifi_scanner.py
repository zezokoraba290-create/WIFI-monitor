import requests
from bs4 import BeautifulSoup

from config import SCAN_URL


def scan_networks():
    response = requests.post(
        SCAN_URL,
        timeout=10
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    networks = []

    count_element = soup.find(id="arrayCount")

    if count_element:
        try:
            count = int(
                count_element.get("value", "0")
            )
        except ValueError:
            count = 100
    else:
        count = 100

    for i in range(count):

        ssid = soup.find(
            id=f"ESSID_{i}"
        )

        if not ssid:
            continue

        signal = soup.find(
            id=f"singalLevel_{i}"
        )

        bssid = soup.find(
            id=f"BSSID_{i}"
        )

        channel = soup.find(
            id=f"channel_{i}"
        )

        band = soup.find(
            id=f"freqBand_{i}"
        )

        encryption = soup.find(
            id=f"encryType_{i}"
        )

        if not signal:
            continue

        try:
            signal_value = int(
                signal.get_text(strip=True)
                .replace("%", "")
            )
        except ValueError:
            continue

        networks.append({
            "ssid": ssid.get_text(strip=True),
            "bssid": (
                bssid.get("value")
                if bssid
                else "?"
            ),
            "signal": signal_value,
            "channel": (
                channel.get("value")
                if channel
                else "?"
            ),
            "band": (
                band.get_text(strip=True)
                if band
                else "?"
            ),
            "encryption": (
                encryption.get_text(strip=True)
                if encryption
                else "?"
            )
        })

    return networks
