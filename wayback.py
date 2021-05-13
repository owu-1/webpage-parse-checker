def wayback(sources, download_function):
    import json
    from datetime import datetime
    import os
    import re

    CACHE_LOCATION = "snapshot_cache"
    CACHE_REGEX = re.compile(r"^(\d{14})\.html$")
    TIMESTAMP_FORMAT = "%Y%m%d%H%M%S"
    CDX_API_URL = ("http://web.archive.org/cdx/search/cdx?"
                   "url={url}&output=json&fl=timestamp,digest&limit=-{limit}")
    SNAPSHOT_URL = "http://web.archive.org/web/{timestamp}id_/{url}"

    parse_fail_timestamps = {}
    for source_name, source_data in sources.items():
        url = source_data["url"]
        snapshot_search_limit = source_data["snapshot_search_limit"]
        parse_function = source_data["parse_function"]
        if snapshot_search_limit < 0:
            print("Snapshot search limit is less than 0 for", source_name)
            return
        source_cache_dir = f"{CACHE_LOCATION}/{source_name}"
        os.makedirs(source_cache_dir, exist_ok=True)
        # search for unique snapshots
        snapshot_timestamps = set()
        if snapshot_search_limit:
            search_url = CDX_API_URL.format(url=url,
                                            limit=snapshot_search_limit)
            search_json = download_function(search_url)
            snapshots = json.loads(search_json)
            snapshots.pop(0)  # remove cdx format line
            previous_digest = None
            # multiple snapshots can occur at a single timestamp
            for snapshot in snapshots:
                timestamp = snapshot[0]
                digest = snapshot[1]
                # skip download if identical to previous snapshot
                if digest == previous_digest:
                    continue
                snapshot_timestamps.add(timestamp)
                previous_digest = digest
            print("Found", len(snapshot_timestamps),
                  "unique snapshots for", source_name)
        else:
            cache_file_names = os.listdir(source_cache_dir)
            for cache_file_name in cache_file_names:
                match = CACHE_REGEX.match(cache_file_name)
                if match:
                    timestamp = match[1]
                    snapshot_timestamps.add(timestamp)

        # download, cache and test snapshots
        parse_fail_timestamps[source_name] = []
        fails = parse_fail_timestamps[source_name]
        for timestamp in snapshot_timestamps:
            snapshot_location = f"{source_cache_dir}/{timestamp}.html"
            timestamp_readable = datetime.strptime(timestamp, TIMESTAMP_FORMAT)
            if os.path.isfile(snapshot_location):
                print("Using cached snapshot from", timestamp_readable)
                with open(snapshot_location) as f:
                    snapshot_html = f.read()
            else:
                print("Downloading snapshot from", timestamp_readable)
                snapshot_url = SNAPSHOT_URL.format(timestamp=timestamp,
                                                   url=url)
                snapshot_html = download_function(snapshot_url)
                # cache snapshot
                with open(snapshot_location, 'w') as f:
                    f.write(snapshot_html)
            # test snapshot
            parse_result = parse_function(snapshot_html)
            if parse_result:
                print("Parsed successfully!")
            else:
                print("Parse failed.")
                fails.append(timestamp)

    for source_name, timestamps in parse_fail_timestamps.items():
        print(source_name, "had", len(timestamps), "parse fails")
        if timestamps:
            print("Parse fails occured in snapshots from:", *timestamps)
