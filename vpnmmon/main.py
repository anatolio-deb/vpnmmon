from vpnmauth import VpnmApiClient
import threading
import subprocess

def traceroute(id: int, host: str) -> None:
    proc = subprocess.run(['traceroute', host], capture_output=True, check=True)
    output = proc.stdout.decode()
    if output.endswith("30  * * *") or len(output.split('\n')) <= 3:
        print(f"{id}: NO")
    print(f"{id}: YES")

if __name__ == "__main__":
    client = VpnmApiClient()
    threads: threading.Thread = []

    for node in client.get_nodes():
        id, host = node['id'], node['server'].split(';')[0]
        thread = threading.Thread(target=traceroute, args=(id, host,))
        thread.start()
        threads.append(thread)
        for thread in threads:
            thread.join()