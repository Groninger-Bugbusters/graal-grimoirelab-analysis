import json
import os
import shutil
import sys
from pathlib import Path

from graal.backends.core.cocom import CoCom
from graal.backends.core.coqua import CoQua
from joblib import Parallel, delayed


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
    BASE_GIT_PATH = "./tmp/coqua/"
    BASE_GIT_URI = "http://github.com/"
    BASE_OUTPUT_PATH = "./results/coqua/"
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
                try:
                    for commit in self.repository.fetch(category):
                        sys.stdout.write(f'\rhandling commit: {commit["uuid"]}')
                        data: str = json.dumps(commit, indent=2) + ",\n"
                        output.write(data)
                    output.write("]\n")
                except:
                    pass

def extract_repository(repo_name: str, repo_entrypoint: str):
    ce = CocomExtraction(repo_name)
    qe = CoQuaExtraction(repo_name, repo_entrypoint)

    ce.start()
    qe.start()

    sys.stdout.flush()
    sys.stdout.write("\rDone\n")


if __name__ == "__main__":
    with open("./extraction-config.json", "r") as config:
        data = config.read()
        json_data = json.loads(data)
        repositories = json_data["repositories"]
    Parallel(n_jobs=len(repositories))(delayed(extract_repository)(
        repositories[i]["uri"], repositories[i]["entrypoint"]) for i in range(len(repositories)))
