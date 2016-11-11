import networkx as nx

from lines import Dialogue, Character, Instruction, Act, Scene
from utils import create_remove_punctuation, get_matcher

def get_characters_by_importance(play_lines, speaking_characters, graph,
        reciprocal_graph, metrics_weight=[0.625, 0.125, 0.125, 0.125]):
    reverse_graph = graph.reverse(copy=True)

    # METRICS
    lines_by_character = get_lines_by_character(play_lines, speaking_characters)
    out_degree = nx.out_degree_centrality(graph)
    page_rank = nx.pagerank_numpy(reverse_graph)
    betweenness = nx.betweenness_centrality(reciprocal_graph)

    metrics = [lines_by_character, out_degree, page_rank, betweenness]

    for i, x in enumerate(metrics):
        normalize_linear(x)
        scale(x, metrics_weight[i])

    # print(speaking_characters)
    # print(metrics)
    character_value = { character : sum( metric.get(character, 0) for metric in
        metrics ) for character in speaking_characters }
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
            for speaker in adj_num for recipient in adj_num[speaker] ]
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

Note:
    If there are no females in the upper 50% of characters, it retuns 0%.
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
            for line in adj[speaker].get(spoken, [])])
    female_lines_by_scene = get_female_lines_by_scene(female_to_female,
            act_scene_start_end)
    males = filter(lambda x: gender[x] == 'M', characters)
    bechdel_scenes = [ bechdel_by_scene(start, end, female_to_female,
        play_lines, males) for start, end in female_lines_by_scene ]
    # Abusing the fact that True is one
    bechdel_percent = sum(bechdel_scenes) / len(act_scene_start_end)
    return bechdel_scenes, bechdel_percent

def get_female_lines_by_scene(female_to_female, act_scene_start_end):
    """ for each scene in play, get the range of lines in female_to_female
    which belong to that scene. As is in common, the range is defined to be
    (inclusive, exclusive).

    For example:
    if 
    >>> female_to_female = [0, 1, 3, 8, 9, 10, 11, 100, 101]
    >>> act_scene_start_end = [(0, 10), (10, 30), (30, 80), (80, 102)]

    then after 
    >>> female_lines_by_scene = [ lines_by_scene(female_to_female, end) for _ ,
            end in act_scene_start_end ]
    >>> female_lines_by_scene == [(0, 5), (5, 7), (7,7), (7,9)]
    """
    class LinesByScenes:
        def __init__(self):
            self.left_marker = 0
            self.reached_end = False

        def __call__(self, female_to_female, end):
            if self.reached_end:
                return (len(female_to_female), len(female_to_female))
            for i in range(self.left_marker, len(female_to_female)):
                line_n = female_to_female[i]
                if line_n >= end:
                    line_range = (self.left_marker, i)
                    self.left_marker = i
                    return line_range
            self.reached_end = True
            return (self.left_marker, len(female_to_female))

    lines_by_scene = LinesByScenes()
    female_lines_by_scene = [ lines_by_scene(female_to_female, end) for _ ,
            end in act_scene_start_end ]
    return female_lines_by_scene

def bechdel_by_scene(start, end, female_to_female, play_lines,
        males):
    forbidden_matcher = create_forbidden_matcher(males)
    # if start == end, this means the scene contains no dialgoue.
    if start == end:
        return False
    notable_females = set()
    # Test forbidden match and keep track of females in the scene
    for i in range(start, end):
        line_i = female_to_female[i]
        line = play_lines[line_i]
        # First Test : forbidden match
        forbidden_match = forbidden_matcher.search(line.dialogue)
        if forbidden_match:
            # print("forbidden_match : ", forbidden_match)
            return False
        notable_females.add(line.character)
    # Return true only if notable females speaking are greater than 1
    return len(notable_females) > 1

def create_forbidden_matcher(males):
    icky = ['sex', 'sexual', 'intercourse', 'marriage', 'matrimony','courting',
            'love', 'wedlock']
    boyfriend = ['boyfriend', 'partner', 'husband', 'spouse', 'lover',
            'admirer', 'fiancé', 'amour', 'inamorato']
    forbidden_words = icky + boyfriend + list(males)
    return get_matcher(forbidden_words, "forbidden")

# VOCAB DIFFERENCES

def vocab_difference(play_lines, gender):
    """ Return a dict that associates each word with whether it is used more
    frequently by males or females, with negative nummbers being female and
    postive numbers being male. Also returns a list that ranks vocab in the
    play by most female to most male"""
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
    return word_gender, word_gender_sorted

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
    try:
        male_threshold = num_male_words / len(males_vocab)
    except ZeroDivisionError:
        # The 1 is arbitrary as there are no vocab to test against it.
        male_threshold = 1
    try:
        female_threshold = num_female_words / len(female_vocab)
    except ZeroDivisionError:
        # The 1 is arbitrary as there are no vocab to test against it.
        female_threshold = 1
    def get_ratio(m_num, f_num):
        try:
            norm_m_num = m_num / num_male_words
        except ZeroDivisionError:
            norm_m_num  = 0
        try:
            norm_f_num = f_num / num_female_words
        except ZeroDivisionError:
            norm_f_num = 0
        diff = norm_m_num - norm_f_num
        _sum = norm_m_num + norm_f_num
        ratio = diff / _sum
        return ratio
    def get_word_gender(word):
        """Assign vocab a gender value only if it used more often than the
        average word"""
        m_num = males_vocab.get(word, 0)
        f_num = female_vocab.get(word, 0)
        meet_threshold = m_num > male_threshold or f_num > female_threshold 
        metric = get_ratio(m_num, f_num) if meet_threshold else 0
        return metric
    return get_word_gender

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
            reciprocal_graph,
            )
    vocab_difference(play_lines, gender)
    bechdel_scenes = bechdel_test(play_lines, characters_by_importance, adj,
            gender, act_scene_start_end)
    return graph
