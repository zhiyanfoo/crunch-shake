# Computational plays

### Using statistics to interpret plays 

The following (still-in-progress) library contains tools to analyze plays
computationally. So far the focus has been on Shakespeare's plays, particularly
the ones found on the [MIT website](http://shakespeare.mit.edu/) which is
marked up in HTML and convenient-ish to parse.

### The Bechdel Test

The most successful metric that has been applied to art I believe is the
[Bechdel Test](https://en.wikipedia.org/wiki/Bechdel_test). The tests asks
whether "a work of fiction features at least two women who talk to each other
about something other than a man." This is not a high bar, but the amount of
movies that have failed this test is surprising, and informative of the current
gender disparities that exists in the film industry. This effect can be
dismissed if looking at any certain movie - A male centric movie by itself does
not imply institutional sexism - but the overall trend shows us the status of
the medium as a whole. 

### Focus of this project
The focus of most of the analysis is in the same vein as the Bechdel test but
on plays. Gender disparity is not the exclusive focus of this project, however,
literary and stylistic analysis will also be a touched upon.

Why were plays chosen as the medium of interest? When analysing plays, it is
easy to get meta information from the text, such as which character speaks
which dialogue, to whom he or she is speaking to and the scenes the different
characters are in. As such compared to poems and prose, it is easier to
computationally analyze plays.

Feel free to submit patches with ideas to IDEAS.md on what type of analysis to
do and how to perform said analysis.

### DEPENDENCIES

NetworkX and PyGraphviz

Both available through pip

### LICENSE

MIT License; see LICENSE.
