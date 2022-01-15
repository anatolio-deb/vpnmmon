import argparse
import subprocess
import threading
from typing import List

from vpnmauth import VpnmApiClient, get_hostname_or_address


class Monitor:
    client = VpnmApiClient()
    total_available = 0
    log_path = "/tmp/vpnmmon.log"
    lock = threading.Lock()
    threads: List[threading.Thread] = []

    def __init__(self, verbose: bool) -> None:
        self.verbose = verbose
        self.nodes = self.client.nodes["data"]["node"]
        if self.verbose:
            print(f"{len(self.nodes)} nodes recieved")

    def traceroute(self, node_id: int, host: str) -> None:
        try:
            proc = subprocess.run(
                ["traceroute", "-T", "-m", "8", host], capture_output=True, check=True
            )
        except subprocess.CalledProcessError as ex:
            print(ex.stderr.decode())
        else:
            result = proc.stdout.decode().split("\n")
            output = {"id": node_id, "hostname": host}

            if len(result) > 5:
                output["status"] = "ok"
                self.total_available += 1
            else:
                output["status"] = "fail"

            self.lock.acquire()

            print(output)

            with open(self.log_path, "a", encoding="utf-8") as file:
                file.write("\n".join(result))

            self.lock.release()

    def run(self):
        for node in self.nodes:
            thread = threading.Thread(
                target=self.traceroute,
                args=(node["id"], get_hostname_or_address(node)),
            )
            thread.start()
            if self.verbose:
                print(f"Tracerouting node id{node['id']} in thread {thread.ident}")
            self.threads.append(thread)

        for thread in self.threads:
            thread.join()

        if self.verbose:
            print("Availability check completed")
            print(f"{self.total_available}/{len(self.nodes)} nodes available")
            print(f"Full log can be found at {self.log_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true", default=False)
    args = parser.parse_args()
    monitor = Monitor(verbose=args.verbose)
    monitor.run()
