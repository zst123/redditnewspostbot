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
    article_html = ""
    article_text = ""
    debug = False
    domain = ""
    url = ""

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

        # Save url
        self.url = url

        # Process article
        page_soup = BeautifulSoup(page.text, "html.parser")
        article_soup = page_soup.select_one(settings["content_selector"])
        if article_soup is None:
            return

        # Convert all URLs to static global URLs
        article_soup = self.replace_url(article_soup)

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

    def replace_url(self, soup):
        for a in soup.find_all("a"):
            try:
                a_href = a["href"]
                if a_href.startswith("/"):
                    a_href = self.domain + a_href
                elif a_href.startswith("#"):
                    a_href = self.url + a_href
                elif not (a_href.startswith("http")
                          or a_href.startswith("ftp")):
                    a_href = self.domain + "/" + a_href
                a["href"] = a_href
            except:
                pass
        for img in soup.find_all("img"):
            try:
                img_src = img["src"]
                if img_src.startswith("/"):
                    img_src = self.domain + img_src
                elif img_src.startswith("#"):
                    img_src = self.url + img_src
                elif not (img_src.startswith("http")
                          or img_src.startswith("ftp")):
                    img_src = self.domain + "/" + img_src
                img["src"] = img_src
            except:
                pass
        return soup

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
        # Strip every line to prevent additional spaces
        text = "\n".join([line.strip() for line in text.split("\n")])
        # Replace link markdown generated by html2text with normal markdown
        text = re.sub(
            r"(?<!!)\[(.+)\]\((.*)\)", "[[LINK: \\1]](\\2)\n\n", text)
        # Replace image markdown generated by html2text with normal markdown
        text = re.sub(r"!\[(.+)\]\((.*)\)", "[[\\1]](\\2)\n\n", text)
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
