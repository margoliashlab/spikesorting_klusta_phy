# Takes a .kwik file after spike sorting and manual tweaking of clusters.
# Pick the clusters you marked as good, and saves them to the arf file specified,
# spike from each dat file are saved to an .arf entry with of the same name.
# Thus it is necessary that infile here is the same file from which you generated the .dat
# files in the first place.
import h5py
import numpy as np

def get_good_clusters(kwik, channel_group_prefix):
    ''' Returns indinces of clusters that are in the Good group.
        `kwik` is an open h5py File
    '''
    # first let's get the cluster group index of "Good" clusters
    cluster_groups = kwik[channel_group_prefix + '/cluster_groups/main']
    good_idx = None
    for (name, dst) in cluster_groups.items():
        if dst.attrs['name'][0] == b'Good':
            good_idx = int(name)
    if good_idx == None:
        raise ValueError('Couldn\'t find the Good cluster group')    

    # now let's get the indices of clusters belonging to Good
    clusters = kwik[channel_group_prefix + '/clusters/main']
    good_clusters = []
    for (name, grp) in clusters.items():
        if grp.attrs['cluster_group'] == good_idx:
            good_clusters.append(int(name))
    return good_clusters


def get_recordings(kwik):
    ''' Return names of recordings that spike sorting was performed on, by looking at
        the names of the dat files. They should correspond to entries in the original
        arf file
    '''
    recording_names = []
    for (name, grp) in kwik['/recordings'].items():
        rec_name = grp['raw'].attrs['dat_path'][0].decode() # from bytestring to normal string
        rec_name = rec_name[:-len('.dat')] # get rid of the extension
        recording_names.append(rec_name)
    return recording_names


def get_data_by_recording(kwik, channel_group_prefix, good_clusters, recording_names):
    ''' Return a dict mapping recording names to spike data from that recording,
        and taking only the good clusters
    '''
    sample_rate = kwik['/application_data/spikedetekt/'].attrs['sample_rate']
    cluster_nums = kwik[channel_group_prefix + '/spikes/clusters/main']
    time_samples = kwik[channel_group_prefix + '/spikes/time_samples']
    times = time_samples / sample_rate # convert to seconds
    recording_nums = kwik[channel_group_prefix + '/spikes/recording']

    grouped_by_recording = { rec : [] for rec in recording_names }
    for (cluster_num, time, recording_num) in zip(cluster_nums, times, recording_nums):
        if cluster_num in good_clusters:
            grouped_by_recording[recording_names[recording_num]].append((time, cluster_num))

    return grouped_by_recording

def save(arfname, grouped_by_recording, dset_name):
    ''' Save spike data to entries in the arf file, according to the recording names
        which are the keys in the `grouped_by_recording` dict
    '''
    datatype = np.dtype([('start', np.float64), ('cluster', np.int16)])
    with h5py.File(arfname) as arffile:
        for (rec, vals) in grouped_by_recording.items():
            data = np.array(vals, dtype=datatype)
            dset = arffile[rec].create_dataset(dset_name, data=data)
            dset.attrs['datatype'] = 1001 # spike event times type in arf
            dset.attrs['units'] = 's'


def from_kwik_to_arf(kwikname, arfname, channel_group_prefix, dset_name):
    ''' Saves good clusters from the kwik file to the arf file.
        The files are tied to each other, because to spike sort you
        need to use the other script. Performs that for a channel group
        in the kwik file, and saves a dataset to each entry in the arf file
        with name `dset_name`
    '''
    with h5py.File(kwikname) as kwik:
        good_clusters = get_good_clusters(kwik, channel_group_prefix)
        recording_names = get_recordings(kwik)
        grouped_data = get_data_by_recording(kwik, channel_group_prefix,
            good_clusters, recording_names)
        save(arfname, grouped_data, dset_name)

if __name__ == '__main__':
    kwikname = '/home/mbadura/neuro/spikesorting/parts/parts.kwik'
    arfname = '/home/mbadura/neuro/spikesorting/parts/parts.arf'

    channel_group_prefix = '/channel_groups/0'
    dset_name = 'klusta_spikes' 
    # if you have more than one channel group, probably make a for-loop with
    # a different name each time
    from_kwik_to_arf(kwikname, arfname, channel_group_prefix, dset_name)

