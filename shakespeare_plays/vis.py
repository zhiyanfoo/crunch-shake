def get_vis(adjacent):
    edges = [ (character, other_character, adjacent[character][other_character])
            for character in adjacent 
            for other_character in adjacent[character] 
            ]
    char_ids = give_id(adjacent)
    vis_nodes = get_vis_nodes(char_ids)
    vis_edges = get_vis_edges(edges, char_ids)
    return vis_nodes, vis_edges

def get_vis_edges(edges, char_ids):
    # "{from: 1, to: 3, width: 5, arrows:'to'},"
    vis_edges = [ { 
        "from" : char_ids[edge[0]], 
        "to" : char_ids[edge[1]],
        "width" : edge[2],
        "arrows" : "to"
        }
            for edge in edges ]
    return vis_edges

def get_vis_nodes(char_ids):
    # {id: 0, label: 'ROMEO'}}
    vis_nodes = [ { 
        "id" : char_ids[char],
        "label" : char
        }
            for char in char_ids ]
    return vis_nodes

def give_id(adjacent):
    i = 0
    char_ids = dict()
    for character in adjacent:
        char_ids[character] = i 
        i += 1
    return char_ids
