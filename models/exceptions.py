#! /usr/bin/env python3
##
# RedditNewsPostBot Exceptions Model
# By Amos (LFlare) Ng
##


class LoginException(Exception):
    pass


class ConfigurationException(Exception):
    pass


class HTTPStatusException(Exception):
    pass


class UnknownCommentsException(Exception):
    pass
