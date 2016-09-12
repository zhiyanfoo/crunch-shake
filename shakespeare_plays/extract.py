import os
import sys

import networkx as nx

import string
from itertools import chain
from functools import reduce
from math import log

from utils import (file_to_list, json_file_to_dict, to_json, list_to_file,
        get_matcher)
from mit_shakespeare_regex import matcher
from lines import Dialogue, Character, Instruction, Act, Scene
from parse import get_speaking_characters, parse_raw_text

# FILE_DIR = os.path.dirname(os.path.abspath(__file__))

PLAY_PATH = os.path.abspath(sys.argv[1])
PLAY_NAME = PLAY_PATH[:-5]

OUTPUT_PATH = PLAY_NAME + ".out"

def get_act_scene_range(play_lines):
    """
    Returns
    -------
    act_scenes
        list of tuples containing (act, scene)

        >>> PLAY_NAME
        alls_well_that_ends_well
        >>> act_scenes
        [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), ...]

    act_scene_range
        contains start of all act/scenes as well as the index of the last line
        + 1 (so basically len(play_lines) appended)
    """
    act_scenes = []
    act_scene_range = []
    for i, line in enumerate(play_lines):
        if line.TYPE == Scene.TYPE:
            prev_line = play_lines[i - 1]
            if prev_line.TYPE == Act.TYPE:
                act_scenes.append((prev_line.act, line.scene))
                act_scene_range.append(i - 1)
            else:
                act_scenes.append((
                    act_scenes[-1][0] if act_scenes else 1,
                    line.scene))
                act_scene_range.append(i)
    act_scene_range.append(len(play_lines))
    # make sure that the beginning is part of an act, scene
    assert act_scene_range[0] == 0
    assert len(act_scenes) + 1 == len(act_scene_range)
    return act_scenes, act_scene_range

def get_entrance_exit(play_lines, act_scene_start_end):
    """
    For each character in the play, entrance[character] gives the line
    numbers, of `play_lines`, for when they enter a scene. exit[character] does
    the same for when the characters exit
    """
    entrance_exit = [ 
            entrance_exit_by_scene(play_lines, scene_start, scene_end)
            for scene_start, scene_end in act_scene_start_end ]
    entrance, exit = map(list, zip(*entrance_exit))
    return entrance, exit

def entrance_exit_by_scene(play_lines, scene_start, scene_end):
    """ 
    Note
    ----
    If character enters, exit and re-enters, scene_entrance will note only
    first entrance; scene_exit will note only first exit.

    scene_exit gives the last line for each character inclusive.
    """
    scene_entrance = dict()
    scene_exit = dict()
    character_start = create_check_and_add(scene_entrance, scene_start)
    character_end = create_check_and_add(
            scene_exit, 
            scene_end, 
            entering=False)
    for i in range(scene_start, scene_end):
        line = play_lines[i]
        character_start(line, i)
    for i in reversed(range(scene_start, scene_end)):
        line = play_lines[i]
        character_end(line, i)
    # ensure that characters have both entrance and exit
    close_loose_characters(scene_entrance, scene_exit, scene_end - 1)
    close_loose_characters(scene_exit, scene_entrance, scene_start)
    return scene_entrance, scene_exit

def close_loose_characters(characters_one, characters_two, default_line_number):
    for character in (characters_one.keys() - characters_two.keys()):
        characters_two[character] = default_line_number

def create_check_and_add(scene, default, entering=True):
    add_if_not_in = create_add_if_not_in(scene)
    patterns = ['enter'] if entering else ['exit', 'exeunt']
    def check_and_add(line, i):
        if line.TYPE == Character.TYPE:
            add_if_not_in(line.character, default)
        elif line.TYPE == Instruction.TYPE:
            instruction_character_start(
                    line, 
                    i, 
                    patterns,
                    add_if_not_in
                    )
        elif line.TYPE == Dialogue.TYPE:
            add_if_not_in(line.character, default)
            instruction = line.instruction
            if instruction:
                instruction_character_start(
                        instruction, 
                        i, 
                        patterns,
                        add_if_not_in
                        )
    return check_and_add

def instruction_character_start(instruction, line_index, patterns,
        add_if_not_in):
    """ 
    determine if instruction contains enter/exit type action and add_if_not_in
    either default_character or characters in instruction
    """
    for i, action in enumerate(instruction.actions):
        if pattern_in(patterns, action):
            if not instruction.characters[i]:
                if instruction.default_character:
                    add_if_not_in(instruction.default_character, line_index)
            for character in instruction.characters[i]:
                add_if_not_in(character, line_index)

def create_add_if_not_in(scene_characters):
    def add_if_not_in(character, i):
        if character not in scene_characters:
            scene_characters[character] = i
    return add_if_not_in

def pattern_in(patterns, action):
    return action and any(pattern in action.lower() for pattern in patterns)

def get_presence(speaking_characters, play_lines, act_scene_start_end,
        entrance, exit):
    adj = { character : dict() for character in speaking_characters }
    for i, start_end in enumerate(act_scene_start_end):
        get_presence_by_scene(
                adj, 
                play_lines, 
                start_end, 
                entrance[i], 
                exit[i])
    return adj

def get_presence_by_scene(adj, play_lines, start_end, scene_entrance,
        scene_exit):
    """ Given the points at which characters entered and exited a screen,
    construct adj which gives which lines were spoken to whom.
    """
    scene_start, scene_end = start_end
    characters_present = set()
    inv_entrance, inv_exit = map(invert_dict, [scene_entrance, scene_exit])
    for i in range(scene_start, scene_end):
        line = play_lines[i]
        if i in inv_entrance:
            for character in inv_entrance[i]:
                characters_present.add(character)
        if line.TYPE == Dialogue.TYPE:
            for character in characters_present - {line.character}:
                if character in adj[line.character]:
                    adj[line.character][character].append(i)
                else:
                    adj[line.character][character] = [i]
        if i in inv_exit:
            for character in inv_exit[i]:
                characters_present.remove(character)

def invert_dict(front_dict):
    """ Take a dict of key->values and return values->[keys] """
    back_dict = { value : [] for value in front_dict.values() }
    for key, value in front_dict.items():
        back_dict[value].append(key)
    return back_dict
    
def preprocess(raw_play_lines):
    speaking_characters = get_speaking_characters(raw_play_lines,
            matcher.character)
    play_lines = parse_raw_text(raw_play_lines, speaking_characters, matcher)
    return speaking_characters, play_lines

def process(speaking_characters, play_lines):
    act_scenes, act_scene_range = get_act_scene_range(play_lines)
    act_scene_start_end = list(zip(act_scene_range, act_scene_range[1:]))
    entrance, exit = get_entrance_exit(
            play_lines, 
            act_scene_start_end)
    adj = get_presence(
            speaking_characters, 
            play_lines, 
            act_scene_start_end,
            entrance, 
            exit)
    return adj, act_scene_start_end

def postprocess(play_lines, speaking_characters, adj, gender,
        act_scene_start_end):
    adj_num = { speaker : { spoken : len(adj[speaker][spoken]) 
        for spoken in adj[speaker] } 
        for speaker in adj }
    graph = create_graph(adj_num)
    reciprocal_graph = create_graph(adj_num, reciprocal=True)
    characters_by_importance = get_characters_by_importance(
            play_lines, 
            speaking_characters, 
            graph,
            reciprocal_graph)
    vocab_difference(play_lines, gender)
    bechdel_scenes = bechdel_test(play_lines, characters_by_importance, adj,
            gender, act_scene_start_end)
    return graph

def get_characters_by_importance(play_lines, speaking_characters, graph,
        reciprocal_graph):
    reverse_graph = graph.reverse(copy=True)

    # METRICS
    lines_by_character = get_lines_by_character(play_lines, speaking_characters)
    out_degree = nx.out_degree_centrality(graph)
    page_rank = nx.pagerank_numpy(reverse_graph)
    betweenness = nx.betweenness_centrality(reciprocal_graph)

    metrics = [lines_by_character, out_degree, page_rank, betweenness]
    relative_importance = [0.625, 0.125, 0.125, 0.125]

    for i, x in enumerate(metrics):
        normalize_linear(x)
        scale(x, relative_importance[i])

    character_value = { character : sum( metric[character] for metric in metrics )
            for character in speaking_characters }
    sorted_characters = dict_sorted(character_value)
    return sorted_characters

def scale(x, a):
    for key in x:
        x[key] *= a

def get_lines_by_character(play_lines, speaking_characters):
    lines_by_character = { key : 0 for key in speaking_characters }
    for line in play_lines:
        if line.TYPE == Dialogue.TYPE:
            lines_by_character[line.character] += 1
    return lines_by_character

def normalize_linear(x):
    biggest = max(x.values())
    scale(x, 1/biggest)

def dict_sorted(x):
    return sorted(( (key , x[key]) for key in x ), key=lambda x: x[1])

def process_play(raw_play_lines, gender):
    speaking_characters, play_lines = preprocess(raw_play_lines)
    adj, act_scene_start_end = process(speaking_characters, play_lines)
    graph = postprocess(play_lines, speaking_characters, adj, gender,
            act_scene_start_end)
    return play_lines, graph

# NETWORKX AND PYGRAPHVIZ

def create_graph(adj_num, reciprocal=False):
    def reciprocal_weight(speaker, recipient):
        weight = adj_num[speaker][recipient]
        try:
            reciprocal_weight = 1 / weight
            return reciprocal_weight
        except ZeroDivisionError:
            return float('inf')
    def normal_weight(speaker, recipient):
        return adj_num[speaker][recipient]
    weight_f = reciprocal_weight if reciprocal else normal_weight
    edges = [ (
        speaker, 
        recipient, 
        {'weight' : weight_f(speaker, recipient), 'color' : 'blue'}
        ) 
            for speaker in adj_num
            for recipient in adj_num[speaker] ]
    graph = nx.DiGraph()
    graph.add_edges_from(edges)
    return graph

# BECHDEL TEST

""" 
The Bechdel test is defined as follows. It 'asks whether a work of fiction
features at least two women who talk to each other about something other than a
man. The requirement that the two women must be named is sometimes added.' 

For this implementation the requirement that the conversation involve something
other than a man is fufilled by the following

1. In a scene the women must not mention any other male characters by name,
when speaking to another women.  

2. they must not mention words relating to male partners.

SEE `create_forbidden_matcher`

3. they must not mention words related to sexual relationships

SEE `create_forbidden_matcher`

In place of whether the two women are named, both women must be in the upper
50% of characters as given by character by importance.  
"""

def bechdel_test(play_lines, characters_by_importance, adj, gender,
        act_scene_start_end):
    characters = [ x[0] for x in characters_by_importance ]
    # if odd number of characters, includes n + 1 characters, where
    # len(characters) = 2n + 1
    start = len(characters_by_importance) // 2
    notable_females = set(filter(lambda x: gender[x] == 'F',
        characters[start:]))
    female_to_female = sorted([ line 
            for speaker in notable_females
            for spoken in notable_females - {speaker} 
            for line in adj[speaker][spoken] ])
    female_lines_by_scene = get_female_lines_by_scene(female_to_female,
            act_scene_start_end)
    males = filter(lambda x: gender[x] == 'M', characters)
    bechdel_scenes = [ bechdel_by_scene(start, end, female_to_female,
        play_lines, males) for start, end in female_lines_by_scene ]
    # Abusing the fact that True is one
    return sum(bechdel_scenes) / len(bechdel_scenes)

def get_female_lines_by_scene(female_to_female, act_scene_start_end):
    i = 0
    female_lines_by_scene = []
    for _ , end in act_scene_start_end:
        for j in range(i, len(female_to_female)):
            if female_to_female[j] >= end:
                female_lines_by_scene.append((i, j))
                i = j
                break
    female_lines_by_scene.append((i, len(female_to_female)))
    return female_lines_by_scene

def bechdel_by_scene(start, end, female_to_female, play_lines,
        males):
    forbidden_matcher = create_forbidden_matcher(males)
    if start == end:
        return False
    for i in range(start, end):
        line_i = female_to_female[i]
        line = play_lines[line_i]
        if forbidden_matcher.search(line.dialogue):
            return False
    return True

def create_forbidden_matcher(males):
    icky = ['sex', 'sexual', 'intercourse', 'marriage', 'matrimony','courting',
            'love', 'wedlock']
    boyfriend = ['boyfriend', 'partner', 'husband', 'spouse', 'lover',
            'admirer', 'fiancé', 'amour', 'inamorato']
    forbidden_words = icky + boyfriend + list(males)
    return get_matcher(forbidden_words, "forbidden")

# VOCAB DIFFERENCES

def vocab_difference(play_lines, gender):
    males_vocab = dict()
    female_vocab = dict()
    line_to_vocab = create_line_to_vocab()
    for line in play_lines:
        if line.TYPE == Dialogue.TYPE:
            gender_character = gender[line.character]
            if gender_character == "M":
                line_to_vocab(line.dialogue, males_vocab)
            elif gender_character == "F":
                line_to_vocab(line.dialogue, female_vocab)
    get_word_gender = create_get_word_gender(males_vocab, female_vocab)
    word_gender = { key : get_word_gender(key)
            for key in set(males_vocab.keys()).union(set(female_vocab.keys())) }
    word_gender_sorted = sorted(word_gender, key=lambda x: word_gender[x])

    # print([ (word, word_gender[word]) for word in word_gender_sorted[:25] ])
    # print([ (word, word_gender[word]) for word in word_gender_sorted[-25:] ])
    # print(word_gender_sorted[:25])
    # print(word_gender_sorted[-25:])

def create_line_to_vocab():
    remove_punctuation = create_remove_punctuation()
    def line_to_vocab(line, vocab):
        stripped = remove_punctuation(line)
        words = stripped.split(" ")
        for word in words:
            if word in vocab:
                vocab[word] += 1
            else:
                vocab[word] = 1
    return line_to_vocab

def create_get_word_gender(males_vocab, female_vocab):
    num_male_words = sum(males_vocab.values())
    num_female_words = sum(female_vocab.values())
    male_threshold = num_male_words / len(males_vocab)
    female_threshold = num_female_words / len(female_vocab)
    def get_ratio(m_num, f_num):
        norm_m_num = m_num / num_male_words
        norm_f_num = f_num / num_female_words
        diff = norm_m_num - norm_f_num
        _sum = norm_m_num + norm_f_num
        ratio = diff / _sum
        return ratio
    def get_word_gender(word):
        m_num = males_vocab.get(word, 0)
        f_num = female_vocab.get(word, 0)
        meet_threshold = m_num > male_threshold or f_num > female_threshold 
        metric = get_ratio(m_num, f_num) if meet_threshold else 0
        return metric
    return get_word_gender

def create_remove_punctuation():
    remove_punct_map = dict.fromkeys(map(ord, string.punctuation))
    def remove_punctuation(line):
        return line.translate(remove_punct_map)
    return remove_punctuation

# INPUT OUTPUT

def to_output(parsed_play):
    play_lines, graph = parsed_play
    a = [ str(x) + "\n" for x in play_lines ]
    list_to_file(a, OUTPUT_PATH)
    print("writing to", OUTPUT_PATH)
    dot_graph = nx.nx_agraph.to_agraph(graph)
    dot_graph.write(PLAY_NAME + ".dot")
    prog = ['dot', 'circo']
    for p in prog:
        dot_graph.layout(p)
        dot_graph.draw(PLAY_NAME + "_" + p + ".png")

def get_files():
    play_lines_raw = file_to_list(PLAY_PATH)
    try:
        gender = json_file_to_dict(PLAY_NAME + "_gender.json")
    except FileNotFoundError:
        print("require gender file")
        gender = None
    return play_lines_raw, gender

def main():
    play_lines, gender = get_files()
    output = process_play(play_lines, gender)
    to_output(output)

if __name__ == "__main__":
    main()
