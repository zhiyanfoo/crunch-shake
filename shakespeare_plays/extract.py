import os
import sys

import re
import json
from collections import Counter, namedtuple
from itertools import chain
from functools import reduce

from lookup import ROMAN_TO_INT 

FILE_DIR = os.path.dirname(os.path.abspath(__file__))

PLAY_PATH = os.path.abspath(sys.argv[1])
PLAY_NAME = PLAY_PATH[:-5]

OUTPUT_PATH = PLAY_NAME + ".out"

"""
MODULE LEVEL MATCHERS
=====================

Included in the module are regex matchers which are throughout by functions in
the module.

Below are examples from Shakespeare's 'All's Well That Ends Well ' (in html)
that will be matched. 

DIALOGUE_MATCHER
----------------
<a name="1.1.11">[To HELENA]  The best wishes that can be forged in</a><br>

CHARACTER_MATCHER
-----------------
<a name="speech25"><b>BERTRAM</b></a>

STAGE_DIRECTION_MATCHER
-----------------------
<a name="speech25"><b>BERTRAM</b></a>

ACT_MATCHER
-----------
<h3>ACT I</h3>

SCENE_MATCHER
-------------
<h3>SCENE I. Rousillon. The COUNT's palace.</h3>
"""


DIALOGUE_PATTERN = r'^<a name="?(?P<act>\d)\.(?P<scene>\d)\.\d+"?>' \
    '(\[(?P<instruction>.*)\])?(?P<dialogue>.*)</a><br>'
DIALOGUE_MATCHER = re.compile(DIALOGUE_PATTERN, re.IGNORECASE)

CHARACTER_PATTERN = r'^<a name="?speech\d+"?><b>(?P<name>.*)</b></a>'
CHARACTER_MATCHER = re.compile(CHARACTER_PATTERN, re.IGNORECASE)

STAGE_DIRECTION_PATTERN = r'<i>(?P<stage_direction>.*)</i>'
STAGE_DIRECTION_MATCHER = re.compile(STAGE_DIRECTION_PATTERN)

INSTRUCTION_PATTERN = r're-enter|enter|exit|exeunt|aside|read|to'
INSTRUCTION_MATCHER = re.compile(
        INSTRUCTION_PATTERN,
        re.IGNORECASE
        )

ACT_PATTERN = r"<h3>act (?P<act>[IVX]+).*</h3>"
ACT_MATCHER = re.compile(ACT_PATTERN, re.IGNORECASE)

SCENE_PATTERN = r"<h3>scene (?P<scene>[IVX]+).*</h3>"
SCENE_MATCHER = re.compile(SCENE_PATTERN, re.IGNORECASE)

class Dialogue(namedtuple('Dialogue', [
        'dialogue', 
        'instruction', 
        'character',
        'act',
        'scene'
        ])):
    TYPE = 'dialogue'
    def __repr__(self):
        return str(self.act) + '.' + str(self.scene) + ' :' \
               + str(self.dialogue) + ' : ' + str(self.instruction)

class Character(namedtuple('Character', ['character'])):
    TYPE = 'character'
    def __repr__(self):
        return self.character

class Instruction(namedtuple('Instruction', [
    'raw', 
    'actions', 
    'characters',
    'default_character'
    ])):
    TYPE = 'instruction'
    def __repr__(self):
        action_characters = [ 
                str(self.actions[i]) + " - " + str(self.characters[i])
                for i in range(len(self.actions)) ]
        return self.raw + ' : ' + str(action_characters) \
                + ' : ' + str(self.default_character)

class Act(namedtuple('Act', ['act'])):
    TYPE ='act'
    def __repr____(self):
        return self.act

class Scene(namedtuple('Scene', ['scene'])):
    TYPE ='scene'
    def __repr____(self):
        return self.scene

def get_speaking_characters(play_lines):
    """ return a set of all character names """
    return { matched_line.group('name') for matched_line in
            (CHARACTER_MATCHER.search(line) for line in play_lines)
            if matched_line }

def get_known_character_matcher(speaking_characters):
    joined_characters = "|".join(speaking_characters)
    characters_pattern = "(?P<character>" + joined_characters + ")"
    known_characters_matcher = re.compile(
            characters_pattern,
            re.IGNORECASE)
    return known_characters_matcher

def parse_raw_text(raw_play_lines, speaking_characters):
    """ Parse the lines of the play which is in HTML

    Each line is either ignored or putting into a class derived from a
    namedtuple. 
    
    Returns
    -------
    character_chain 
        A list of the characters who speak in turn, all capitalized

    Example:
        >>> PLAY_NAME
        alls_well_that_ends_well
        >>> character_chain
        ['COUNTESS', 'BERTRAM', 'LAFEU', 'COUNTESS', 'BERTRAM', ...]
    """
    known_characters_matcher = get_known_character_matcher(speaking_characters)
    parsed_lines = []
    character_chain = []
    for i, line in enumerate(raw_play_lines):
        d_match = DIALOGUE_MATCHER.search(line)
        # d has 3-4 groups : act, scene, dialogue, optional instruction
        if d_match:
            dialogue = Dialogue(
                    d_match.group('dialogue'), 
                    process_instructions(
                        d_match.group('instruction'),
                        known_characters_matcher,
                        character_chain[-1]),
                    character_chain[-1],
                    d_match.group('act'), 
                    d_match.group('scene'))
            parsed_lines.append(dialogue)
            continue
        c_match = CHARACTER_MATCHER.search(line)
        if c_match:
            name = c_match.group('name').upper()
            character_chain.append(name)
            parsed_lines.append(Character(name))
            continue
        sd_match = STAGE_DIRECTION_MATCHER.search(line)
        if sd_match:
            stage_direction = sd_match.group('stage_direction')
            prev_character = character_chain[-1] if character_chain else None
            instruction = process_instructions(
                    stage_direction,
                    known_characters_matcher,
                    prev_character)
            parsed_lines.append(instruction)
            continue
        act_match = ACT_MATCHER.search(line)
        if act_match:
            act_roman = act_match.group('act')
            act = ROMAN_TO_INT[act_roman]
            parsed_lines.append(Act(act))
            prev_character = None
            continue
        scene_match = SCENE_MATCHER.search(line)
        if scene_match:
            scene_roman = scene_match.group('scene')
            scene = ROMAN_TO_INT[scene_roman]
            parsed_lines.append(Scene(scene))
            prev_character = None
            continue
    return parsed_lines, character_chain

def process_instructions(
        instruction, 
        known_characters_matcher, 
        default_character):
    """
    For each sentence only one action (the first) is matched, but a single
    instruction can contain multiple sentences, which is why action are
    returned as a list. Each action can be applied to multiple characters. Note
    that all character names are shifted to uppercase
    """
    if instruction is None:
        return None
    instruction_lines = instruction.split(".")
    actions = [ match.group(0) if match else None for match in 
            ( INSTRUCTION_MATCHER.search(line) 
                for line in instruction_lines ) ]
    characters = [ 
            [ character.upper() 
                for character in known_characters]
            for known_characters in
            ( known_characters_matcher.findall(line) 
                for line in instruction_lines) ]
    return Instruction(instruction, actions, characters, default_character)

def get_act_scene_range(play_lines):
    """
    act_scenes : 
    act_scene_range : 
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
        + 1 (so basically len(play_lines))
 
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

def get_enterance_exit(play_lines, act_scene_range, character_chain):
    """
    For each character in the play, enterance[character] gives the line
    numbers, of `play_lines`, for when they enter a scene. exit[character] does
    the same for when the characters exit
    """
    enterance = { character : [] for character in character_chain }
    print(enterance)
    exit = { character : [] for character in character_chain }
    for scene_start, scene_end in zip(act_scene_range, act_scene_range[1:]):
        scene_enterance, scene_exit = enterance_exit_by_scene(
                play_lines, 
                scene_start,
                scene_end)
        for character in scene_enterance:
            enterance[character].append(scene_enterance[character])
            exit[character].append(scene_exit[character])
    print("enterance")
    print(enterance)
    print("exit")
    print(exit)
    return enterance, exit

def enterance_exit_by_scene(play_lines, scene_start, scene_end):
    """ 
    If character enters, exit and re-enters, scene_enterance will note only
    first enterance; scene_exit will note only first exit.
    """
    scene_enterance = dict()
    scene_exit = dict()
    character_start = create_check_and_add(scene_enterance, scene_start)
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
    close_loose_characters(scene_enterance, scene_exit, scene_end - 1)
    close_loose_characters(scene_exit, scene_enterance, scene_start)
    return scene_enterance, scene_exit

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

def instruction_character_start(
        instruction, 
        line_index, 
        patterns, 
        add_if_not_in):
    """
    determine if instruction contains enter/exit type action
    and add either default_character or characters in instruction
    to scene_enterance/exit
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

def process_play(raw_play_lines):
    speaking_characters = get_speaking_characters(raw_play_lines)
    play_lines, character_chain = parse_raw_text(
            raw_play_lines, 
            speaking_characters)
    act_scenes, act_scene_range = get_act_scene_range(play_lines)
    print(act_scenes)
    print(act_scene_range)
    enterance, exit = get_enterance_exit(
            play_lines, 
            act_scene_range, 
            character_chain)
    return play_lines, character_chain

# INPUT OUTPUT

def to_output(parsed_play):
    a = [ str(x) + "\n" for x in  parsed_play[0] ]
    li = a + ['\n'] * 3 + [ x + ", " for x in parsed_play[1] ]
    # li = reduce(lambda x, y: x + ['\n'] * 3 + y, parsed_play)
    list_to_file(li, OUTPUT_PATH)

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

def get_files():
    play_lines_raw = file_to_list(PLAY_PATH)
    return play_lines_raw

def main():
    play_lines = get_files()
    output = process_play(play_lines)
    to_output(output)

if __name__ == "__main__":
    main()
