from joblib import Parallel, delayed
from array import array
from graal.backends.core.cocom import CoCom
import json
import os
import shutil
import sys
import matplotlib.pyplot as plt
import math


class GraalTest:
    """
    Can be used to analyse a single Github repository,
    and store and graph the complexity changes per python file.
    """
    BASE_URL = "http://github.com/"
    DATA_PATH = "../tmp/"
    RESULTS_PATH = "../results/"
    LOG_EXT = ".json"

    repository_name: str = None
    repository: CoCom = None

    # maps file names to timestamp (x) and
    # complexity information (y_i) coordinates.
    file_complexity: dict = {}

    def __init__(self, repository_name: str):
        """
        Sets up Graal repository
        """
        sys.stdout.write(f'Started analysis with repo: {repository_name}\n')
        self.repository_name = repository_name
        repo_uri = os.path.join(self.BASE_URL, repository_name)
        repo_dir = os.path.join(self.DATA_PATH, repository_name)
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)
        self.repository = CoCom(uri=repo_uri, git_path=repo_dir)

    def start(self):
        """
        Template method that starts repository analysis using Graal.Cocom.
        Handles all commits, and stores and graphs the results.
        """
        self.start_analysis()
        self.store_complexity()
        self.graph_complexity()

    def start_analysis(self):
        """
        Performs analysis using Graal.CoCom
        """
        for commit in self.repository.fetch():
            sys.stdout.write(f'\rProcessing commit: {commit["uuid"]}')
            self.handle(commit)
        sys.stdout.write('\rDone!')
        sys.stdout.flush()
        sys.stdout.write("\n")

    def handle(self, commit: dict):
        """
        If the commit is a merge, it iterates through
        all affected files, and per python file adds
        the Cocom results to the analysis results.
        """
        if GraalTest.is_merge(commit):
            for file in commit["data"]["analysis"]:
                if GraalTest.is_python(file):
                    self.add_file_complexity(commit, file)

    def add_file_complexity(self, commit: dict, file: dict):
        """
        Adds a new file complexity entry to the current results.
        """
        path = file["file_path"]
        file.pop('file_path', None)
        file.pop('ext', None)
        entry = {"timestamp": commit["timestamp"], "analysis": file}
        try:
            self.file_complexity[path].append(entry)
        except:
            self.file_complexity[path] = [entry]

    def store_complexity(self):
        """
        Stores results in persistent storage.
        Makes directory if none exists yet.
        """
        file_path = os.path.join(self.RESULTS_PATH, self.repository_name)
        file_path += self.LOG_EXT
        dirname = os.path.dirname(file_path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(file_path, "w") as file:
            data = json.dumps(self.file_complexity, indent=2)
            file.write(data)

    def load_complexity(self):
        """
        Loads data from persistent storage.
        """
        file_path = os.path.join(self.RESULTS_PATH, self.repository_name)
        file_path += self.LOG_EXT
        with open(file_path, "r") as file:
            data = file.read()
            self.file_complexity = json.loads(data)

    def graph_complexity(self):
        """Graphs Cocom results with pyplot"""
        metrics: array = ["ccn", "avg_ccn", "avg_loc", "avg_tokens",
                          "num_funs", "loc", "tokens", "blanks", "comments"]
        rows = columns = int(math.sqrt(len(metrics)))
        if len(metrics) % columns > 0:
            rows += 1
        _, axis = plt.subplots(rows, columns)
        i: int = 0
        for metric in metrics:
            row: int = int(i % columns)
            col: int = int(i / columns)
            for (file, entry) in self.file_complexity.items():
                x: array = [change["timestamp"] for change in entry]
                y: array = [change["analysis"][metric] for change in entry]
                axis[row, col].plot(x, y, label=file)
            axis[row, col].set_title(f'Cocom: {metric}')
            i += 1
        plt.show()

    @staticmethod
    def is_merge(commit: dict) -> bool:
        """
        Returns true when the commit is a merge.
        """
        try:
            commit["data"]["Merge"]
            return True
        except:
            return False

    @staticmethod
    def is_python(file: dict) -> bool:
        """
        Returns true when the file is a python file.
        """
        return file["ext"] == "py"


def perform_repository_analysis(repository: str):
    ra = GraalTest(repository)
    ra.start()
    # ra.load_complexity()
    # ra.graph_complexity()


if __name__ == "__main__":
    with open("./config.json") as config:
        data = config.read()
        json_data = json.loads(data)
        repositories = json_data["repositories"]
    Parallel(n_jobs=len(repositories))(delayed(perform_repository_analysis)(
        repositories[i]) for i in range(len(repositories)))
