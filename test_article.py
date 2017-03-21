#! /usr/bin/env python3
##
# RedditNewsPostBot Article Tester
# By Amos (LFlare) Ng
##
# Import dependencies
import sys

# Import Article model
from models.article import Article


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for url in sys.argv[1:]:
            article_text = Article(url=url).get_article_text()
            print(article_text)
    else:
        print("%s [url] [url] [url]" % sys.argv[0])