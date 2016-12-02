import sys
import os

import run
import glob

plays = glob.glob(os.path.join(sys.argv[1], "*.html"))
stats = {}
for play in plays[:]:
    run.run(play, stats)

def processing(stats):
    print(stats)
    for play_name in stats:
        play = stats[play_name]
        play['female fail'] = play['scenes'] - play['female passes'] 
        play['male fail'] = play['scenes'] - play['male passes'] 
        play['female fail %'] = 100 * play['female fail'] / play['scenes']
        play['male fail %'] = 100 * play['male fail'] / play['scenes']
        play['no female'] = play['female fail'] - play['female blacklist']
        play['no male'] = play['male fail'] - play['male blacklist']
        play['no female %'] = 100 * play['no female'] / play['scenes']
        play['no male %'] = 100 * play['no male'] / play['scenes']
        play['female passes %'] = 100 * play['female passes'] / play['scenes']
        play['male passes %'] = 100 * play['male passes'] / play['scenes']
        play['notable'] = play['female notable'] + play['male notable']
        play['notable female %'] = 100 * play['female notable'] \
            / play['notable']
        play['notable male %'] = 100 * play['male notable'] \
            / play['notable']
        play['female blacklist %'] = 100 * play['female blacklist'] \
                / play['scenes']
        play['male blacklist %'] = 100 * play['male blacklist'] / play['scenes']
    ranking = sorted(stats.values(), key=lambda play: play['female fail %'])
    return ranking

def presentation(ranking):
    print("Title, Bechdel Pass (Female) %, Bechdel Pass (Male) %, Notable" \
    "Females %, Notable Males %, Blacklisted (Female)%, Blacklisted (Male)%")
    # metrics = ['female passes %', 'male passes %', 'notable female %',
    #         'notable male %', 'female blacklist %', 'male blacklist %']
    metrics = ['female fail %', 'male fail %', 'no female %', 'no male %',
            'female blacklist %', 'male blacklist %']
    for i, play in enumerate(ranking):
        num = " & ".join( [str(i + 1)] + [ '"' + play['title'] + '"'] +
                ["{0:.2f}".format(play[x]) for x in metrics] ) + r' \\ \hline'
        print(num)

def averages(ranking):
    num_scenes = sum(play['scenes'] for play in ranking)
    # num_fail_males = sum(play['male fail'] for play in ranking)
    num_fail_males = sum(play['male blacklist'] for play in ranking)
    # num_fail_female = sum(play['female fail'] for play in ranking)
    num_fail_females = sum(play['female blacklist'] for play in ranking)
    # print(num_fail_males/ num_scenes)
    # print(num_fail_females/ num_scenes)
    num_male_passes = sum(play['male passes'] for play in ranking)
    num_female_passes = sum(play['female passes'] for play in ranking)
    # print(num_fail_males/(num_fail_males + num_male_passes))
    # print(num_fail_females/(num_fail_females + num_female_passes))
    num_no_male  = sum(play['no male'] for play in ranking)
    num_no_female  = sum(play['no female'] for play in ranking)
    print(num_no_male/num_scenes)
    print(num_no_female/num_scenes)





ranking = processing(stats)
# print(ranking)
averages(ranking)
# presentation(ranking)
