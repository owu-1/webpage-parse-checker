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
        "date_filter": 5,  # an int describing the number of days before the current time
                           # or a string describing date in form of yyyyMMddhhmmss

        "parse_function": parse_function  # expects a function that takes html as its only parameter
                                          # and returns True on a successful parse
                                          # or False on a failed parse
    },
    # ...
}
```
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

wayback(SOURCES, download)
```
