import os
import sys

from utils import (file_to_list, json_file_to_dict, to_json, list_to_file)
from mit_shakespeare_regex import matcher
from parse import preprocess
from process import process
from analysis import postprocess

import networkx as nx

# INPUT OUTPUT

def to_output(parsed_play, output_path, output_path_base):
    play_lines, graph = parsed_play
    a = [ str(x) + "\n" for x in play_lines ]
    print("writing to", output_path)
    list_to_file(a, output_path_base + '.out')
    dot_graph = nx.nx_agraph.to_agraph(graph)
    dot_graph.write(output_path_base + ".dot")
    prog = ['dot', 'circo']
    for p in prog:
        dot_graph.layout(p)
        dot_graph.draw(output_path_base + "_" + p + ".png")

def get_files(play_path, gender_path):
    play_lines_raw = file_to_list(play_path)
    try:
        gender = json_file_to_dict(gender_path)
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

def get_paths(play_path):
    head_dir = os.path.dirname(os.path.dirname(play_path))
    play_name = os.path.basename(play_path)[:-len('.html')]
    gender_path = os.path.join(head_dir, 'gender', play_name + ".gender")
    output_path = os.path.join(head_dir, 'output')
    output_path_base = os.path.join(output_path, play_name)
    return gender_path, output_path, output_path_base

def run(play_path):
    gender_path, output_path, output_path_base = get_paths(play_path)
    play_lines, gender = get_files(play_path, gender_path)
    output = process_play(play_lines, gender)
    # to_output(output, output_path, output_path_base)

def main():
    play_path = os.path.abspath(sys.argv[1])
    run(play_path)


if __name__ == "__main__":
    main()
