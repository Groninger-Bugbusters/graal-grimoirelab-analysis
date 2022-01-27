# Beware traveler; Here, there be dragons.

import json
import os
from pathlib import Path

import dateparser
import matplotlib.pyplot as plt
import numpy

complexity_lifetimes = {}


def main(path: str):
    complexity_lifetimes.clear()

    with open(path, "r") as data:
        commits = json.loads(data.read())

    for commit in commits:
        handle(commit)


def handle(commit: dict):
    for file_complexity in commit["data"]["analysis"]:
        file_name = file_complexity["file_path"]

        if not "ext" in file_complexity or file_complexity["ext"] != "py":
            continue

        if not file_name in complexity_lifetimes:
            complexity_lifetimes[file_name] = []

        if not "ext" in file_complexity:
            complexity_lifetimes.pop(file_name)
            continue

        file_complexity.pop("ext")
        file_complexity.pop("file_path")
        file_complexity["timestamp"] = dateparser.parse(
            commit["data"]["CommitDate"])

        complexity_lifetimes[file_name].append(file_complexity)

    for value in complexity_lifetimes.values():
        value.sort(key=commit_order)


def commit_order(val):
    return val["timestamp"]


def show(metric: str, repository_name:str):
    # NOW: {file_name: [(timestamp, ccn)]}
    # GOAL: {timestamp: {file_name: ccn}}
    final_results = {}

    # gets names
    names = []
    for (file_name, ccn) in complexity_lifetimes.items():
        names.append(file_name)

    # gets all timestamps
    timestamps = []
    for name in names:
        for ccn in complexity_lifetimes[name]:
            ts = ccn["timestamp"]
            if not ts in timestamps:
                timestamps.append(ts)

    # gets complexity entries and maps them to timestamps.
    timestamps.sort()
    for ts in timestamps:
        final_results[ts] = {}

        for name in names:
            data_entries = complexity_lifetimes[name]
            prev_comp = 0
            for entry in data_entries:
                gotEntry = False

                if ts == entry["timestamp"]:
                    gotEntry = True

                    if metric not in entry: 
                        continue

                    final_results[ts][name] = entry[metric]
                    break

                if entry["timestamp"] > ts:
                    break
                
                if metric in entry: 
                    prev_comp = entry[metric]

            if not gotEntry:
                final_results[ts][name] = prev_comp

    # calculates max/mean of the data
    max = -numpy.Infinity
    mean = 0

    x = final_results.keys()
    maxs = []
    means = []

    for complexities in final_results.values():
        for ccn in complexities.values():
            if ccn > max:
                max = ccn

            mean += ccn

        maxs.append(max)
        mean /= len(complexity_lifetimes)
        means.append(mean)

    plt.plot(x, maxs, label=f'max {metric}')
    plt.plot(x, means, label=f'mean {metric}')
    plt.legend()
    plt.title(f'{repository_name} {metric} over repo lifetime')
    plt.savefig(os.path.join(Path(__file__).parent.absolute(), "../figures/", f'{repository_name}_mean_max_{metric}.png'))
    plt.clf()

if __name__ == "__main__":
    metrics = ["ccn", "loc", "num_funs"]

    file_path = Path(__file__).parent.absolute()

    print(f'file path: {file_path}')

    config_path = os.path.join(file_path, "../extraction-config.json")
    with open(config_path, "r") as config_file:
        config = json.loads(config_file.read())

    for repository in config["repositories"]:
        repo_uri = os.path.join(
            file_path, "../results/cocom", repository["uri"])
        repo_uri += ".json"

        repo_name = os.path.basename(repo_uri).split('.')
        repo_name = repo_name[0].split('-')
        repo_name = repo_name[1]

        if os.path.exists(repo_uri):
            main(repo_uri)

            for metric in metrics:
                show(metric, repo_name)
