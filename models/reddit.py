#! /usr/bin/env python3
##
# RedditNewsPostBot Reddit Model
# By Amos (LFlare) Ng
##
# Import dependencies
import praw
import re
import sys
import time

# Import exceptions
from models.exceptions import *


class Reddit():
    reddit = None

    def __init__(self, configuration):
        self.login(configuration)

    def login(self, configuration):
        credentials = configuration.get_credentials()
        user_agent = configuration.get_user_agent()
        reddit = praw.Reddit(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            username=credentials["username"],
            password=credentials["password"],
            user_agent=user_agent
        )

        if reddit.user.me() == credentials["username"]:
            self.reddit = reddit
            return True
        else:
            raise Exception("LoginException")

    def is_commented(self, object):
        comments = []
        if isinstance(object, praw.models.Submission):
            comments = object.comments
        elif isinstance(object, praw.models.Comment):
            comments = object.replies

        for top_level_comment in comments:
            if isinstance(top_level_comment, praw.models.MoreComments):
                continue
            if (top_level_comment.author == self.reddit.user.me()
                    and top_level_comment.banned_by == None):
                return True
        return False

    def post_reply(self, parent, reply_comment):
        while True:
            try:
                if not self.is_commented(parent):
                    child_comment = parent.reply(reply_comment)
                    print("Posted %s" % child_comment)
                    return child_comment
            except praw.exceptions.APIException as e:
                if "try again in" in e.message:
                    try:
                        sleep_time = (int(
                            re.search("([0-9]+) minute", e.message).group(1))
                            * 60)
                    except AttributeError:
                        sleep_time = int(
                            re.search("([0-9]+) second", e.message).group(1))
                    except AttributeError:
                        sleep_time = 600  # Default to 10 minutes cooldown
                    else:
                        while sleep_time > 0:
                            print("API limit hit, sleeping for %d...  " %
                                  sleep_time, end="\r")
                            time.sleep(1)
                            sleep_time -= 1

    def stream_subreddit(self, subreddit, submission_queue, supported_sites):
        stream = self.reddit.subreddit(subreddit).stream.submissions()
        for submission in stream:
            if any(site in submission.url for site in supported_sites):
                if not self.is_commented(submission):
                    print("Queueing [%s](%s)" %
                          (submission.id, submission.url))
                    submission_queue.put(submission)
                else:
                    print("Skipping [%s](%s)" %
                          (submission.id, submission.url))
