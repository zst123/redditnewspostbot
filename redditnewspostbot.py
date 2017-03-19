#! /usr/bin/env python3
##
# RedditNewsPostBot
# By Amos (LFlare) Ng
##
# Import dependencies
import json
import os
import praw
import queue
import re
import requests
import signal
import sys
import time
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from threading import Thread

# Import models
from models.article import Article
from models.configuration import Configuration
from models.reddit import Reddit


class RedditNewsPostBot:
    # Object variables
    debug = True
    reddit = None
    configuration = None
    active_threads = []
    submission_queue = queue.Queue()

    def __init__(self):
        print(
            "RNPB started in",
            "debug" if self.debug else "standard",
            "mode")
        # Don't print stacktrace on ctrl-c
        signal.signal(signal.SIGINT, lambda x, y: sys.exit(0))
        self.configuration = Configuration()
        self.reddit = Reddit(self.configuration)

    def start(self):
        queue_handler_thread = Thread(target=self.queue_handler)
        queue_handler_thread.daemon = True
        queue_handler_thread.start()
        self.active_threads.append(queue_handler_thread)
        self.reddit.stream_subreddit(
            subreddit="singapore",
            submission_queue=self.submission_queue,
            supported_sites=self.configuration.get_supported_sites())

    def reply_article(self, submission, article):
        article_lines = article.split("\n")
        article_parts = []
        article_part = ""

        i = 0
        while i < len(article_lines):
            article_part += "> " + article_lines[i] + "\n"
            i += 1
            if len(article_part) >= 5000:
                article_parts.append(article_part)
                article_part = ""
        article_parts.append(article_part)

        i = 0
        parent = submission
        for article_part in article_parts:
            comment_part_header = ""
            if len(article_parts) != 1:
                comment_part_header = "Part [%d/%d]\n" % (
                    i+1, len(article_parts))
            reply_comment = self.configuration.get_comment_template().format(
                comment_part_header, article_part, submission.shortlink)

            print("Posting [%s]" % submission.id)
            if self.debug:
                print(reply_comment)
            parent = self.reddit.post_reply(parent, reply_comment)
            i += 1

    def queue_handler(self):
        while True:
            submission = self.submission_queue.get()
            article = None
            print("Attempting [%s](%s)" % (submission.id, submission.url))

            supported_sites = self.configuration.get_supported_sites().items()
            site = ((site, settings) for (site, settings)
                    in supported_sites if site in submission.url).__next__()

            if site:
                article = Article(
                    submission.url, self.configuration, debug=self.debug
                ).get_article_text()
                if article != "":
                    self.reply_article(submission, article)
                else:
                    print("Empty [%s](%s)" % (submission.id, submission.url))

            print("Sleeping for 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    redditnewspostbot = RedditNewsPostBot()
    redditnewspostbot.start()
