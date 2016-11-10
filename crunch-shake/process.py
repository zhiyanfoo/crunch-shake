from lines import Dialogue, Character, Instruction, Act, Scene
from utils import invert_dict

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
    # print(act_scene_range)
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
