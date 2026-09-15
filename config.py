ROUTER_IP = "192.168.1.240"

SCAN_URL = (
    f"http://{ROUTER_IP}"
    "/goform/RP_getStaBSSIDList"
)

SCAN_INTERVAL = 30

CSV_FILE = "data/wifi_history.csv"
GRAPH_FILE = "graphs/wifi_signal_graph.png"

MOVING_AVERAGE_WINDOW = 3
