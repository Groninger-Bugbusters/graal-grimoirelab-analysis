import json

"""calculates min, max, mean, etc. LOC of different commits"""

with open("../extraction-config.json", "r") as config_file:
    uris = [
        repository["uri"]
        for repository in json.loads(config_file.read())["repositories"]
    ]

total_results = {}

for uri in uris:
    loc_count = {}
    with open(f"../results/cocom/{uri}.json", "r") as data_file:
        commits = json.loads(data_file.read())

    for commit in commits:
        data: dict = commit["data"]["analysis"]
        for file in data: 
            if not "loc" in file: 
                continue 

            loc = file["loc"]
            file_name = file["file_path"]

            if loc == None and file_name in loc_count: 
                loc_count.pop(file_name)
                continue
            elif loc == None or file["ext"] != "py": 
                continue

            file.pop("file_path")
            file.pop("ext")

            loc_count[file_name] = file


    results = {}
    
    for key, value in loc_count.items(): 
        for metric_key, metric_value in value.items():
            if metric_key not in results:
                results[metric_key] = {
                    "total":0.0, 
                    "average":0.0,
                    "minimum":0.0,
                    "maximum":0.0,
                    "largest_file": "",
                    "count":0,
                }
            
            results[metric_key]["count"] += 1

            results[metric_key]["total"] += metric_value

            if results[metric_key]["minimum"] > metric_value: 
                results[metric_key]["minimum"] = metric_value  

            if results[metric_key]["maximum"] < metric_value: 
                results[metric_key]["maximum"] = metric_value
                results[metric_key]["largest_file"] = key

        
    for key, value in results.items(): 
        avg = results[key]["total"] / results[key]["count"]
        results[key]["average"] = avg

    total_results[uri] = results

with open("../results/stats.json", "w") as output_file: 
    output_file.write(json.dumps(total_results, indent=2))
