from subprocess import Popen, PIPE

def to_dot(edges_list, directed=False):
    str_templates = {
            "dir" : ("  {0} -> {1}", "digraph {\n"), 
            "undir" : ("  {0} -- {1}", "graph {\n") 
            }
    str_template, first_line = str_templates["dir"] if directed else str_templates["undir"]
    # +1 so that vertices start from 1 instead of 0
    body_str = "\n".join([ str_template.format(edge[0]+1, edge[1]+1)
        for edge in edges_list ])
    last_line = "\n}"
    dot_str = first_line + body_str + last_line
    return dot_str

def to_dot_dir(edges_list):
    """
    graph {
      1 -> 2
      2 -> 3
      3 -> 4
      1 -> 4
      1 -> 5
      5 -> 4
    }
    """
    str_template = "  {0} -> {1}"
    # +1 so that vertices start from 1 instead of 0
    body_str = "\n".join([ str_template.format(edge[0]+1, edge[1]+1)
        for edge in edges_list ])
    first_line = "digraph {\n"
    last_line = "\n}"
    dot_str = first_line + body_str + last_line
    return dot_str

def create_image(dot_str, image_filename):
    byte_dot = dot_str.encode('utf-8')
    cmd = ['dot', '-Tpng', '-o{0}'.format(image_filename)]
    p = Popen(cmd, stdin=PIPE)    
    p.communicate(input=byte_dot)
