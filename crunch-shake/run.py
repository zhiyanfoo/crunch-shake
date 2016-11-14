import os
import sys

from utils import (file_to_list, json_file_to_dict, to_json, list_to_file,
        get_title)
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


def get_paths(play_path):
    head_dir = os.path.dirname(os.path.dirname(play_path))
    play_name = os.path.basename(play_path)[:-len('.html')]
    gender_path = os.path.join(head_dir, 'gender', play_name + ".gender")
    output_path = os.path.join(head_dir, 'output')
    output_path_base = os.path.join(output_path, play_name)
    return gender_path, output_path, output_path_base, play_name

# STATS

"""
    Percentage of females to males overall.
    Percentage of notable female characters to notable male characters
      (the rest would be ambiguous) per scene and overall.
    A ranking of the plays using the percentages of scenes that past the
      Bechdel Test.
    The percentages that fail the test because of a lack of females versus
      those that failed because the conversation was about males.
    A summary of what the notable females talked about in 8 randomly chosen
      scenes that passed the test. 
    A summary of what the notable females talked about in 8 randomly chosen
        scenes that failed the test because they said a word on the blacklist.
"""

def gender_stats(speaking_characters, gender, play_stats):
    def count(letter):
        return sum([ 1 for character in speaking_characters if
                gender[character] == letter])
    play_stats['males'] = count('M')
    play_stats['females'] = count('F')
    play_stats['unisex'] = count('N')

# PROCESSING


def process_play(raw_play_lines, gender, play_stats):
    speaking_characters, play_lines = preprocess(raw_play_lines, matcher)
    gender_stats(speaking_characters, gender, play_stats)
    adj, act_scene_start_end = process(speaking_characters, play_lines)
    play_stats['scenes'] = len(act_scene_start_end)
    graph = postprocess(play_lines, speaking_characters, adj, gender,
            act_scene_start_end, play_stats)
    return play_lines, graph


def run(play_path, stats):
    gender_path, output_path, output_path_base, play_name = get_paths(play_path)
    # print(play_name)
    raw_play_lines, gender = get_files(play_path, gender_path)
    stats[play_name] = {'title' : get_title(raw_play_lines)}
    play_stats= stats[play_name]
    output = process_play(raw_play_lines, gender, play_stats)
    # to_output(output, output_path, output_path_base)

def main():
    play_path = os.path.abspath(sys.argv[1])
    stats = {}
    run(play_path, stats)


if __name__ == "__main__":
    main()
