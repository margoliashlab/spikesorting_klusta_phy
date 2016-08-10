# Lets you pick channels, then gets them for each entry in the file,
# then processes them and saves to .dat files with names the same as entries.
# Also outputs the line you should paste into the .prm file of klusta as raw_data_files.
# You should do everything in one directory (arf file, dat files, .prm and .prb files).
from Stream import Stream, ArfStreamer, DatStreamer
import scipy.signal as sig


sample_rate = 30000
fN = sample_rate/2
freq_norm = [500/fN, 10000/fN]
filtExtracel_b, filtExtracel_a =\
        sig.butter(2, freq_norm, btype='bandpass', output='ba')

chunk_size = 1000000

filename = "/home/mbadura/recordings/entries.arf"
channels_to_save = ['0', '1'] # names of the datasets in each entry that you want to save

outfiles_prefix = 'entries_data/'


with ArfStreamer(filename) as data:
    # data.file wraps the h5py object that we read data from
    entries = [entry for entry in data.file] # can modify it to pick only the ones you want
    print(entries)
    outfiles = []
    for entry in entries:
        channels = [entry + '/' + chan for chan in channels_to_save]
        stream = data.stream_channels(channels)
        # represented as columns in the order they were specified in channels_to_save
        stream = (
            stream.map(lambda chunk:
                        chunk[:,0]-chunk[:,1])
                .map(lambda chunk:
                    sig.filtfilt(filtExtracel_b, filtExtracel_a, chunk).astype('int16'))
            )
        outfile = outfiles_prefix + entry + '.dat'
        DatStreamer.save(stream, outfile)
        outfiles.append(entry+'.dat')

print('This is the list of your entries, paste that into your .prm file:')
print(outfiles)