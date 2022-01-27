from datetime import datetime
from dateutil.parser import parse
from graal.backends.core.cocom import CoCom, CATEGORY_COCOM_LIZARD_REPOSITORY
import json
import matplotlib.pyplot as plt
import os

"""Exports cocom results from our graal repository"""

results = {"ccn": [], "loc": [], "num_funs": []}


def handle_commit(commit, metric):
    analysis = commit["data"]["analysis"]

    max = 0
    sum = 0.0
    count = 0

    for element in analysis:
        ext = element["ext"]

        if ext != "py" or metric not in element:
            continue

        count += 1

        val = element[metric]

        sum += val

        if val > max:
            max = val

    avg = sum / count

    timestamp = commit["data"]["CommitDate"]
    timestamp = parse(timestamp)
    results[metric].append({"timestamp": timestamp, "avg": avg, "max": max})


git_uri = "https://github.com/chaoss/grimoirelab-graal"
git_path = os.path.abspath("../tmp/cocom")
out_path = os.path.abspath("./results/cocom.json")

cc = CoCom(uri=git_uri, git_path=git_path, in_paths=[".py"])

# gets results
with open("./results/cocom-complete", "a") as output_file:
    i = 0
    for commit in cc.fetch(
        category=CATEGORY_COCOM_LIZARD_REPOSITORY, from_date=datetime(2021, 1, 13)
    ):
        print(commit["data"]["commit"])

        output_file.write(f'{json.dumps(commit, indent=2)},\n')

        for metric in results.keys():
            handle_commit(commit, metric)

        if i > 2:
            break
        i += 1 

# plots results. 
for metric, results in results.items():
    list.sort(results, key=lambda x : x["timestamp"])

    avg = [entry["avg"] for entry in results]
    # max = [entry["max"] for entry in results]
    x = [entry["timestamp"] for entry in results]

    print(avg)

    plt.plot(x, avg, label=f"avg {metric}")
    # plt.plot(x, max, label=f"max {metric}")
    plt.legend()
    plt.title(f"Graal {metric} over repo lifetime")
    plt.savefig(os.path.abspath(f"./results/graal-{metric}.png"))
    plt.clf()
