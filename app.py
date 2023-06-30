import requests, os, json
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, send_file

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        global product_id
        product_id = request.form['product_id']
        opinions = get_product_opinions(product_id)
        opinions_len = len(opinions)
        return render_template('index.html', opinions=opinions, opinions_len=opinions_len, product_id=product_id)
    
    return render_template('index.html', opinions=None)

def get_product_opinions(product_id):
    url = f'https://www.ceneo.pl/{product_id}#tab=reviews'
    global opinions_all
    opinions_all = []
    response = requests.get(url)
    
    def get_element(ancestor, selector=None, attribute=None, return_list=False):
        try:
            if return_list:
                return [tag.get_text().strip() for tag in ancestor.select(selector)]
            if selector:
                if attribute:
                    return ancestor.select_one(selector)[attribute].strip()
                return ancestor.select_one(selector).get_text().strip()
            return ancestor[attribute]
        except (AttributeError, TypeError):
            return None

    selectors = {
        "opinion_id": (None, "data-entry-id"),
        "author": ("span.user-post__author-name",),
        "recommendation": ("span.user-post__author-recomendation > em",),
        "score": ("span.user-post__score-count",),
        "confirmed": ("div.review-pz",),
        "opinion_date": ("span.user-post__published > time:nth-child(1)", "datetime"),
        "purchase_date": ("span.user-post__published > time:nth-child(2)", "datetime"),
        "up_votes": ("span[id^='votes-yes']",),
        "down_votes": ("span[id^='votes-no']",),
        "content": ("div.user-post__text",),
        "cons": ("div.review-feature__col:has(> div.review-feature__title--negatives) > div.review-feature__item", None, True),
        "pros": ("div.review-feature__col:has(> div.review-feature__title--positives) > div.review-feature__item", None, True)
    }

    while url:
        print(url)
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)

        if response.status_code == requests.codes.ok:
            page_dom = BeautifulSoup(response.text, "html.parser")
            opinions = page_dom.select("div.js_product-review")

            for opinion in opinions:
                single_opinion = {}
                for key, value in selectors.items():
                    single_opinion[key] = get_element(opinion, *value)
                opinions_all.append(single_opinion)

            next_page_link = page_dom.select_one("a.pagination__next")
            
            if next_page_link:
                url = next_page_link["href"]
            else:
                url = None

            if url and not url.startswith("https://www.ceneo.pl"):
                url = "https://www.ceneo.pl" + url

    return opinions_all

@app.route('/save_reviews', methods=['GET'])
def save_reviews():
    if not os.path.exists("./opinions/"):
        os.mkdir("./opinions/")
    
    with open(f'./opinions/{product_id}.json', 'w', encoding='UTF-8') as file:
        json.dump(opinions_all, file, indent=4, ensure_ascii=False)

    return send_file(f'./opinions/{product_id}.json', as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)