import os
import sys

import re
import json
from collections import Counter, namedtuple

file_dir = os.path.dirname(os.path.abspath(__file__))

PLAY_PATH = os.path.abspath(sys.argv[1])
PLAY_NAME = PLAY_PATH[:-5]
META_INPUT_PATH = PLAY_NAME + "_in.json"
META_OUTPUT_PATH = PLAY_NAME +"_out2.json"

DIALOGUE_PATTERN = r'^<a name="(?P<act>\d)\.(?P<scene>\d)\.\d+">' \
    '(\[(?P<instruction>.*)\])?(?P<dialogue>.*)</a><br>'
DIALOGUE_MATCHER = re.compile(DIALOGUE_PATTERN)

CHARACTER_PATTERN = r'^<a name="speech\d+"><b>(?P<name>.*)</b></a>'
CHARACTER_MATCHER = re.compile(CHARACTER_PATTERN)

STAGE_DIRECTION_PATTERN = r'<i>(?P<stage_direction>.*)</i>'
STAGE_DIRECTION_MATCHER = re.compile(STAGE_DIRECTION_PATTERN)

STAGE_DIRECTION_KEYWORDS_PATTERN = r'(enter|exit|exeunt|aside|read)'

class ActSceneDialogue(namedtuple('ActSceneDialogue', ['act', 'scene', 'dialogue'])):
    def __repr__(self):
        return str(self.act) + '.' + str(self.scene) + ' : ' + str(self.dialogue)

class StageDirection(
        namedtuple('StageDirection', ['prec_dialogue_num', 'stage_direction'])):
    # prec_dialogue_num : preceding diaglogue number
    def __repr__(self):
        return str(self.prec_dialogue_num) + ' : ' + str(self.stage_direction)

def file_to_list(path):
    with open(path, 'r') as inputFile:
        return inputFile.readlines()

def json_file_to_dict(path):
    with open(path, 'r') as jsonFile:
        return json.load(jsonFile)

def to_json(x, path):
    with open(path, 'w') as jsonFile:
        return json.dump(x, jsonFile)

def get_files():
    play_lines = file_to_list(PLAY_PATH)
    meta_dict = json_file_to_dict(META_INPUT_PATH)
    return play_lines, meta_dict


def process_play(play_lines):
    speaking_characters = get_speaking_characters(play_lines)
    parsed_play = parse_raw_text(play_lines, speaking_characters)
    play_analysis(speaking_characters, *parsed_play)

def parse_raw_text(play_lines, speaking_characters):
    character_chain = []
    dialogue = []
    act_scene = [ActSceneDialogue(-1, -1, 0)]
    stage_directions = []
    for i in range(len(play_lines)):
        line = play_lines[i]
        d_match = DIALOGUE_MATCHER.search(line)
        if d_match:
            d_info = [ d_match.group('act'), d_match.group('scene'), d_match.group('dialogue') ]
            if d_match.group('instruction'):
                stage_directions.append(
                        StageDirection(
                            len(dialogue) -1,
                            d_match.group('instruction')
                            )
                        )
                
            act = d_match.group('act')
            scene = d_match.group('scene')
            if (act != act_scene[-1].act or scene != act_scene[-1].scene): 
                # len(dialogue) - 1 because before the first line 
                # when a character speaks, a new dialogue is already started
                act_scene.append(ActSceneDialogue(act, scene, len(dialogue) - 1))
            dialogue[-1].append(d_match.group('dialogue'))
            continue
        c_match = CHARACTER_MATCHER.search(line)
        if c_match:
            c_info = c_match.group('name')
            character_chain.append(c_info)
            dialogue.append(list())
            continue
        sd_match = STAGE_DIRECTION_MATCHER.search(line)
        if sd_match:
            stage_direction = sd_match.group('stage_direction')
            # Note sometimes stage directions in the middle of a characters
            # dialogue. However this is treated as if the character appeared
            # after the dialogue in question ended
            stage_directions.append(
                    StageDirection(len(dialogue) - 1, stage_direction))
            continue
    assert len(dialogue) == len(character_chain)
    # Remove placeholder initial act_scene
    act_scene.pop(0)
    parsed_play = namedtuple(
            'ParsedPlay', 
            ['character_chain', 'dialogue', 'act_scene' ,'stage_directions']
            )(character_chain, dialogue, act_scene, stage_directions)
    return parsed_play

def play_analysis(speaking_characters, character_chain, dialogue, act_scene, stage_directions):
    character_count = Counter(character_chain)
    character_dialogue_count = count_lines_of_dialogue(
            character_chain, dialogue)
    parse_stage_directions(speaking_characters, stage_directions)

def parse_stage_directions(speaking_characters, stage_directions):
    parsed_stage_directions = [ 
            [ parse_stage_direction(
                speaking_characters,
                stage_direction_sentences
                )
                for stage_direction_sentences
                in stage_direction.split('.')
                ]
            for (num, stage_direction) in stage_directions 
            ]
    print(parsed_stage_directions)
    return parsed_stage_directions

def parse_stage_direction(speaking_characters, stage_direction_sentence):
    return stage_direction_sentence


def determine_presense():
    pass

def get_speaking_characters(play_lines):
    return { matched_line.group('name') for matched_line in
            (CHARACTER_MATCHER.search(line) for line in play_lines)
            if matched_line }

def count_lines_of_dialogue(character_chain, dialogue):
    assert len(dialogue) == len(character_chain)

    character_dialogue_count = dict()
    for i in range(len(dialogue)):
        if character_chain[i] not in character_dialogue_count:
            character_dialogue_count[character_chain[i]] = 1
        else:
            character_dialogue_count[character_chain[i]] += 1
    return character_dialogue_count 

def main():
    play_lines, meta_dict = get_files()
    output_dict = process_play(play_lines)
    to_json(output_dict, META_OUTPUT_PATH)

if __name__ == "__main__":
    main()
