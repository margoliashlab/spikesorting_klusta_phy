# Spike sorting with klustakwik and phy

## Links
[Phy documentation: covers mostly how to use phy for scripting](http://phy.readthedocs.io])

[Phy on Github: also has installation instructions](https://github.com/kwikteam/phy)

[phy-users mailing list](https://groups.google.com/forum/#!forum/phy-users)

[klusta documentation and example](http://klusta.readthedocs.io/en/latest/)




## Installing the software

Install Anaconda if you don't have it yet. Download the [environment file](https://raw.githubusercontent.com/kwikteam/phy/master/installer/environment.yml). Open the terminal, navigate to the folder with the file, and then type

    conda env create -n phy
    source activate phy  # omit the `source` on Windows
    pip install phy phycontrib

Then every time you want to use the software, type `source activate phy` in the terminal first, to switch to that conda Python environment.

Also maybe you want to install it on kkong (probably makes more sense, considering how long it takes to run it). Then you need to run those commands as well:

    source activate phy
    conda remove klustakwik2
    pip install cython
    pip install klustakwik2

Also include the fix for bug with TraceView normalization, especially if you want to look at single channel data:
    
    pip install git+https://github.com/rossant/phy.git@fix-trace-normalization --upgrade
    
(you can check the status of the [pull request](https://github.com/kwikteam/phy/pull/707), maybe it has been merged to the main version already?)

## Spike sorting with klustakwik

You can find an example, including also example parameter and config files [here](http://klusta.readthedocs.io/en/latest/). But let's say you want to spike sort single electrode data.

### Preparing the data

Supposing you have [dspflow](https://github.com/kylerbrown/dspflow), you can use this script to reference electrode and uncoated channel, then filter it, and save to a .dat file. (Though syntax might change.)

    from Stream import Stream, ArfStreamer, DatStreamer
    import scipy.signal as sig
    
    filename = "/path/to/file/data.arf"
    outfile = "/save/path/test.dat"
    
    electrode_path = "/0/5"
    uncoated_path = "/0/6"
    
    sample_rate = 30000
    chunk_size = 10000000
    
    fN = sample_rate/2
    
    with ArfStreamer(filename) as data:
        freq_norm = [500/fN, 10000/fN]
    
        filtExtracel_b, filtExtracel_a =\
            sig.butter(2, freq_norm, btype='bandpass', output='ba')
    
        elec = data.stream_channel(electrode_path, chunk_size) #electrode channel
        unc = data.stream_channel(uncoated_path, chunk_size) #uncoated channel
        refd = (
            Stream.merge(elec, unc).map(lambda chunk:
                             chunk[:,0]-chunk[:,1])
                .map(lambda chunk:
                    sig.filtfilt(filtExtracel_b, filtExtracel_a, chunk).astype('int16'))
        )
    
        DatStreamer.save(refd, outfile)
 
 ### Get parameter and probe files

Create a new folder, put the .dat file you create in it. It's important that you have a separate folder for each piece of spikesorting you do, because klustakwik creates some intermediate files.

For single channel data, you would use this .prb file. Save it in the folder as `1singleUnit.prb`.

    total_nb_channels = 1
    radius = 00
    channel_groups = {
        0: {
            "channels": list(range(1)),
            "graph" : [],
            "geometry": {
                0: [0, 0]
            }
        }
    }
   
   You also need a parameter file. Here's one that should be good. Save it as `test.prb` (or something).

    experiment_name = 'test' #name of your .dat file
    prb_file = '1singleUnit.prb'
    
    traces = dict(
        raw_data_files=[experiment_name + '.dat'],
        voltage_gain=1.,
        sample_rate=30000,
        n_channels=1,
        dtype='int16',
    )
    
    spikedetekt = dict(
        filter_low=100.,  # Low pass frequency (Hz)
        filter_high_factor=0.95 * .5,
        filter_butter_order=1,  # Order of Butterworth filter.
    
        filter_lfp_low=0,  # LFP filter low-pass frequency
        filter_lfp_high=300,  # LFP filter high-pass frequency
    
        chunk_size_seconds=1,
        chunk_overlap_seconds=.015,
    
        n_excerpts=50,
        excerpt_size_seconds=1,
        threshold_strong_std_factor=4.5,
        threshold_weak_std_factor=2.,
        detect_spikes='negative',
    
        connected_component_join_size=1,
    
        extract_s_before=16,
        extract_s_after=16,
    
        n_features_per_channel=3,  # Number of features per channel.
        pca_n_waveforms_max=10000,
    )
    
    klustakwik2 = dict(
        num_starting_clusters=100,
    )
   
We filtered the data on our own, because otherwise if you visualize the data it's too messy to see anything. However, klustakwik also filters the data (with a low-pass filter?) Therefore we want to change its filtering parameters `filter_low=100.`, which is smaller than the frequency of the bandpass filter we used in the Python script, and `filter_butter_order=1`. I don't know. Sofija suggested that, so maybe ask her. It doesn't seem like there's an option to turn off filtering, but maybe there is one? Spike detection program is called spikedetekt.

### Running klustakwik

Remember to do `source activate phy` first. Then go to the folder with the data and do `klustakwik test.prm`. 

It will take a while; it's probably best to run it at trex. By the way, something useful: use the `screen` commandline program. It lets you create multiple terminal sessions, and connect to them over many SSH sessions, so you don't have to keep the terminal open the whole time. So do

    screen
    source activate phy
    klustakwik test.prm
   
   Then press Ctrl+D to close screen, but it will keep running in the background. Then you can log in by SSH again, do `screen -r` to connect to that sessions again.

### Looking at the results in kwik-gui

I'm not sure if you can do that on trex; I got a GL error. Therefore you might have to use your own computer. Download the .dat, .kwik, .kwx files from your folder. You can also download the entire folder, but that will take longer, because there's some amount of hidden files creating during clustering. Then you can just do
    
    source activate phy
    phy kwik-gui test.kwik

To scale the waveform in TraceView, use your right mouse button. The Increase/Narrow in the menu doesn't work for single channel data (that's what they told me on the mailing list). You can look at PCA in FeatureView, for example selecting a few clusters at once. Then you might want to cut out a part of the cluster (repeated ctrl+click creates a polygon), then Split the cluster and maybe Merge with some other cluster.