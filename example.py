from tkinter import *
# Application sets up my tkinter window
from solution import Application, download  # import my download function
from wayback import Wayback  # file named wayback.py contains wayback code

# Capture the first promo on the 'carousel' from the QUT website

def qut_parse(html):
    # Parse promo title
    matches = re.search(
        (r'<h2 id="carouselHeading1">(?P<title>.*)</h2>\n'
         r'\s+<div class = "row justify-content-between">\n'
         r'\s+<div class = "col-lg-7">(?P<description>.*)</div>'), html)
    if matches:
        result = {
            "title": matches["title"],
            "description": matches["description"]
        }
        return result
    else:
        return False


SOURCES = {
    "QUT": {
        "url": "https://www.qut.edu.au/",
        "date_filter": 5,  # snapshots from 5 days ago to now
        "parse_function": qut_parse
    }
}

wayback = Wayback.parse_check(SOURCES, download)

# tkinter setup
sources = []
root = Tk()
root.title("Example")

# from application:
# export_selection_button["command"] = wayback.toggle
app = Application(root, sources, wayback)
# from application:
# def change_gui(data):
#    title_label["text"] = data["title"]
#    description_label["text"] = data["description"]
wayback.set_gui_display_function(app.change_gui)
app.mainloop()
