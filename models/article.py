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

        # Replace "img" and "a" with markdown
        article_soup = BeautifulSoup(article_html, "html.parser")
        article_html = self.replace_markdown(article_soup)

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
        return soup.prettify()

    def replace_markdown_a(self, a):
        a_href = "#"
        a_desc = ": "
        replacement = ""

        # Try checking if link contains an image
        if a.img:
            replacement += self.replace_markdown_img(
                a.img, linked=True) + "\n\n"
            a_desc = " OF IMAGE ABOVE"
        else:
            try:
                a_desc += a.text.strip()
            except:
                raise

        # Try replacing link meta
        try:
            a_href = a["href"]
            if a_href.startswith("/"):
                a_href = self.domain + a_href
            elif not (a_href.startswith("http")
                      or a_href.startswith("ftp")):
                a_href = self.domain + "/" + a_href
        except:
            raise

        replacement += "[LINK%s](%s)\n\n" % (a_desc, a_href)
        return replacement

    def replace_markdown_img(self, img, linked=False):
        img_src = "#"
        img_alt = ": "

        # Try parsing src of img
        try:
            img_src = img["src"]
            if img_src.startswith("/"):
                img_src = self.domain + img_src
            elif not (img_src.startswith("http")
                      or img_src.startswith("ftp")):
                img_src = self.domain + "/" + img_src
        except (KeyError, TypeError):
            return ""

        # Try getting img alt else default empty
        try:
            img_alt = img["alt"]
        except KeyError:
            img_alt = ""

        # Strip img alt
        img_alt = img_alt.strip()

        replacement = "[IMAGE%s](%s)\n\n" % (img_alt, img_src)
        return replacement

    def replace_markdown(self, soup):
        # Parse links to markdown
        for a in soup("a"):
            replacement = self.replace_markdown_a(a)
            a.replace_with(replacement)

        # Parse images to markdown
        for img in soup("img"):
            replacement = self.replace_markdown_img(img)
            img.replace_with(replacement)

        return soup.prettify()

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
