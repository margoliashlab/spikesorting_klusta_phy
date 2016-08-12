import h5py
import sys
import os

# Simple tool to help you with getting a list of entries and channels
# you want to perform spike sorting on.

def main(filename):
    with h5py.File(filename) as f:
        entries = sorted(list(f.keys()))
        
        datasets = None
        for e in entries:
            try:
                entry = f[e]
                datasets = sorted(list(entry.keys()))
                if len(datasets) > 0:
                    break
            except:
                pass

        print('Entries in {0}:'.format(filename))
        print(entries)
        print('\n Datasets in {0}:'.format(entry))
        print(datasets)


if __name__ == '__main__':
    filename = sys.argv[1]
    if not os.path.isfile(filename):
        print("USAGE: listlist.py filename")
    else:
        main(filename)
