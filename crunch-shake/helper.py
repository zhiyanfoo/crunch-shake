from urllib.request import urlopen
import glob

from parse import get_speaking_characters
from mit_shakespeare_regex import matcher
from utils import file_to_list, to_json, str_to_file


def blank_gender_files():
    names_plays = glob.glob("plays/*.html")
    for name in names_plays:
        play = file_to_list(name)
        speaking_characters = get_speaking_characters(play, matcher.character)
        # print(speaking_characters)
        speaking_characters_dict = dict.fromkeys(speaking_characters, "M")
        json_name = name[:-len("html")] + "gender"
        to_json(speaking_characters_dict, json_name)
        print(json_name)

def get_html(names):
    li_names = names.strip().split("\n")
    print(li_names)
    for name in li_names[-3:-2]:
        url = "http://shakespeare.mit.edu/" + name + "/full.html"
        print(url)
        html = urlopen(url).read().decode('utf-8')
        str_to_file(html, "plays/" + name + ".html")

def main():
    # get_html(names)
    blank_gender_files()
    pass
        
names = """
allswell
asyoulikeit
comedy_errors
cymbeline
lll
measure
merry_wives
merchant
midsummer
much_ado
pericles
taming_shrew
tempest
troilus_cressida
twelfth_night
two_gentlemen
winters_tale
1henryiv
2henryiv
henryv
1henryvi
2henryvi
3henryvi
henryviii
john
richardii
richardiii
cleopatra
coriolanus
hamlet
julius_caesar
lear
macbeth
othello
romeo_juliet
timon
titus
"""

if __name__ == "__main__":
    main()

