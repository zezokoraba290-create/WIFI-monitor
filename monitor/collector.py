from datetime import datetime


class DataCollector:

    def __init__(self):
        self.data = []

    def clear(self):
        self.data.clear()

    def add_scan(self, networks):

        current_time = datetime.now()

        for network in networks:

            self.data.append({
                "time": current_time,
                "ssid": network["ssid"],
                "bssid": network["bssid"],
                "signal": network["signal"],
                "channel": network["channel"],
                "band": network["band"],
                "encryption": network["encryption"]
            })

    def get_data(self):
        return self.data
