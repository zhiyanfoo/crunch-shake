import re

from utils import Matcher

"""
MIT SHAKESPEARE MATCHERS
========================

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
STAGE_DIRECTION_MATCHER = re.compile(STAGE_DIRECTION_PATTERN, re.IGNORECASE)

INSTRUCTION_PATTERN = r're-enter|enter|exit|exeunt|aside|read|to'
INSTRUCTION_MATCHER = re.compile(
        INSTRUCTION_PATTERN,
        re.IGNORECASE
        )

ACT_PATTERN = r"<h3>act (?P<act>[IVX]+).*</h3>"
ACT_MATCHER = re.compile(ACT_PATTERN, re.IGNORECASE)

SCENE_PATTERN = r"<h3>scene (?P<scene>[IVX]+).*</h3>"
SCENE_MATCHER = re.compile(SCENE_PATTERN, re.IGNORECASE)

matcher = Matcher(DIALOGUE_MATCHER, CHARACTER_MATCHER, STAGE_DIRECTION_MATCHER,
        INSTRUCTION_MATCHER, ACT_MATCHER, SCENE_MATCHER)
