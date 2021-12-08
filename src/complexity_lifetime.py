import json
import os
import sys
from typing import final
import numpy

import dateparser
import matplotlib.pyplot as plt

complexity_lifetimes = {}

def main(path:str): 
    with open(path, "r") as data: 
        commits = json.loads(data.read())
    
    for commit in commits: 
        handle(commit)
    
def handle(commit:dict): 
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
        file_complexity["timestamp"] = dateparser.parse(commit["data"]["CommitDate"])

        complexity_lifetimes[file_name].append(file_complexity)
    
    for (key, value) in complexity_lifetimes.items(): 
        value.sort(key=sorting)

def sorting(val): 
    return val["timestamp"]

def show():
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
    metric = "ccn"
    for ts in timestamps: 
        final_results[ts] = {}

        for name in names: 
            data_entries = complexity_lifetimes[name]
            prev_comp = 0
            for entry in data_entries: 
                gotEntry = False
                
                if ts == entry["timestamp"]: 
                    final_results[ts][name] = entry[metric]
                    gotEntry = True
                    break
                
                if entry["timestamp"] > ts:
                    break

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
    plt.title(f'max and mean {metric} of graal over repository lifetime')
    plt.show()


if __name__ == "__main__": 
    path = "../results/cocom/chaoss/grimoirelab-elk.json"
    path = os.path.join(os.path.dirname(__file__), path)
    main(path)
    show()
