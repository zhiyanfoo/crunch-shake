import os
import sys

import re
import json
from collections import Counter

file_dir = os.path.dirname(os.path.abspath(__file__))

PLAY_PATH = os.path.abspath(sys.argv[1])
PLAY_NAME = PLAY_PATH[:-4]
META_INPUT_PATH = PLAY_NAME + "_in.json"
META_OUTPUT_PATH = PLAY_NAME +"_out.json"

def file_to_list(path):
    with open(path, 'r') as inputFile:
        return inputFile.readlines()

def json_file_to_dict(path):
    with open(path, 'r') as jsonFile:
        return json.load(jsonFile)

def to_json(x, path):
    with open(path, 'w') as jsonFile:
        return json.dump(x, jsonFile)

def reduce_play_lines(play_lines, meta_dict):
    return play_lines[meta_dict['start_line'] - 1: meta_dict['end_line']]

def get_files():
    play_lines_extended = file_to_list(PLAY_PATH)
    meta_dict = json_file_to_dict(META_INPUT_PATH)
    play_lines = reduce_play_lines(play_lines_extended, meta_dict)
    return play_lines, meta_dict

def get_character_chain(play_lines):
    return [ matched_line.group('name') for matched_line in
            ( find_dialogue(line) for line in play_lines)
            if matched_line is not None
            ]

def find_dialogue(line):
    pattern = r"^  (?P<name>[A-Z]+)\."
    return re.search(pattern, line)

def process_play(play_lines, meta_dict):
    character_chain = get_character_chain(play_lines)
    character_count = dict(Counter(character_chain))
    output_dict = {
            "character_chain" : character_chain,
            "character_count" : character_count
            }
    return output_dict

def main():
    play_lines, meta_dict = get_files()
    output_dict = process_play(play_lines, meta_dict)
    to_json(output_dict, META_OUTPUT_PATH)

if __name__ == "__main__":
    main()
