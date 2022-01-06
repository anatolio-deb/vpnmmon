import subprocess
import threading

from vpnmauth import VpnmApiClient


def traceroute(server_id: int, host: str) -> None:
    proc = subprocess.run(["traceroute", host], capture_output=True, check=True)
    output = proc.stdout.decode()
    if output.endswith("30  * * *") or len(output.split("\n")) <= 3:
        print(f"{server_id}: NO")
    print(f"{server_id}: YES")


if __name__ == "__main__":
    client = VpnmApiClient()
    threads: threading.Thread = []

    for node in client.get_nodes():
        thread = threading.Thread(
            target=traceroute,
            args=(
                node["server_id"],
                node["server"].split(";")[0],
            ),
        )
        thread.start()
        threads.append(thread)
        for thread in threads:
            thread.join()
