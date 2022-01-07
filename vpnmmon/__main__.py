import subprocess
import threading

from vpnmauth import VpnmApiClient


def traceroute(node_id: int, host: str) -> None:
    global NODES_AVAILABLE
    proc = subprocess.run(["traceroute", host], capture_output=True, check=True)
    output = proc.stdout.decode()
    if output.endswith("30  * * *") or len(output.split("\n")) <= 3:
        print(f"Node id{node_id} is unavailable")
    else:
        print(f"Node id{node_id} is available")
        NODES_AVAILABLE += 1


if __name__ == "__main__":
    NODES_AVAILABLE = 0
    threads: threading.Thread = []
    client = VpnmApiClient()
    print("Logged in")
    nodes = client.get_nodes()
    print(f"{len(nodes)} nodes recieved")

    for node in nodes:
        thread = threading.Thread(
            target=traceroute,
            args=(
                node["id"],
                node["server"].split(";")[0],
            ),
        )
        thread.start()
        print(f"Tracerouting node id{node['id']} in thread {thread.ident}")
        threads.append(thread)

    for thread in threads:
        thread.join()

    print("Availability check completed")
    print(f"{NODES_AVAILABLE}/{len(nodes)} nodes available")
