import json
from datetime import datetime, timedelta
import os
import re


class Wayback:
    CACHE_LOCATION = "snapshot_cache"
    SETTINGS_LOCATION = f"{CACHE_LOCATION}/settings.json"
    PARSE_RESULTS_LOCATION = f"{CACHE_LOCATION}/parse_results.json"

    def __init__(self, results, changes):
        self.results = results
        self.changes = iter(changes)

    @staticmethod
    def parse_check(sources, download_function):
        # open settings file
        if os.path.isfile(Wayback.SETTINGS_LOCATION):
            with open(Wayback.SETTINGS_LOCATION) as f:
                settings = json.load(f)
            # create source entry if it doesn't exist
            for source_name in sources:
                if not settings.get(source_name):
                    settings[source_name] = {}
        else:
            settings = {source_name: {} for source_name in sources}
        # open previous parse results file
        if os.path.isfile(Wayback.PARSE_RESULTS_LOCATION):
            with open(Wayback.PARSE_RESULTS_LOCATION) as f:
                all_previous_results = json.load(f)
        else:
            all_previous_results = None

        current_date = datetime.now()
        all_results = {}
        all_fails = {}
        all_changes = Changes()
        for source_name, source_data in sources.items():
            source = Source(source_name, source_data, current_date)
            timestamps = source.download_snapshots(
                download_function, settings, current_date)
            results, fails, changes = source.parse_snapshots(
                timestamps,
                all_previous_results)
            all_results[source_name] = results
            all_fails[source_name] = fails
            all_changes = all_changes + changes

        # update date filter setting
        with open(Wayback.SETTINGS_LOCATION, 'w') as f:
            json.dump(settings, f)

        # save parse results
        with open(Wayback.PARSE_RESULTS_LOCATION, 'w') as f:
            json.dump(all_results, f)

        # overviews
        for source_name in sources:
            fails = all_fails[source_name]
            changes = all_changes[source_name]
            print("-----", source_name, "-----")
            print(source_name, "had", len(fails), "parse fails")
            if fails:
                print("Parse fails occured in snapshots from:", *fails)
            if len(changes):
                print(source_name, "had", len(changes),
                      "different results to previous results")
                print("Changes occured in snapshots from",
                      *changes)

        return Wayback(all_results, all_changes)

    # todo: remove and put somewhere else
    def set_gui_display_function(self, gui_function):
        self.gui_function = gui_function

    # view results on GUI
    def toggle(self):
        try:
            change = next(self.changes)
            # todo: abstract this
            source_name = change[0]
            timestamp = change[1]
        except StopIteration:
            print("No more changes")
            return
        print("Showing change for", source_name, "at", timestamp)
        change_result = self.results[source_name][timestamp]
        self.gui_function(change_result)


class Changes:
    def __init__(self, changes=[]):
        self.changes = changes

    def __add__(self, other):
        return Changes(self.changes + other.changes)

    def __getitem__(self, source_name):
        source_changes = []
        for change in self.changes:
            if change[0] == source_name:
                source_changes.append(change[1])
        return source_changes

    def __iter__(self):
        return iter(self.changes)

    def append(self, source_name, timestamp):
        change = [source_name, timestamp]
        self.changes.append(change)


class Source:
    TIMESTAMP_FORMAT = "%Y%m%d%H%M%S"
    CACHE_TIME = timedelta(hours=1)
    CACHE_REGEX = re.compile(r"^(\d{14})\.html$")
    SNAPSHOT_URL = "http://web.archive.org/web/{timestamp}id_/{url}"
    CDX_API_URL = (
        "http://web.archive.org/cdx/search/cdx?"
        "output=json&"  # return in json form
        "fl=timestamp&"  # only return timestamps
        "collapse=digest&"  # only show unique captures
        "filter=statuscode:200&"  # only return pages without errors
        "url={url}&"
        "from={date_filter}&"
        "to={current_date}")

    def __init__(self, name, data, current_date):
        self.name = name
        self.url = data["url"]
        self.parse_function = data["parse_function"]

        date_filter = data["date_filter"]
        # use day offset if integer, or wayback date format if string
        if isinstance(date_filter, int):
            self.date_filter = \
                current_date - timedelta(days=date_filter)
        else:
            self.date_filter = datetime.strptime(date_filter,
                                                 self.TIMESTAMP_FORMAT)
        # create source cache directories
        self.cache_dir = f"{Wayback.CACHE_LOCATION}/{self.name}"
        os.makedirs(self.cache_dir, exist_ok=True)

    def download_snapshots(self, download_function,
                           settings, current_date):
        # check if snapshots are cached
        oldest_date_filter_str = settings[self.name].get("date_filter")
        downloaded_date_str = \
            settings[self.name].get("downloaded_date")
        if oldest_date_filter_str and downloaded_date_str:
            oldest_date_filter = datetime.strptime(
                oldest_date_filter_str, self.TIMESTAMP_FORMAT)
            downloaded_date = datetime.strptime(
                downloaded_date_str, self.TIMESTAMP_FORMAT)
            cache_contains_snapshots = \
                oldest_date_filter <= self.date_filter
            cache_is_outdated = \
                (current_date - downloaded_date) > self.CACHE_TIME
            if cache_contains_snapshots and not cache_is_outdated:
                # use cached snapshots
                cache_file_names = os.listdir(self.cache_dir)
                timestamps = []
                for cache_file_name in cache_file_names:
                    match = self.CACHE_REGEX.match(cache_file_name)
                    if match:
                        timestamp = match[1]
                        timestamps.append(timestamp)
                print("Found", len(timestamps),
                      "snapshots cached for", self.name)
                return timestamps

        # retrive timestamps
        search_url = self.CDX_API_URL.format(
            url=self.url,
            date_filter=self.date_filter.strftime(self.TIMESTAMP_FORMAT),
            current_date=current_date.strftime(self.TIMESTAMP_FORMAT)
        )
        search_json = download_function(search_url)
        snapshots = json.loads(search_json)
        if not snapshots:
            print("No snapshots found for", self.name)
            return []
        snapshots.pop(0)  # remove cdx format line
        timestamps = set()  # multiple snapshots occur at one timestamp
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
                      datetime.strptime(timestamp, self.TIMESTAMP_FORMAT))
                snapshot_url = self.SNAPSHOT_URL.format(
                    timestamp=timestamp,
                    url=self.url)
                snapshot_html = download_function(snapshot_url)
                # cache snapshot
                with open(snapshot_location, 'w', encoding="utf-8") as f:
                    f.write(snapshot_html)
        settings[self.name]["date_filter"] = \
            self.date_filter.strftime(self.TIMESTAMP_FORMAT)
        settings[self.name]["downloaded_date"] = \
            current_date.strftime(self.TIMESTAMP_FORMAT)
        return timestamps

    def parse_snapshots(self, timestamps, all_previous_results):
        if all_previous_results:
            previous_results = all_previous_results[self.name]
        else:
            previous_results = {}

        results = {}
        fails = []
        changes = Changes()
        for timestamp in timestamps:
            snapshot_location = f"{self.cache_dir}/{timestamp}.html"
            with open(snapshot_location) as f:
                snapshot_html = f.read()
            result = self.parse_function(snapshot_html)
            if result:
                # successful parse
                if isinstance(result, dict):
                    results[timestamp] = result
                    # don't check if previously failed
                    previous_result = previous_results.get(timestamp)
                    if (result != previous_result):
                        changes.append(self.name, timestamp)
                else:
                    results[timestamp] = None
            else:
                # failed parse
                fails.append(timestamp)
        return (results, fails, changes)
