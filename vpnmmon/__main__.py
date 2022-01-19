import argparse
import json
import logging
import subprocess
import threading
from datetime import datetime
from typing import List

from vpnmauth import VpnmApiClient, get_hostname_or_address


class Monitor:
    """Gets nodes from VPN Manager backend and traceroutes them"""

    total_available = 0
    log_path = "/tmp/vpnmmon.log"
    lock = threading.Lock()
    threads: List[threading.Thread] = []
    timestamp: float = 0.0
    results: List = []
    client = VpnmApiClient()

    def __init__(self, token: str = "", url: str = "") -> None:
        if url and token:
            self.client = VpnmApiClient(url, token=token)
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
            proc_out = proc.stdout.decode()
            result = list(
                filter(
                    lambda line: line[0].isnumeric(),
                    [line.strip() for line in list(filter(None, proc_out.split("\n")))],
                )
            )

            if len(result) > 4:
                output["status"] = True
                self.total_available += 1
            else:
                output["status"] = False

            self.lock.acquire()

            with open(self.log_path, "a", encoding="utf-8") as file:
                file.write(proc_out)

            self.lock.release()
        finally:
            self.lock.acquire()

            self.results.append(output)

            self.lock.release()

    def run(self):
        self.timestamp = datetime.now().timestamp()

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

        truly = []
        falsy = []

        for result in self.results:
            if result["status"]:
                truly.append(self.results.pop(self.results.index(result)))

        for result in self.results:
            if result["status"] is False:
                falsy.append(self.results.pop(self.results.index(result)))

        self.results = (
            sorted(truly, key=lambda result: result["id"])
            + sorted(falsy, key=lambda result: result["id"])
            + sorted(self.results, key=lambda result: result["id"])
        )

        print(
            json.dumps(
                {"timestamp": self.timestamp, "results": self.results},
                sort_keys=True,
                indent=4,
            )
        )

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
    parser.add_argument(
        "--credentials",
        help="A path to credentials file, e.g. 'credentials.json'",
        default="",
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

    if args.credentials:
        with open(args.credentials, "r", encoding="utf-8") as file:
            credentials = json.load(file)
        monitor = Monitor(credentials.token, credentials.url)
    else:
        monitor = Monitor()
    monitor.run()
