# webpage-parse-checker
Generate robust parsing code for webpages

<b>Warning - A directory named snapshot_cache will be created in the current directory</b>

<b>Warning - Remember to remove the function and the snapshot_cache folder for submission</b>
## How to use
Copy and paste the wayback function into your solution, then call the function with source infomation and your download function. Importing the function from a file is not suggested (if you forget to remove the import in the submission, no one is gonna be happy)
```python
def wayback(sources, download_function):
```

<b>sources</b> expects a dictonary containing source infomation in this format:
```python
{
    "source_name": {
        "url": "http://...",
        "snapshot_search_limit": 10,  # a number greater or equal to 0
        "parse_function": parse_function
    },
    # ...
}
```
The snapshot search limit controls the amount of snapshots searched for with the wayback api. It has to be greater or equal to 0. The amount of snapshots searched for may not equal the amount of snapshots downloaded as non-unique snapshots are rejected.

Set the snapshot search limit to 0 to skip the snapshot search and use only cached web-pages

parse_function expects a function that takes html as its only parameter and returns True on a successful parse or False on a failed parse

<b>download_function</b> expects a function that takes a url as its only parameter and returns html


## Example
```python
def download(url):
    # download logic
    return html

def nine_news_parse(html):
    # parse logic
    # print parsed infomation, print errors
    if parse_success:
        return True
    else:
        return False

# ...similar parse functions for remaining sources

SOURCES = {
    "Nine News": {
        "url": "https://www.9news.com.au/politics",
        "snapshot_search_limit": 10,
        "parse_function": nine_news_parse
    },
    "Brisbane Times": {
        "url": "https://www.brisbanetimes.com.au/politics/federal",
        "snapshot_search_limit": 10,
        "parse_function": brisbane_times_parse
    },
    "ABC News": {
        "url": "https://abc.net.au/news/politics",
        "snapshot_search_limit": 10,
        "parse_function": abc_news_parse
    },
    "Financial Review": {
        "url": "https://afr.com/politics",
        "snapshot_search_limit": 10,
        "parse_function": financial_review_parse
    }
}

wayback(SOURCES, download)
```
