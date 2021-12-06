from graal.backends.core.coqua import CoQua
from graal.backends.core.cocom import CoCom

import json
from joblib import Parallel, delayed
import os
from pathlib import Path
import shutil
import sys
import threading


class CocomExtraction:
    BASE_GIT_PATH = "./tmp/cocom/"
    BASE_GIT_URI = "http://github.com/"
    BASE_OUTPUT_PATH = "./results/cocom/"
    OUTPUT_EXT = ".json"

    repository: CoCom = None
    output_path: str

    def __init__(self, repo_name: str):
        repo_uri = os.path.join(self.BASE_GIT_URI, repo_name)
        repo_dir = os.path.join(self.BASE_GIT_PATH, repo_name)

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        self.output_path = os.path.join(self.BASE_OUTPUT_PATH, repo_name)
        self.output_path += self.OUTPUT_EXT
        self.repository = CoCom(uri=repo_uri, git_path=repo_dir)

    def start(self):
        if not os.path.exists(self.output_path):
            if not os.path.exists(os.path.dirname(self.output_path)):
                os.mkdir(os.path.dirname(self.output_path))
            Path(self.output_path).touch()

        with open(self.output_path, "a") as output:
            output.write("[\n")
            for commit in self.repository.fetch():
                sys.stdout.write(f'\rhandling commit: {commit["uuid"]}')
                data: str = json.dumps(commit, indent=2) + ",\n"
                output.write(data)
            output.write("]\n")


class CoQuaExtraction:
    BASE_GIT_PATH = "../tmp/coqua/"
    BASE_GIT_URI = "http://github.com/"
    BASE_OUTPUT_PATH = "../results/coqua/"
    OUTPUT_EXT = ".json"

    repository: CoQua = None
    output_path: str

    def __init__(self, repo_name: str, entrypoint: str):
        repo_uri = os.path.join(self.BASE_GIT_URI, repo_name)
        repo_dir = os.path.join(self.BASE_GIT_PATH, repo_name)

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        self.output_path = os.path.join(self.BASE_OUTPUT_PATH, repo_name)
        self.repository = CoQua(
            uri=repo_uri, entrypoint=entrypoint, git_path=repo_dir)

    def start(self):
        for category in CoQua.CATEGORIES:
            category_output_path = f'{self.output_path}_{category}{self.OUTPUT_EXT}'

            if not os.path.exists(category_output_path):
                dirname: str = os.path.dirname(category_output_path)
                if not os.path.exists(dirname):
                    os.mkdir(dirname)
                Path(category_output_path).touch()

            with open(category_output_path, "a") as output:
                output.write("[\n")
                for commit in self.repository.fetch(category):
                    sys.stdout.write(f'\rhandling commit: {commit["uuid"]}')
                    data: str = json.dumps(commit, indent=2) + ",\n"
                    output.write(data)
                output.write("]\n")


def extract_repository(repo_name: str, repo_entrypoint: str):
    repo_name = "chaoss/grimoirelab-graal"
    repo_entrypoint = "graal"
    ce = CocomExtraction(repo_name)
    qe = CoQuaExtraction(repo_name, repo_entrypoint)

    t_ce = threading.Thread(target=ce.start())
    t_qe = threading.Thread(target=qe.start())

    t_ce.start()
    t_qe.start()

    t_ce.join()
    t_qe.join()

    sys.stdout.flush()
    sys.stdout.write("\rDone\n")


if __name__ == "__main__":
    with open("./extraction-config.json", "r") as config:
        data = config.read()
        json_data = json.loads(data)
        repositories = json_data["repositories"]
    Parallel(n_jobs=len(repositories))(delayed(extract_repository)(
        repositories[i]["uri"], repositories["entrypoint"]) for i in range(len(repositories)))
