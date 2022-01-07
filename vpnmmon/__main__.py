import socket
import subprocess
import threading

from vpnmauth import VpnmApiClient


class Monitor:
    total_available = 0
    log_path = "/tmp/vpnmmon.log"
    lock = threading.Lock()
    threads: threading.Thread = []

    def __init__(self) -> None:
        self.client = VpnmApiClient()
        print("Logged in")
        self.nodes = self.client.get_nodes()
        print(f"{len(self.nodes)} nodes recieved")

    def traceroute(self, node_id: int, host: str) -> None:
        try:
            proc = subprocess.run(
                ["traceroute", host, "-T"], capture_output=True, check=True
            )
        except subprocess.CalledProcessError as ex:
            print(ex.stderr.decode())
        else:
            output = list(filter(lambda x: x, proc.stdout.decode().split("\n")))

            if socket.gethostbyname(host) in output[0] and output[-1]:
                print(f"Node id{node_id} is available")
                self.total_available += 1
            else:
                print(f"Node id{node_id} is unavailable")

            self.lock.acquire()

            with open(self.log_path, "a", encoding="utf-8") as file:
                file.write(output)

            self.lock.release()

    def run(self):
        for node in self.nodes:
            thread = threading.Thread(
                target=self.traceroute,
                args=(
                    node["id"],
                    node["server"].split(";")[0],
                ),
            )
            thread.start()
            print(f"Tracerouting node id{node['id']} in thread {thread.ident}")
            self.threads.append(thread)

        for thread in self.threads:
            thread.join()

        print("Availability check completed")
        print(f"{self.total_available}/{len(self.nodes)} nodes available")
        print(f"Full log can be found at {self.log_path}")


if __name__ == "__main__":
    monitor = Monitor()
    monitor.run()
