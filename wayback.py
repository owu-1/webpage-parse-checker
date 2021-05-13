def wayback(url, download_function, parse_function, search_snapshot_limit=10):
    # Expects download_function(url)
    # Expects parse_function(html)
    # Expects parse_function to return True on a successful parse
    # Expects parse_function to return False on a failed parse
    import json
    from datetime import datetime

    TIMESTAMP_FORMAT = "%Y%m%d%H%M%S"
    CDX_API_URL = ("http://web.archive.org/cdx/search/cdx?"
                   "url={url}&output=json&fl=timestamp,digest&limit=-{limit}")
    SNAPSHOT_URL = "http://web.archive.org/web/{timestamp}id_/{url}"

    # search for unique snapshots
    search_url = CDX_API_URL.format(url=url, limit=search_snapshot_limit)
    search_json = download_function(search_url)
    snapshots = json.loads(search_json)
    snapshots.pop(0)  # remove cdx format line
    previous_digest = None
    snapshot_timestamps = []
    for snapshot in snapshots:
        timestamp = snapshot[0]
        digest = snapshot[1]
        # skip download if identical to previous snapshot
        if digest == previous_digest:
            continue
        snapshot_timestamps.append(timestamp)
        previous_digest = digest
    print("Found", len(snapshot_timestamps), "unique snapshots")

    # download and test snapshots
    for timestamp in snapshot_timestamps:
        timestamp_readable = datetime.strptime(timestamp, TIMESTAMP_FORMAT)
        print("Downloading snapshot from", timestamp_readable)
        snapshot_url = SNAPSHOT_URL.format(timestamp=timestamp, url=url)
        snapshot_html = download_function(snapshot_url)
        parse_result = parse_function(snapshot_html)
        if parse_result:
            print("Parsed successfully!")
        else:
            print("Parse failed. Saving locally as", timestamp + ".html")
            with open(timestamp + ".html", 'w') as f:
                f.write(snapshot_html)
