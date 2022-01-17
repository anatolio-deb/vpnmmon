import argparse
import json
import logging
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

    def __init__(self) -> None:
        self.nodes = self.client.nodes["data"]["node"]
        logging.info("%s nodes recieved", len(self.nodes))

    def traceroute(self, node_id: int, host: str) -> None:
        output = {"id": node_id, "hostname": host}

        try:
            proc = subprocess.run(
                ["traceroute", "-T", "-m", "8", host], capture_output=True, check=True
            )
        except subprocess.CalledProcessError as ex:
            logging.error(ex.stderr.decode())
            output["status"] = None
        else:
            result = list(
                filter(
                    lambda line: line[0].isnumeric(),
                    [
                        line.strip()
                        for line in list(filter(None, proc.stdout.decode().split("\n")))
                    ],
                )
            )

            if len(result) > 4:
                output["status"] = True
                self.total_available += 1
            else:
                output["status"] = False

            self.lock.acquire()

            print(json.dumps(output))

            with open(self.log_path, "a", encoding="utf-8") as file:
                file.write(proc.stdout.decode())

            self.lock.release()

    def run(self):
        for node in self.nodes:
            thread = threading.Thread(
                target=self.traceroute,
                args=(node["id"], get_hostname_or_address(node)),
            )
            thread.start()

            logging.info(
                "Tracerouting node id%s in thread %s", node["id"], thread.ident
            )
            self.threads.append(thread)

        for thread in self.threads:
            thread.join()

        logging.info("Availability check completed")
        logging.info("%s/%s nodes available", self.total_available, len(self.nodes))
        logging.info("Full log can be found at %s", self.log_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verbosity",
        choices=["debug", "info", "error", "none"],
        default="none",
    )
    args = parser.parse_args()

    if args.verbosity == "debug":
        LOGGING_LEVEL = logging.DEBUG
    elif args.verbosity == "info":
        LOGGING_LEVEL = logging.INFO
    elif args.verbosity == "error":
        LOGGING_LEVEL = logging.ERROR
    elif args.verbosity == "none":
        LOGGING_LEVEL = logging.CRITICAL

    logging.basicConfig(format="%(levelname)s:%(message)s", level=LOGGING_LEVEL)
    monitor = Monitor()
    monitor.run()
