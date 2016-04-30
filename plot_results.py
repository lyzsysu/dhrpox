# plot_results.py
#
# Plot the results of total throughput for each traffic pattern and
# scheduling alogorithm.
#
# by Anh Truong (anhlt92)
# and Ian Walsh (iwalsh)
# for CS 244, Spring 2015

import json
import matplotlib as m
import os
if os.uname()[0] == "Darwin":
    m.use("MacOSX")
else:
    m.use("Agg")

import matplotlib.pyplot as plt

from argparse import ArgumentParser
from math import ceil

RESULTS_DIR = 'results/'

# Keys in the results/*.json dictionaries
DHR_MEAN = 'dhr_mean_gbps'
DHR_STDDEV = 'dhr_stddev_gbps'
ROBUST_MEAN = 'robust_mean_gbps'
ROBUST_STDDEV = 'robust_stddev_gbps'
OBLIVIOUS_MEAN = 'oblivious_mean_gbps'
OBLIVIOUS_STDDEV = 'oblivious_stddev_gbps'

# Plot params
TRAFFICS_PER_ROW = 6
LEGEND_BEST = 0
LEGEND_UPPER_LEFT = 2
LEGEND_CENTER_BOTTOM = 8
BAR_WIDTH = 0.35
OPACITY = 1.0
ERROR_CONFIG = {'ecolor': '0.3'}

parser = ArgumentParser(description='Plotting Hedera results')
parser.add_argument('outfile', type=str, help='Where to save the plot')
args = parser.parse_args()


def load_data():
    """
    Outermost keys are the traffic patterns: 'stride1', 'stag0_0203', etc.
    They are mapped to the results dictionary from results/<traffic>.json.
    """
    data = {}

    for filename in os.listdir(RESULTS_DIR):
        datafile = RESULTS_DIR + filename
        label = filename.replace('.json', '')
        if os.path.isfile(datafile):
            with open(datafile, 'r') as f:
                data[label] = json.load(f)

    return data


def extract_means(data):
    """
    Return two lists of means, ordered by traffic pattern in data's keyset
    """
    means_dhr = []
    means_oblivious = []

    for label in sorted(data):
        if DHR_MEAN in data[label]:
            means_dhr.append(data[label][DHR_MEAN])
        else:
            means_dhr.append(0.0)

        if OBLIVIOUS_MEAN in data[label]:
            means_oblivious.append(data[label][OBLIVIOUS_MEAN])
        else:
            means_oblivious.append(0.0)

    return (means_dhr, means_oblivious)


def extract_stddevs(data):
    """
    Extract two lists of stddevs, ordered by traffic pattern
    """
    stddevs_dhr = []
    stddevs_oblivious = []

    for label in sorted(data):
        if DHR_STDDEV in data[label]:
            stddevs_dhr.append(data[label][DHR_STDDEV])
        else:
            stddevs_dhr.append(0.0)

        if OBLIVIOUS_STDDEV in data[label]:
            stddevs_oblivious.append(data[label][OBLIVIOUS_STDDEV])
        else:
            stddevs_oblivious.append(0.0)

    return (stddevs_dhr, stddevs_oblivious)


def plot(data):
    (means_dhr, means_oblivious) = extract_means(data)
    (stddevs_dhr, stddevs_oblivious) = extract_stddevs(data)
    traffics = sorted(data.keys())

    n_rows = int(ceil(float(len(traffics)) / TRAFFICS_PER_ROW))

    # Plot TRAFFICS_PER_ROW results on each row
    for r in xrange(n_rows):
        lower = r * TRAFFICS_PER_ROW
        upper = r * TRAFFICS_PER_ROW + TRAFFICS_PER_ROW

        # Slice data for this row
        row_dhr_avgs = means_dhr[lower:upper]
        row_dhr_devs = stddevs_dhr[lower:upper]
        row_oblivious_avgs = means_oblivious[lower:upper]
        row_oblivious_devs = stddevs_oblivious[lower:upper]
        row_traffics = traffics[lower:upper]

        index = range(len(row_dhr_avgs))
        index2 = map(lambda x: x + BAR_WIDTH, index)

        plt.subplot(n_rows, 1, r + 1)

        # DHR bars
        plt.bar(index, row_dhr_avgs, BAR_WIDTH,
                alpha=OPACITY,
                color='r',
                yerr=row_dhr_devs,
                error_kw=ERROR_CONFIG,
                label='Dynamic Hybrid Routing')

        # OBLIVIOUS bars
        plt.bar(index2, row_oblivious_avgs, BAR_WIDTH,
                alpha=OPACITY,
                color='g',
                yerr=row_oblivious_devs,
                error_kw=ERROR_CONFIG,
                label='Oblivious Routing')

        plt.xticks(index2, row_traffics)

        if r == 0:
            plt.title('Comparison of scheduling performance')
        elif r == n_rows - 1:
            plt.xlabel('Traffic pattern')

        if r == 1:
            plt.ylabel('Total throughput (Gbps)')

    plt.legend(loc=LEGEND_BEST)

    plt.tight_layout()

    if os.path.exists(args.outfile):
        os.remove(args.outfile)

    plt.savefig(args.outfile)


def main():
    data = load_data()
    plot(data)
    print 'Plot saved to %s!' % args.outfile

if __name__ == '__main__':
    main()
