from collections import namedtuple

class Dialogue(namedtuple('Dialogue', [
        'dialogue', 
        'instruction', 
        'character',
        'act',
        'scene'
        ])):
    """ Raw lines of dialogue should be parsed and put into this namedtuple.

    Parameters 
    ----------
    dialogue : str
        Actual line that the character will speak.
    instruction : Instruction
        Any stage directions that are embedded in the dialogue.
    character : str
        Name of character speaking.
    act : int
        Act number the line is form.
    scene : int
        Scene number the line is fom
    """
    TYPE = 'dialogue'
    def __repr__(self):
        return str(self.act) + '.' + str(self.scene) + ' :' \
               + str(self.dialogue) + ' : ' + str(self.instruction)

class Character(namedtuple('Character', ['character'])):
    """ Line that indicates a new character is going to speak.

    Parameters 
    ----------
    character : str
        character name
    """
    TYPE = 'character'
    def __repr__(self):
        return self.character

class Instruction(namedtuple('Instruction', [
    'raw', 
    'actions', 
    'characters',
    'default_character'
    ])):
    """ Stage direction, could be embedded in line of dialogue

    Parameters 
    ----------
    raw : str
        The text of the stage direction in its entirety (mainly used for
        debugging)
    actions : list of str
        list of actions
    characters : list of str
        list of characters. The characters at index i are associated with the
        actions at index i. So the length of actions must be identical to that
        of characters.
    default_character : str
        If name is embedded in dialogue, default_character is the person who
        spoke the line. Else it is the person who spoke the previous line. If
        it is that start of the scene, then None.

    Example
    -------
    <A NAME=speech5><b>FRIAR LAURENCE</b></a>
    <blockquote>
    <A NAME=4.1.16>[Aside]  I would I knew not why it should be slow'd.</A><br>
    >>> Instruction(
            'I would I knew not why it should be slow'd',
            [ 'Aside'],
            [ None ],
            'Friar Laurence'
            )
    """
    TYPE = 'instruction'
    def __repr__(self):
        action_characters = [ 
                str(self.actions[i]) + " - " + str(self.characters[i])
                for i in range(len(self.actions)) ]
        return self.raw + ' : ' + str(action_characters) \
                + ' : ' + str(self.default_character)

class Act(namedtuple('Act', ['act'])):
    """ Signfies a new act
    Parameters 
    ----------
    act : int
        act number

    Notes 
    -----
    Should be followed by a scene line
    """
    TYPE ='act'
    def __repr____(self):
        return self.act

class Scene(namedtuple('Scene', ['scene'])):
    """ Signfies a new scene
    Parameters 
    ----------
    act : int
        act number
    """
    TYPE ='scene'
    def __repr____(self):
        return self.scene
