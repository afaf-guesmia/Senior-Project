from flask import Flask, request, jsonify
from search import search
from filter import Filter
from storage import DBStorage
import html
import requests

app = Flask(__name__)
styles = """
<style>
    body {
        background-image: url("https://rare-gallery.com/mocahbig/1363018-Clean-wallpaper.jpg");
    }
    .site, .snippet, .rel-button {
    .site, .snippet {
        width: 50%;
        background-color: lightgray;
        padding: 20px;
@@ -22,6 +22,16 @@
        transition: transform 0.3s ease-in-out;
    }
   a:link {
        color: yellow;
        background-color: transparent;
        text-decoration: none;
    }
    a:visited {
        color: white;
        background-color: transparent;
        text-decoration: none;
    }
    .site:hover, .snippet:hover, .rel-button:hover {
        transform: translateY(-10px);
    }
@@ -30,17 +40,25 @@
        font-size: .8rem;
        color: green;
    }

    .snippet {
        font-size: .9rem;
        color: gray;
        margin-bottom: 30px;
    }
    .rel-button {
        cursor: pointer;
        width: 50%;
        background-color: lightgray;
        color: blue;
        padding: 1px;
        box-sizing: border-box;
        margin: 0px 0 0px 20px;
        border-radius: 0px;
        transition: transform 0.3s ease-in-out;
        cursor: pointer;
    }

    input[type="text"] {
        padding: 10px;
@@ -65,6 +83,21 @@
        cursor: pointer;
    }
</style>
<script>
const relevant = function(query, link){
    fetch("/relevant", {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
           "query": query,
           "link": link
          })
        });
}
</script>
"""

search_template = styles + """
<html>
  <head>
  </head>
  <body>
    <form action="/" method="post">
      <input type="text" name="query" placeholder="Enter Search Here">
      <input type="submit" value="Search">
    </form>
  </body>
</html>
"""
result_template = """
<p class="site">{rank}: {link} <span class="rel-button" onclick='relevant("{query}", "{link}");'>Relevant</span></p>
<a href="{link}">{title}</a>
<p class="snippet">{snippet}</p>
<div class="related">
<h2>Related Keywords:</h2>
<ul>
{related}
</ul>
</div>
"""


def show_search_form():
    return search_template


def run_search(query):
    results = search(query)
    fi = Filter(results)
    filtered = fi.filter()
    rendered = search_template
    filtered["snippet"] = filtered["snippet"].apply(lambda x: html.escape(x))
    for index, row in filtered.iterrows():
        related = get_related_keywords(row["title"])
        related_html = ""
        for keyword in related:
            related_html += f"<li>{keyword}</li>"
        row["related"] = related_html
        rendered += result_template.format(**row)
    return rendered


@app.route("/", methods=['GET', 'POST'])
def search_form():
    if request.method == 'POST':
        query = request.form["query"]
        return run_search(query)
    else:
        return show_search_form()


@app.route("/relevant", methods=["POST"])
def mark_relevant():
    data = request.get_json()
    query = data["query"]
    link = data["link"]
    storage = DBStorage()
    storage.update_relevance(query, link, 10)
    return jsonify(success=True)


def get_related_keywords(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "cx": "66244c6da00bd48d6",
        "key": "AIzaSyD83Zli76Hqhqf1xN690Pgh9m2uRtJAdno",
        "num": 5,
        "fields": "items(title)"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json()["items"]
        return [result["title"] for result in results]
    else:
        return []