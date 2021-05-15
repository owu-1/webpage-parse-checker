def wayback(sources, download_function):
    import json
    from datetime import datetime, timedelta
    import os
    import re

    CACHE_LOCATION = "snapshot_cache"
    CACHE_REGEX = re.compile(r"^(\d{14})\.html$")
    SETTINGS_LOCATION = f"{CACHE_LOCATION}/settings.json"
    PARSE_RESULTS_LOCATION = f"{CACHE_LOCATION}/parse_results.json"
    CHANGES_LOCATION = f"{CACHE_LOCATION}/changes.json"
    CACHE_TIME = timedelta(hours=1)
    TIMESTAMP_FORMAT = "%Y%m%d%H%M%S"
    CDX_API_URL = ("http://web.archive.org/cdx/search/cdx?"
                   "output=json&"  # return in json form
                   "fl=timestamp&"  # only return timestamps
                   "collapse=digest&"  # only show unique captures
                   "filter=statuscode:200&"  # only return pages without errors
                   "url={url}&"
                   "from={date_filter}&"
                   "to={current_date}")
    SNAPSHOT_URL = "http://web.archive.org/web/{timestamp}id_/{url}"

    class Source:
        def __init__(self, name, data, current_date):
            self.name = name
            self.url = data["url"]
            self.parse_function = data["parse_function"]

            date_filter = data["date_filter"]
            # use day offset if integer, or wayback date format if string
            if isinstance(date_filter, int):
                self.date_filter = current_date - timedelta(days=date_filter)
            else:
                self.date_filter = datetime.strptime(date_filter,
                                                     TIMESTAMP_FORMAT)
            # create source cache directory
            self.cache_dir = f"{CACHE_LOCATION}/{self.name}"
            os.makedirs(self.cache_dir, exist_ok=True)

        def download_snapshots(self, settings, current_date):
            # check if snapshots are cached
            oldest_date_filter_str = settings[self.name].get("date_filter")
            downloaded_date_str = settings[self.name].get("downloaded_date")
            if oldest_date_filter_str and downloaded_date_str:
                oldest_date_filter = datetime.strptime(oldest_date_filter_str,
                                                       TIMESTAMP_FORMAT)
                downloaded_date = datetime.strptime(downloaded_date_str,
                                                    TIMESTAMP_FORMAT)
                cache_contains_snapshots = \
                    oldest_date_filter <= self.date_filter
                cache_is_outdated = \
                    (current_date - downloaded_date) > CACHE_TIME
                if cache_contains_snapshots and not cache_is_outdated:
                    # use cached snapshots
                    cache_file_names = os.listdir(self.cache_dir)
                    timestamps = []
                    for cache_file_name in cache_file_names:
                        match = CACHE_REGEX.match(cache_file_name)
                        if match:
                            timestamp = match[1]
                            timestamps.append(timestamp)
                    print("Found", len(timestamps),
                          "snapshots cached for", self.name)
                    return timestamps

            # retrive timestamps
            search_url = CDX_API_URL.format(
                url=self.url,
                date_filter=self.date_filter.strftime(TIMESTAMP_FORMAT),
                current_date=current_date.strftime(TIMESTAMP_FORMAT)
            )
            search_json = download_function(search_url)
            snapshots = json.loads(search_json)
            if not snapshots:
                print("No snapshots found for", self.name)
                return []
            snapshots.pop(0)  # remove cdx format line
            timestamps = set()  # multiple snapshots can occur at one timestamp
            for snapshot in snapshots:
                timestamp = snapshot[0]
                timestamps.add(timestamp)
            print("Found", len(timestamps),
                  "unique snapshots for", self.name)
            # download and cache snapshots
            for timestamp in timestamps:
                snapshot_location = f"{self.cache_dir}/{timestamp}.html"
                if os.path.isfile(snapshot_location):
                    continue
                else:
                    print("Downloading snapshot from",
                          datetime.strptime(timestamp, TIMESTAMP_FORMAT))
                    snapshot_url = SNAPSHOT_URL.format(
                        timestamp=timestamp,
                        url=self.url)
                    snapshot_html = download_function(snapshot_url)
                    # cache snapshot
                    with open(snapshot_location, 'w') as f:
                        f.write(snapshot_html)
            settings[source_name]["date_filter"] = \
                self.date_filter.strftime(TIMESTAMP_FORMAT)
            settings[source_name]["downloaded_date"] = \
                current_date.strftime(TIMESTAMP_FORMAT)
            return timestamps

        def parse_snapshots(self, timestamps, all_previous_results):
            if all_previous_results:
                previous_results = all_previous_results[self.name]
            else:
                previous_results = {}

            results = {}
            fails = []
            changes = []
            for timestamp in timestamps:
                snapshot_location = f"{self.cache_dir}/{timestamp}.html"
                with open(snapshot_location) as f:
                    snapshot_html = f.read()
                result = source_data["parse_function"](snapshot_html)
                if result:
                    # successful parse
                    if isinstance(result, dict):
                        results[timestamp] = result
                        # don't check if previously failed
                        previous_result = previous_results.get(timestamp)
                        if (previous_result and
                                not result == previous_result):
                            changes.append(timestamp)
                    else:
                        results[timestamp] = None
                else:
                    # failed parse
                    fails.append(timestamp)
            return (results, fails, changes)

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
            all_previous_results = json.load(f)
    else:
        all_previous_results = None

    current_date = datetime.now()
    all_results = {}
    all_fails = {}
    all_changes = {}
    for source_name, source_data in sources.items():
        source = Source(source_name, source_data, current_date)
        timestamps = source.download_snapshots(settings, current_date)
        results, fails, changes = source.parse_snapshots(timestamps,
                                                         all_previous_results)
        all_results[source_name] = results
        all_fails[source_name] = fails
        all_changes[source_name] = changes

    # update date filter setting
    with open(SETTINGS_LOCATION, 'w') as f:
        json.dump(settings, f)

    # save parse results
    with open(PARSE_RESULTS_LOCATION, 'w') as f:
        json.dump(all_results, f)

    # overviews
    for source_name in sources:
        fails = all_fails[source_name]
        changes = all_changes[source_name]
        print(source_name, "had", len(fails), "parse fails")
        if fails:
            print("Parse fails occured in snapshots from:", *fails)
        if changes:
            print(source_name, "had", len(changes),
                  "different results to previous results")
            print("Changes occured in snapshots from", *changes)
