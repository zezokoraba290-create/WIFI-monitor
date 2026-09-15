import csv
import os
import threading
import time
from collections import defaultdict

import flet as ft
import matplotlib.pyplot as plt

from config import (
    SCAN_INTERVAL,
    CSV_FILE,
    GRAPH_FILE,
    MOVING_AVERAGE_WINDOW
)

from scanner.wifi_scanner import scan_networks
from monitor.collector import DataCollector
from analysis.security import (
    security_score,
    security_label
)


class WiFiMonitorApp:

    def __init__(self, page):

        self.page = page

        self.collector = DataCollector()

        self.running = False
        self.worker = None

        self.current_networks = {}

        self.status_text = ft.Text(
            "Stopped"
        )

        self.network_count = ft.Text(
            "Networks: 0"
        )

        self.last_scan = ft.Text(
            "Last scan: --"
        )

        self.error_text = ft.Text(
            ""
        )

        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(
                    ft.Text("SSID")
                ),
                ft.DataColumn(
                    ft.Text("Signal")
                ),
                ft.DataColumn(
                    ft.Text("Channel")
                ),
                ft.DataColumn(
                    ft.Text("Band")
                ),
                ft.DataColumn(
                    ft.Text("Security")
                ),
                ft.DataColumn(
                    ft.Text("Score")
                )
            ],
            rows=[]
        )

        self.graph_image = ft.Image(
            src="",
            visible=False,
            width=900
        )

        # -------------------------
        # LIVE ANIMATED CHART
        # -------------------------

        self.chart_points = {}
        self.network_colors = {}
        self.scan_index = 0
        self.max_points_window = 20

        self.chart_colors = [
            ft.Colors.RED,
            ft.Colors.BLUE,
            ft.Colors.GREEN,
            ft.Colors.ORANGE,
            ft.Colors.PURPLE,
            ft.Colors.CYAN,
            ft.Colors.PINK,
            ft.Colors.TEAL,
            ft.Colors.AMBER,
            ft.Colors.INDIGO
        ]

        self.live_chart = ft.LineChart(
            data_series=[],
            border=ft.border.all(
                1,
                ft.Colors.with_opacity(0.3, ft.Colors.ON_SURFACE)
            ),
            left_axis=ft.ChartAxis(
                labels_size=40,
                title=ft.Text("Signal %")
            ),
            bottom_axis=ft.ChartAxis(
                labels_size=30,
                title=ft.Text("Scan #")
            ),
            min_y=0,
            max_y=100,
            min_x=0,
            max_x=self.max_points_window,
            animate=300,
            expand=True,
            height=350,
            visible=False
        )

        self.live_legend = ft.Row(
            wrap=True,
            spacing=10
        )

        self.start_button = ft.ElevatedButton(
            "Start",
            on_click=self.start_monitor
        )

        self.stop_button = ft.ElevatedButton(
            "Stop",
            on_click=self.stop_monitor
        )

        self.build_page()

    # -------------------------
    # UI
    # -------------------------

    def build_page(self):

        self.page.title = "Wi-Fi Monitor"

        self.page.padding = 20

        self.page.scroll = ft.ScrollMode.AUTO

        title = ft.Text(
            "Wi-Fi Monitor",
            size=30,
            weight=ft.FontWeight.BOLD
        )

        controls = ft.Row(
            [
                self.start_button,
                self.stop_button,
                self.status_text,
                self.network_count,
                self.last_scan
            ],
            wrap=True
        )

        self.page.add(
            title,

            ft.Divider(),

            controls,

            self.error_text,

            ft.Divider(),

            self.table,

            ft.Divider(),

            ft.Text(
                "Live Signal (Real-Time)",
                size=24,
                weight=ft.FontWeight.BOLD
            ),

            self.live_chart,

            self.live_legend,

            ft.Divider(),

            ft.Text(
                "Signal Graph",
                size=24,
                weight=ft.FontWeight.BOLD
            ),

            self.graph_image
        )

    # -------------------------
    # START
    # -------------------------

    def start_monitor(self, e=None):

        if self.running:
            return

        self.collector.clear()

        self.current_networks.clear()

        self.chart_points.clear()

        self.network_colors.clear()

        self.scan_index = 0

        self.live_chart.data_series = []

        self.live_chart.min_x = 0

        self.live_chart.max_x = self.max_points_window

        self.live_chart.visible = True

        self.live_legend.controls = []

        self.running = True

        self.status_text.value = "Running..."

        self.error_text.value = ""

        self.graph_image.visible = False

        self.update_ui()

        self.worker = threading.Thread(
            target=self.monitor_loop,
            daemon=True
        )

        self.worker.start()

    # -------------------------
    # STOP
    # -------------------------

    def stop_monitor(self, e=None):

        if not self.running:
            return

        self.running = False

        self.status_text.value = "Stopping..."

        self.update_ui()

        if self.worker:

            self.worker.join(
                timeout=2
            )

        self.save_csv()

        if self.collector.get_data():

            self.create_graph()

        self.status_text.value = "Stopped"

        self.update_ui()

    # -------------------------
    # MONITOR LOOP
    # -------------------------

    def monitor_loop(self):

        while self.running:

            try:

                networks = scan_networks()

                self.collector.add_scan(
                    networks
                )

                self.update_live_chart(
                    networks
                )

                self.current_networks = {
                    network["bssid"]: network
                    for network in networks
                }

                self.update_table(
                    networks
                )

                self.last_scan.value = (
                    "Last scan: "
                    + time.strftime("%H:%M:%S")
                )

                self.network_count.value = (
                    f"Networks: {len(networks)}"
                )

                self.status_text.value = (
                    "Running..."
                )

                self.error_text.value = ""

                self.update_ui()

            except Exception as error:

                self.error_text.value = (
                    f"Error: {error}"
                )

                self.update_ui()

            for _ in range(SCAN_INTERVAL):

                if not self.running:
                    break

                time.sleep(1)

    # -------------------------
    # LIVE ANIMATED CHART
    # -------------------------

    def update_live_chart(self, networks):

        self.scan_index += 1

        for network in networks:

            key = (
                network["ssid"],
                network["bssid"]
            )

            if key not in self.chart_points:
                self.chart_points[key] = []

            if key not in self.network_colors:
                self.network_colors[key] = (
                    self.chart_colors[
                        len(self.network_colors)
                        % len(self.chart_colors)
                    ]
                )

            self.chart_points[key].append(
                ft.LineChartDataPoint(
                    self.scan_index,
                    network["signal"]
                )
            )

            if len(self.chart_points[key]) > self.max_points_window:

                self.chart_points[key] = (
                    self.chart_points[key][
                        -self.max_points_window:
                    ]
                )

        data_series = []

        legend_items = []

        for key, points in self.chart_points.items():

            ssid = key[0] if key[0].strip() else "<Hidden SSID>"

            color = self.network_colors[key]

            data_series.append(
                ft.LineChartData(
                    data_points=points,
                    stroke_width=2,
                    color=color,
                    curved=True,
                    stroke_cap_round=True,
                    point=True
                )
            )

            legend_items.append(
                ft.Row(
                    [
                        ft.Container(
                            width=12,
                            height=12,
                            bgcolor=color,
                            border_radius=6
                        ),
                        ft.Text(ssid, size=12)
                    ],
                    spacing=4
                )
            )

        self.live_chart.data_series = data_series

        self.live_legend.controls = legend_items

        all_x = [
            point.x
            for points in self.chart_points.values()
            for point in points
        ]

        if all_x:

            min_x = min(all_x)

            max_x = max(all_x)

            self.live_chart.min_x = min_x

            self.live_chart.max_x = (
                max_x
                if max_x > min_x
                else min_x + 1
            )

    # -------------------------
    # TABLE
    # -------------------------

    def update_table(self, networks):

        rows = []

        sorted_networks = sorted(
            networks,
            key=lambda x: x["signal"],
            reverse=True
        )

        for network in sorted_networks:

            score = security_score(
                network["encryption"]
            )

            label = security_label(
                score
            )

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Text(
                                network["ssid"]
                            )
                        ),

                        ft.DataCell(
                            ft.Text(
                                f'{network["signal"]}%'
                            )
                        ),

                        ft.DataCell(
                            ft.Text(
                                str(
                                    network["channel"]
                                )
                            )
                        ),

                        ft.DataCell(
                            ft.Text(
                                str(
                                    network["band"]
                                )
                            )
                        ),

                        ft.DataCell(
                            ft.Text(
                                f'{network["encryption"]} '
                                f'({label})'
                            )
                        ),

                        ft.DataCell(
                            ft.Text(
                                f"{score}/100"
                            )
                        )
                    ]
                )
            )

        self.table.rows = rows

    # -------------------------
    # SAVE CSV
    # -------------------------

    def save_csv(self):

        data = self.collector.get_data()

        if not data:
            return

        os.makedirs(
            "data",
            exist_ok=True
        )

        with open(
            CSV_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "Time",
                "SSID",
                "BSSID",
                "Signal",
                "Channel",
                "Band",
                "Encryption"
            ])

            for item in data:

                writer.writerow([
                    item["time"].strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

                    item["ssid"],

                    item["bssid"],

                    item["signal"],

                    item["channel"],

                    item["band"],

                    item["encryption"]
                ])

    # -------------------------
    # MOVING AVERAGE
    # -------------------------

    def moving_average(self, values):

        if len(values) < 2:
            return values

        result = []

        window = MOVING_AVERAGE_WINDOW

        for i in range(len(values)):

            start = max(
                0,
                i - window + 1
            )

            section = values[
                start:i + 1
            ]

            result.append(
                sum(section) / len(section)
            )

        return result

    # -------------------------
    # GRAPH
    # -------------------------

    def create_graph(self):

        data = self.collector.get_data()

        os.makedirs(
            "graphs",
            exist_ok=True
        )

        networks = defaultdict(
            lambda: {
                "time": [],
                "signal": []
            }
        )

        for item in data:

            key = (
                item["ssid"],
                item["bssid"]
            )

            networks[key]["time"].append(
                item["time"]
            )

            networks[key]["signal"].append(
                item["signal"]
            )

        plt.figure(
            figsize=(14, 8)
        )

        for (ssid, bssid), values in networks.items():

            times = values["time"]

            signals = values["signal"]

            smooth_signals = (
                self.moving_average(
                    signals
                )
            )

            label = ssid

            if not ssid.strip():

                label = "<Hidden SSID>"

            plt.plot(
                times,
                smooth_signals,
                marker="o",
                markersize=3,
                linewidth=2,
                label=label
            )

        plt.title(
            "Wi-Fi Signal Strength Over Time"
        )

        plt.xlabel(
            "Time"
        )

        plt.ylabel(
            "Signal (%)"
        )

        plt.ylim(
            0,
            100
        )

        plt.grid(
            True
        )

        plt.legend(
            bbox_to_anchor=(
                1.02,
                1
            ),
            loc="upper left"
        )

        plt.xticks(
            rotation=45
        )

        plt.tight_layout()

        plt.savefig(
            GRAPH_FILE,
            dpi=150
        )

        plt.close()

        self.graph_image.src = (
            GRAPH_FILE
        )

        self.graph_image.visible = True

        self.update_ui()

    # -------------------------
    # UI UPDATE
    # -------------------------

    def update_ui(self):

        try:
            self.page.update()
        except Exception:
            pass


def create_app(page):

    WiFiMonitorApp(page)
