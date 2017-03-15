#! /usr/bin/env python3
##
# RedditNewsPostBot Article Model
# By Amos (LFlare) Ng
##
# Import dependencies
import re
import requests
import sys
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# Import exceptions
from models.exceptions import *

# Import configuration
from models.configuration import Configuration


class Article():
    article_text = ""
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

        # Process article
        page_soup = BeautifulSoup(page.text, "html.parser")
        article_soup = page_soup.select_one(settings["content_selector"])
        if article_soup is None:
            return

        article_html = self.modify_selectors(
            article_soup, settings["modifications"]).prettify()

        # Replace local regex
        article_html = self.replace_local(
            article_html, settings["replacements"])

        # Replace global regex
        article_text = BeautifulSoup(article_html, "html.parser").text
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
        return soup

    def replace_local(self, text, replacements):
        for find, replace in replacements.items():
            text = re.sub(str(find), str(replace), text, flags=re.M)
        return text

    def replace_global(self, text):
        # Remove all latin non-breaking spaces and replace with normal spaces
        text = re.sub(r"\xa0", " ", text)
        # Remove all empty newlines with white spaces
        text = "\n".join([line.strip() for line in text.split("\n")])
        # Convert newlines to double newlines
        text = re.sub(r"(?<!\n)\n(?!\n)|\n{3,}", r"\n\n", text)
        # Remove header and footer newlines
        text = text.strip()
        return text

    def get_article_text(self):
        return self.article_text

if __name__ == "__main__":
    if len(sys.argv) >= 1:
        for url in sys.argv:
            article_text = Article(url).get_article_text()
            print(article_text)
