import json
import re
from collections import namedtuple

# INPUT OUTPUT

def file_to_list(path):
    with open(path, 'r') as inputFile:
        return inputFile.readlines()

def json_file_to_dict(path):
    with open(path, 'r') as jsonFile:
        return json.load(jsonFile)

def to_json(x, path):
    with open(path, 'w') as jsonFile:
        json.dump(x, jsonFile)

def list_to_file(li, path):
    with open(path, 'w') as outputFile:
        outputFile.writelines(li)

# MATCHERS

def get_matcher(words, identifier):
    joined_words = "|".join(words)
    pattern = "(?P<{0}>".format(identifier) + joined_words + ")"
    matcher = re.compile(
            pattern,
            re.IGNORECASE)
    return matcher

Matcher = namedtuple('Matcher', ['dialogue', 'character', 'stage_direction',
    'instruction', 'act', 'scene'])
