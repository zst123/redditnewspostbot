#! /usr/bin/env python3
##
# RedditNewsPostBot Credentials Model
# By Amos (LFlare) Ng
##
# Import dependencies
import json
import re

# Import exceptions
from models.exceptions import *


class Configuration():
    configuration = None

    def __init__(self, configuration_file="config.json"):
        try:
            configuration = open(configuration_file, "r").read()
            parsed_configuration = re.sub(r"// .*\n", r"\n", configuration)
            self.configuration = json.loads(parsed_configuration)
        except:
            raise ConfigurationException(
                "Configuration invalid, please check json syntax!")

    def get_credentials(self):
        return self.configuration["credentials"]

    def get_user_agent(self):
        return self.configuration["user_agent"]

    def get_supported_sites(self):
        return self.configuration["supported_sites"]

    def get_comment_template(self):
        return self.configuration["comment_template"]
