# Lets you pick channels, then gets them for each entry in the file,
# then processes them and saves to .dat files with names the same as entries.
# Also outputs the line you should paste into the .prm file of klusta as raw_data_files.
# You should do everything in one directory (arf file, dat files, .prm and .prb files).
from dspflow import Stream, ArfStreamer, DatStreamer
import scipy.signal as sig


sample_rate = 30000
fN = sample_rate/2
freq_norm = [350/fN, 10000/fN]
filtExtracel_b, filtExtracel_a =\
        sig.butter(2, freq_norm, btype='bandpass', output='ba')

chunk_size = 1000000

filename = "/home/mbadura/neuro/spikesorting/kyler/data.arf"
outfiles_prefix = '/home/mbadura/neuro/spikesorting/kyler/'


# if set to None, will take all entries - but that might cause problems if your file is non-standard
entries_to_save = ['entry1', 'entry2'] #name of entries you want to save 
channels_to_save = ['0', '1'] # names of the datasets in each entry that you want to save





with ArfStreamer(filename) as data:
    # data.file wraps the h5py object that we read data from
    if entries_to_save == None:
        entries = [entry for entry in data.file]    
    else:
        entries = entries_to_save
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
        # mind the dtype! you will have to specify it in the .prm file as well
        # also when you filter, it gives you a float, so if you had ints,
        # you need to convert back
        outfile = outfiles_prefix + entry + '.dat'
        DatStreamer.save(stream, outfile)
        outfiles.append(entry+'.dat')

print('This is the list of your entries, paste that into your .prm file:')
print('raw_data_files='+str(outfiles))
print('nchannels='+str(len(channels)))