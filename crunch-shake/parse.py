from utils import get_matcher
from lookup import ROMAN_TO_INT 
from lines import Dialogue, Character, Instruction, Act, Scene

def get_speaking_characters(raw_play_lines, character_matcher):
    """ return a set of all character names """
    return { matched_line.group('name').upper() for matched_line in
            ( character_matcher.search(line) for line in raw_play_lines )
            if matched_line }

def parse_raw_text(raw_play_lines, speaking_characters, matcher):
    """ Parse the lines of the play which is in HTML

    Each line is either ignored or putting into a class derived from a
    namedtuple. 

    Parameters 
    ----------
    raw_play_lines : list of str
        lines of the play
    speaking_characters : set of str
        names of characters who speak
    matcher : namedtuple
        matcher must contain the following the following compiled regex
        matchers, with the following groups. 
        MATCHER : GROUP NAMES
        ---------------------
        dialogue : 'act' , 'scene', 'dialogue' ; opt : 'instruction'
        character : 'name'
        stage_direction : 'stage_direction'
        instruction : no name, uses index 0
        act : 'act'
        scene : 'scene'
        
    Notes
    -----
    character_chain 
        A list of the characters who speak in turn, all capitalized

    Example
    -------
    >>> PLAY_NAME
    alls_well_that_ends_well
    >>> character_chain
    ['COUNTESS', 'BERTRAM', 'LAFEU', 'COUNTESS', 'BERTRAM', ...]
    """
    known_characters_matcher = get_matcher(speaking_characters, "character")
    parsed_lines = []
    character_chain = []
    for i, line in enumerate(raw_play_lines):
        d_match = matcher.dialogue.search(line)
        # d has 3-4 groups : act, scene, dialogue, optional instruction
        if d_match:
            try:
                instruction = d_match.group('instruction')
            except IndexError:
                instruction = None
            dialogue = Dialogue(
                    d_match.group('dialogue'), 
                    process_instructions(
                        d_match.group('instruction'),
                        known_characters_matcher,
                        matcher.instruction,
                        character_chain[-1]),
                    character_chain[-1],
                    d_match.group('act'), 
                    d_match.group('scene'))
            parsed_lines.append(dialogue)
            continue
        c_match = matcher.character.search(line)
        if c_match:
            name = c_match.group('name').upper()
            character_chain.append(name)
            parsed_lines.append(Character(name))
            continue
        sd_match = matcher.stage_direction.search(line)
        if sd_match:
            stage_direction = sd_match.group('stage_direction')
            prev_character = character_chain[-1] if character_chain else None
            instruction = process_instructions(
                    stage_direction,
                    known_characters_matcher,
                    matcher.instruction,
                    prev_character)
            parsed_lines.append(instruction)
            continue
        act_match = matcher.act.search(line)
        if act_match:
            act_roman = act_match.group('act')
            act = ROMAN_TO_INT[act_roman]
            parsed_lines.append(Act(act))
            prev_character = None
            continue
        scene_match = matcher.scene.search(line)
        if scene_match:
            scene_roman = scene_match.group('scene')
            scene = ROMAN_TO_INT[scene_roman]
            parsed_lines.append(Scene(scene))
            prev_character = None
            continue
    return parsed_lines


def process_instructions(instruction, known_characters_matcher,
        instruction_matcher, default_character):
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
            ( instruction_matcher.search(line) 
                for line in instruction_lines ) ]
    characters = [ 
            [ character.upper() 
                for character in known_characters]
            for known_characters in
            ( known_characters_matcher.findall(line) 
                for line in instruction_lines) ]
    return Instruction(instruction, actions, characters, default_character)

def preprocess(raw_play_lines, matcher):
    speaking_characters = get_speaking_characters(raw_play_lines,
            matcher.character)
    play_lines = parse_raw_text(raw_play_lines, speaking_characters, matcher)
    return speaking_characters, play_lines
