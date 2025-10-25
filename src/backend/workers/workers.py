import threading
import time
from datetime import datetime, timedelta
from importlib import import_module

import yaml


class Worker:
    def __init__(self, name, schedule, max_runtime, max_instances):
        self.name = name
        self.schedule = schedule
        self.max_runtime = max_runtime
        self.max_instances = max_instances
        self.last_run = None
        self.running = False
        self.instances = 0

    def run(self):
        current_time = datetime.now()
        if self.schedule["type"] == "startup":
            if self.last_run is None:
                self.execute_worker()
            return  # Exit after one run if it's a startup type
        elif self.schedule["type"] == "interval":
            next_run_time = (
                self.last_run + timedelta(minutes=self.schedule["interval"])
                if self.last_run
                else None
            )
            if self.last_run is None or current_time >= next_run_time:
                self.execute_worker()

    def execute_worker(self):
        if self.instances < self.max_instances:
            print(f"Running {self.name} worker...")
            self.last_run = datetime.now()
            self.running = True
            script_module = import_module(f"{self.name}")
            script_module.run()
            self.running = False
        else:
            print(f"Maximum instances reached for {self.name}.")


class WorkerManager:
    def __init__(self, config_file):
        self.workers = {}
        self.load_config(config_file)

    def load_config(self, config_file):
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
            for name, details in config["workers"].items():
                self.workers[name] = Worker(
                    name,
                    details["schedule"],
                    details["max_runtime"],
                    details["max_instances"],
                )

    def start_workers(self):
        for worker in self.workers.values():
            if worker.schedule["type"] == "startup":
                worker_thread = threading.Thread(target=worker.run)
                worker_thread.start()
            elif worker.schedule["type"] == "interval":
                worker_thread = threading.Thread(target=self.run_worker, args=(worker,))
                worker_thread.start()

    def run_worker(self, worker):
        while True:
            worker.run()
            time.sleep(
                1
            )  # Keep this to prevent a tight loop that consumes too much CPU.


if __name__ == "__main__":
    manager = WorkerManager("config.yml")
    manager.start_workers()
