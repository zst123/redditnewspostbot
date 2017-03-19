#! /usr/bin/env python3
##
# RedditNewsPostBot Article Model
# By Amos (LFlare) Ng
##
# Import dependencies
import re
import requests
import sys
import html2text
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from urllib.parse import urlparse

# Import exceptions
from models.exceptions import *

# Import configuration
from models.configuration import Configuration


class Article():
    article_text = ""
    article_html = ""
    domain = ""
    debug = False

    def __init__(self, url, configuration=Configuration(), debug=False):
        # Set debugging settings
        if debug:
            self.debug = debug

        # Find site settings
        supported_sites = configuration.get_supported_sites().items()
        _, settings = (
            (
                (site, settings)
                for (site, settings) in supported_sites
                if site in url
            ).__next__())

        # Attempt to retrieve page
        try:
            page = requests.get(
                url, headers={"User-Agent": UserAgent().random})
        except:
            raise HTTPStatusException(page.status_code)
        else:
            print("Retrieved [%s](%s) Length: %d" %
                  (settings["site"], url, len(page.text)))

        # Get domain name
        parsed_uri = urlparse(url)
        self.domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)

        # Process article
        page_soup = BeautifulSoup(page.text, "html.parser")
        article_soup = page_soup.select_one(settings["content_selector"])
        if article_soup is None:
            return

        # Modify specified selectors
        article_html = self.modify_selectors(
            article_soup, settings["modifications"])

        # Replace local regex
        article_html = self.replace_local(
            article_html, settings["replacements"])
        self.article_html = article_html

        # Replace html with markdown
        article_text = self.replace_markdown(article_html)

        # Replace global regex
        article_text = self.replace_global(article_text)

        # Save article text to object-scope variable
        self.article_text = article_text

        if debug:
            print(article_html)

    def modify_selectors(self, soup, modifications):
        for selector, action in modifications.items():
            for selected in soup.select(selector):
                if action == "decompose":
                    selected.decompose()
                if action == "unwrap":
                    selected.unwrap()
        return str(soup)

    def replace_local(self, text, replacements):
        for find, replace in replacements.items():
            text = re.sub(str(find), str(replace), text, flags=re.M)
        return text

    def replace_markdown(self, html):
        h2t = html2text.HTML2Text()
        h2t.body_width = 0
        h2t.default_image_alt = "IMAGE"
        return h2t.handle(html)

    def replace_global(self, text):
        # Replace link markdown generated by html2text with normal markdown
        text = re.sub(
            r"(?<!!)\[(.+)\]\((.*)\)", "[[LINK: \\1]](\\2)\n\n", text)
        # Replace image markdown generated by html2text with normal markdown
        text = re.sub(r"!\[(.+)\]\((.*)\)", "[[\\1]](\\2)\n\n", text)
        # Remove header and footer newlines
        text = text.strip()
        return text

    def get_article_text(self):
        return self.article_text

    def get_article_html(self):
        return self.article_html

if __name__ == "__main__":
    if len(sys.argv) >= 1:
        for url in sys.argv:
            article = Article(url)
            article_html = article.get_article_html()
            article_text = article.get_article_text()
            print(article_html)
            print(article_text)
