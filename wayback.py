# Example usage:
# def download(url):
#   # download logic
#   return html

# def parse(html):
#   # parse logic
#   # print parsed infomation, print errors

# URL = "https://www.google.com/"
# wayback(URL, download, parse, 5, hide_snapshot_url_on_success=True)


def wayback(url, download_function, parse_function, amount_of_snapshots=10,
            hide_snapshot_url_on_success=False):
    # Expects download function to take one parameter (url) and return HTML
    # in a format that the parse function handles,
    # and the parse function to return True for a correct parse
    # and return False for an incorrect parse
    #
    # Amount of snapshots is the amount of snapshots to test before stopping
    #
    # If extra parameters are needed for the download function,
    # wrap the download function (with needed parameters) in another function,
    # then pass that new function into wayback
    import json
    from datetime import datetime, timedelta
    TIMESTAMP_FORMAT = "%Y%m%d%H%M%S"
    SEARCH_TIME_GAP = timedelta(days=1)

    snapshot_count = 0
    previous_snapshot_datetime = None
    search_snapshot_datetime = datetime.now()
    search_snapshot_timestamp = search_snapshot_datetime.strftime(
        TIMESTAMP_FORMAT)
    while snapshot_count < amount_of_snapshots:
        # Find closest avaliable webpage archive to the date
        # https://archive.org/help/wayback_api.php
        print("Searching for the closest snapshot to",
              search_snapshot_datetime)
        wayback_api_html = download_function(
            "http://archive.org/wayback/available?url={}&timestamp={}".format(
                url, search_snapshot_timestamp))

        wayback_snapshots = json.loads(wayback_api_html)["archived_snapshots"]
        # Contains empty dict if a snapshot is not avaliable
        if wayback_snapshots:
            # Only the closest snapshot to the requested date is returned
            snapshot = wayback_snapshots["closest"]
            snapshot_timestamp = snapshot["timestamp"]
            snapshot_datetime = datetime.strptime(
                snapshot_timestamp,
                TIMESTAMP_FORMAT)

            # todo: too many skips will probably get user banned.
            #       increase search time gap incrementally
            #       and pause every so often
            if (snapshot_datetime == previous_snapshot_datetime):
                print("Already downloaded snapshot at {}. Skipping".format(
                    snapshot_datetime
                ))
                continue

            # URL might be different to what wayback expects?
            #
            # Page returned is "rendered exactly as it was archived"
            # https://webapps.stackexchange.com/a/40912
            print(f"Found snapshot at {snapshot_datetime}. Downloading...")
            if not hide_snapshot_url_on_success:
                print("Snapshot link:",
                      "http://web.archive.org/web/{}/{}".format(
                          snapshot_timestamp, url))
            # todo: cache downloaded pages.
            #       warning - might be similar to export functionality?
            snapshot_html = download_function(
                f"http://web.archive.org/web/{snapshot_timestamp}id_/{url}")
            # todo: expect and handle parse function's dictonary or bool return
            parse_result = parse_function(snapshot_html)
            if parse_result:
                print("Parse was successful!")
            else:
                if hide_snapshot_url_on_success:
                    print("Parse failed. Snapshot link:",
                          "http://web.archive.org/web/{}/{}".format(
                              snapshot_timestamp, url))
                else:
                    print("Parse failed")

            previous_snapshot_datetime = snapshot_datetime
            search_snapshot_datetime = snapshot_datetime - SEARCH_TIME_GAP
            search_snapshot_timestamp = search_snapshot_datetime.strftime(
                TIMESTAMP_FORMAT)
            snapshot_count += 1
        else:
            print("No snapshots were found")
            return
