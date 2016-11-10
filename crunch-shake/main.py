import os
import sys

from utils import (file_to_list, json_file_to_dict, to_json, list_to_file)
from mit_shakespeare_regex import matcher
from parse import preprocess
from process import process
from analysis import postprocess

import networkx as nx

PLAY_PATH = os.path.abspath(sys.argv[1])
HEAD_DIR = os.path.dirname(os.path.dirname(PLAY_PATH))
PLAY_NAME = os.path.basename(PLAY_PATH)[:-len('.html')]
GENDER_PATH = os.path.join(HEAD_DIR, 'gender', PLAY_NAME + ".gender")
OUTPUT_PATH = os.path.join(HEAD_DIR, 'output')
OUTPUT_PATH_BASE = os.path.join(OUTPUT_PATH, PLAY_NAME)

# INPUT OUTPUT

def to_output(parsed_play):
    play_lines, graph = parsed_play
    a = [ str(x) + "\n" for x in play_lines ]
    print("writing to", OUTPUT_PATH)
    list_to_file(a, OUTPUT_PATH_BASE + '.out')
    dot_graph = nx.nx_agraph.to_agraph(graph)
    dot_graph.write(OUTPUT_PATH_BASE + ".dot")
    prog = ['dot', 'circo']
    for p in prog:
        dot_graph.layout(p)
        dot_graph.draw(OUTPUT_PATH_BASE + "_" + p + ".png")

def get_files():
    play_lines_raw = file_to_list(PLAY_PATH)
    try:
        gender = json_file_to_dict(GENDER_PATH)
    except FileNotFoundError:
        print("require gender file")
        gender = None
    return play_lines_raw, gender

def process_play(raw_play_lines, gender):
    speaking_characters, play_lines = preprocess(raw_play_lines, matcher)
    adj, act_scene_start_end = process(speaking_characters, play_lines)
    graph = postprocess(play_lines, speaking_characters, adj, gender,
            act_scene_start_end)
    return play_lines, graph

def main():
    play_lines, gender = get_files()
    output = process_play(play_lines, gender)
    to_output(output)

if __name__ == "__main__":
    main()
