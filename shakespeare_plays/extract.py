import os
import sys

import re
import json
from collections import Counter, namedtuple
from itertools import chain
from functools import reduce


FILE_DIR = os.path.dirname(os.path.abspath(__file__))

PLAY_PATH = os.path.abspath(sys.argv[1])
PLAY_NAME = PLAY_PATH[:-5]

OUTPUT_PATH = PLAY_NAME + ".out"

DIALOGUE_PATTERN = r'^<a name="?(?P<act>\d)\.(?P<scene>\d)\.\d+"?>' \
    '(\[(?P<instruction>.*)\])?(?P<dialogue>.*)</a><br>'
# <a name="1.1.11">[To HELENA]  The best wishes that can be forged in</a><br>
DIALOGUE_MATCHER = re.compile(DIALOGUE_PATTERN, re.IGNORECASE)

CHARACTER_PATTERN = r'^<a name="?speech\d+"?><b>(?P<name>.*)</b></a>'
# <a name="speech25"><b>BERTRAM</b></a>
CHARACTER_MATCHER = re.compile(CHARACTER_PATTERN, re.IGNORECASE)

STAGE_DIRECTION_PATTERN = r'<i>(?P<stage_direction>.*)</i>'
# <p><i>Exeunt BERTRAM and LAFEU</i></p>
STAGE_DIRECTION_MATCHER = re.compile(STAGE_DIRECTION_PATTERN)

INSTRUCTION_PATTERN = r're-?enter|enter|exit|exeunt|aside|read|to'
INSTRUCTION_MATCHER = re.compile(
        INSTRUCTION_PATTERN,
        re.IGNORECASE
        )

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
    'prev_character'
    ])):
    TYPE = 'instruction'
    def __repr__(self):
        action_characters = [ 
                str(self.actions[i]) + " - " + str(self.characters[i])
                for i in range(len(self.actions)) ]
        return self.raw + ' : ' + str(action_characters) + ' : ' + str(self.prev_character)

def get_speaking_characters(play_lines):
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
            name = c_match.group('name')
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
    return parsed_lines, character_chain

def process_instructions(
        instruction, 
        known_characters_matcher, 
        prev_character):
    if instruction is None:
        return None
    instruction_lines = instruction.split(".")
    actions = [ match.group(0) if match else None for match in 
            [ INSTRUCTION_MATCHER.search(line)
            for line in instruction_lines ]]
    characters = [ known_characters_matcher.findall(line) 
            for line in instruction_lines ]
    return Instruction(instruction, actions, characters, prev_character)

def get_act_scene_range(play_lines):
    act_scene_range = []
    act_scenes = []
    cur_act_scene = None
    for i, line in enumerate(play_lines):
        if line.TYPE == 'dialogue':
            act_scene = (line.act, line.scene)
            if cur_act_scene != act_scene:
                cur_act_scene = act_scene
                act_scenes.append(act_scene)
                act_scene_range.append(i)
    act_scene_range.append(len(play_lines))
    return act_scenes, act_scene_range

def process_play(raw_play_lines):
    speaking_characters = get_speaking_characters(raw_play_lines)
    play_lines, character_chain = parse_raw_text(
            raw_play_lines, 
            speaking_characters)
    act_scenes, act_scene_range = get_act_scene_range(play_lines)
    print(act_scenes)
    print(act_scene_range)

    # presense = get_presense(play_lines)
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
