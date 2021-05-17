# webpage-parse-checker
Generate robust parsing code for webpages

<b>Warning - Remember to remove the code and the snapshot_cache folder for submission</b>

This code will test your parse logic against previous versions of a web-page. It also supports warning and displaying to users what parsed data has changed from the previous attempt, and cycling through and displaying on the GUI the changed parsed data

Note: A directory named snapshot_cache will be created in the current directory

## How to use
Either copy and paste the code into your own file, or import Wayback from a file. Importing is better imo
```python
# Under the class Wayback
def parse_check(sources, download_function):
```

<b>sources</b> expects a dictonary containing source infomation in this format:
```python
{
    "source_name": {
        "url": "http://...",
        "date_filter": 5,  # an int describing the number of days before the current time
                           # or a string describing date in form of yyyyMMddhhmmss

        "parse_function": parse_function  # expects a function that takes html as its only parameter
                                          # and returns True or a dictonary of parsed data on a successful parse
                                          # or False on a failed parse
    },
    # ...
}
```
If parse_function returns a dictonary of parsed data, the data will be saved in snapshot_cache/parse_results.json. This enables result comparison which warns if different results were found compared to the previous results. Result diff can be viewed using http://www.jsondiff.com/. Save the original parse_results.json file somewhere else as future runs will overwrite it

<b>download_function</b> expects a function that takes a url as its only parameter and returns html

<b>parse_check</b> returns a Wayback object which contains parsed data and timestamps where results were different from before. Use its set_gui_display_function method to set a function which will edit the gui based on parsed data. Use the toggle method to execute the supplied gui edit function with parsed data as its only parameter.

## Example
```python
def download(url):
    # download logic
    return html

def nine_news_parse(html):
    # parse logic
    # print parsed infomation, print errors
    if parse_success:
        return True  # or return { "headline": headline, ... }
    else:
        return False

# ...similar parse functions for remaining sources

SOURCES = {
    "Nine News": {
        "url": "https://www.9news.com.au/politics",
        "date_filter": 30,  # search for snapshots 30 days from current date
        "parse_function": nine_news_parse
    },
    "Brisbane Times": {
        "url": "https://www.brisbanetimes.com.au/politics/federal",
        "date_filter": "202105",
        "parse_function": brisbane_times_parse
    },
    "ABC News": {
        "url": "https://abc.net.au/news/politics",
        "date_filter": "20210513",
        "parse_function": abc_news_parse
    },
    "Financial Review": {
        "url": "https://afr.com/politics",
        "date_filter": "20210513211838",
        "parse_function": financial_review_parse
    }
}

# Without displaying data on GUI
Wayback.parse_check(SOURCES, download)

# With displaying data on GUI
def change_gui(parsed_data):
    headline_label["text"] = parsed_data["headline"]
    # ...
wayback = Wayback.parse_check(SOURCES, download)
wayback.set_gui_display_function(change_gui)
button["command"] = wayback.toggle  # bind the wayback object's toggle method to button
```
