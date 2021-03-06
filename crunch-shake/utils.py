import json
import re
from collections import namedtuple
import string

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

def str_to_file(x, path):
    with open(path, 'w') as outputFile:
        outputFile.write(x)

# MATCHERS

def get_title(raw_play_lines):
    pattern = re.compile("<title>(.*): Entire Play.*")
    for line in raw_play_lines:
        match = pattern.search(line)
        if match:
            return match.group(1)
    raise ValueError

def get_matcher(words, identifier):
    joined_words = "|".join(words)
    pattern = "(?P<{0}>".format(identifier) + joined_words + ")"
    matcher = re.compile(
            pattern,
            re.IGNORECASE)
    return matcher

Matcher = namedtuple('Matcher', ['dialogue', 'character', 'stage_direction',
    'instruction', 'act', 'scene'])

# HELPERS

def invert_dict(front_dict):
    """ Take a dict of key->values and return values->[keys] """
    back_dict = { value : [] for value in front_dict.values() }
    for key, value in front_dict.items():
        back_dict[value].append(key)
    return back_dict

def create_remove_punctuation():
    remove_punct_map = dict.fromkeys(map(ord, string.punctuation))
    def remove_punctuation(line):
        return line.translate(remove_punct_map)
    return remove_punctuation
