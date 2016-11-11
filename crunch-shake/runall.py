import sys
import run

for play in sys.argv[1:]:
    print(play)
    run.run(play)
