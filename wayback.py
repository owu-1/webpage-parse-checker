def wayback(sources, download_function):
    import json
    from datetime import datetime, timedelta
    import os
    import re
    from pprint import pprint

    CACHE_LOCATION = "snapshot_cache"
    CACHE_REGEX = re.compile(r"^(\d{14})\.html$")
    SETTINGS_LOCATION = f"{CACHE_LOCATION}/settings.json"
    PARSE_RESULTS_LOCATION = f"{CACHE_LOCATION}/parse_results.json"
    CACHE_TIME = timedelta(hours=1)
    TIMESTAMP_FORMAT = "%Y%m%d%H%M%S"
    CDX_API_URL = ("http://web.archive.org/cdx/search/cdx?"
                   "output=json&"  # return in json form
                   "fl=timestamp&"  # only return timestamps
                   "collapse=digest&"  # only show unique captures
                   "filter=statuscode:200&"  # only return pages without errors
                   "url={url}&"
                   "from={requested_date}&"
                   "to={current_date}")
    SNAPSHOT_URL = "http://web.archive.org/web/{timestamp}id_/{url}"

    # open settings file
    if os.path.isfile(SETTINGS_LOCATION):
        with open(SETTINGS_LOCATION) as f:
            settings = json.load(f)
        # create source entry if it doesn't exist
        for source_name in sources:
            if not settings.get(source_name):
                settings[source_name] = {}
    else:
        settings = {source_name: {} for source_name in sources}
    # open previous parse results file
    if os.path.isfile(PARSE_RESULTS_LOCATION):
        with open(PARSE_RESULTS_LOCATION) as f:
            previous_parse_results = json.load(f)
    else:
        previous_parse_results = None

    current_date = datetime.now()
    current_date_str = current_date.strftime(TIMESTAMP_FORMAT)
    parse_fail_timestamps = {}
    parse_results = {}
    for source_name, source_data in sources.items():
        url = source_data["url"]
        date_filter = source_data["date_filter"]
        # create source cache directory
        source_cache_dir = f"{CACHE_LOCATION}/{source_name}"
        os.makedirs(source_cache_dir, exist_ok=True)
        # use day offset if integer, or wayback date format if string
        if isinstance(date_filter, int):
            requested_date = current_date - timedelta(days=date_filter)
            requested_date_str = requested_date.strftime(TIMESTAMP_FORMAT)
        else:
            requested_date = datetime.strptime(date_filter, TIMESTAMP_FORMAT)
            requested_date_str = date_filter

        # check settings
        oldest_date_filter_str = settings[source_name].get("date_filter")
        if oldest_date_filter_str:
            oldest_date_filter = datetime.strptime(oldest_date_filter_str,
                                                   TIMESTAMP_FORMAT)
            if (oldest_date_filter - requested_date) < CACHE_TIME:
                search = False
            else:
                search = True
        else:
            search = True

        # retrive timestamps
        timestamps = set()  # multiple snapshots can occur at one timestamp
        if search:
            # search for unique snapshots
            search_url = CDX_API_URL.format(
                url=url,
                requested_date=requested_date_str,
                current_date=current_date_str)
            search_json = download_function(search_url)
            snapshots = json.loads(search_json)
            snapshots.pop(0)  # remove cdx format line

            for snapshot in snapshots:
                timestamp = snapshot[0]
                timestamps.add(timestamp)
            print("Found", len(timestamps),
                  "unique snapshots for", source_name)

            # download and cache snapshots
            for timestamp in timestamps:
                snapshot_location = f"{source_cache_dir}/{timestamp}.html"
                timestamp_readable = datetime.strptime(timestamp,
                                                       TIMESTAMP_FORMAT)
                if os.path.isfile(snapshot_location):
                    continue
                else:
                    print("Downloading snapshot from", timestamp_readable)
                    snapshot_url = SNAPSHOT_URL.format(
                        timestamp=timestamp,
                        url=url)
                    snapshot_html = download_function(snapshot_url)
                    # cache snapshot
                    with open(snapshot_location, 'w') as f:
                        f.write(snapshot_html)
        else:
            # use cached snapshots
            cache_file_names = os.listdir(source_cache_dir)
            for cache_file_name in cache_file_names:
                match = CACHE_REGEX.match(cache_file_name)
                if match:
                    timestamp = match[1]
                    timestamps.add(timestamp)
            print("Found", len(timestamps),
                  "snapshots cached for", source_name)

        # test snapshots
        source_parse_results = {}
        if previous_parse_results:
            previous_source_parse_results = previous_parse_results[source_name]
        parse_fail_timestamps[source_name] = []
        fails = parse_fail_timestamps[source_name]
        for timestamp in timestamps:
            snapshot_location = f"{source_cache_dir}/{timestamp}.html"
            with open(snapshot_location) as f:
                snapshot_html = f.read()
            parse_result = source_data["parse_function"](snapshot_html)
            if parse_result:
                print("Parsed successfully!")
                if isinstance(parse_result, dict):
                    source_parse_results[timestamp] = parse_result
                    if previous_parse_results:
                        previous_parse_result = \
                            previous_source_parse_results.get(timestamp)
                        if (previous_parse_result and
                                not parse_result == previous_parse_result):
                            print("Parse result is different "
                                  "from previous result for", timestamp)
                            print("Previous:")
                            pprint(previous_parse_result)
                            print("Current:")
                            pprint(parse_result)
                else:
                    source_parse_results[timestamp] = None
            else:
                print("Parse failed.")
                fails.append(timestamp)

        # update parse results
        parse_results[source_name] = source_parse_results

        # update date filter setting
        if search:
            settings[source_name]["date_filter"] = requested_date_str
            with open(SETTINGS_LOCATION, 'w') as f:
                json.dump(settings, f)

    # save parse results
    with open(PARSE_RESULTS_LOCATION, 'w') as f:
        json.dump(parse_results, f)

    # failed parses overview
    for source_name, timestamps in parse_fail_timestamps.items():
        print(source_name, "had", len(timestamps), "parse fails")
        if timestamps:
            print("Parse fails occured in snapshots from:", *timestamps)
