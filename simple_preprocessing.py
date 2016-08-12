# For very simple spike sorting or a test run - lets you pick a bunch of datasets,
# and saves them to a .dat file.

from dspflow import Stream, ArfStreamer, DatStreamer
import scipy.signal as sig

filename = "/home/mbadura/neuro/spikesorting/long.arf"
outfile = "no_merge.dat"

electrode_path = "/0/5"
uncoated_path = "/0/6"

sample_rate = 30000
chunk_size = 1000000

fN = sample_rate/2

with ArfStreamer(filename) as data:
    freq_norm = [500/fN, 10000/fN]

    filtExtracel_b, filtExtracel_a =\
        sig.butter(2, freq_norm, btype='bandpass', output='ba')

    vals = data.stream_channels([electrode_path, uncoated_path], chunk_size)
    refd = (
        vals.map(lambda chunk:
                         chunk[:,0]-chunk[:,1])
            .map(lambda chunk:
                sig.filtfilt(filtExtracel_b, filtExtracel_a, chunk).astype('int16'))
    )

    DatStreamer.save(refd, outfile)