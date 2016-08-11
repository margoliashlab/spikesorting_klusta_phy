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

Supposing you have [dspflow](https://github.com/kylerbrown/dspflow), you can used the preprocessing script included in this repo. In the script, you modify the appropriate values, such as filename, and also select entries and channels you want to analyze. If you don't specify entries, then it will take all entries (though sometimes you might have some junk entries or top-level datasets, then it won't work). You have to specify datasets manually, because it's very likely that you will have some non-continuous datasets.

To make that easier, use `python listlist.py ` to list all entries, and then all datasets from the first entry - that should help you, because you only need to delete the one you don't want, and paste them to your preprocessing script.

Also it's important that you pay attention to the datatype! If you filter data as part of your preprocessing, then it's converted to floats, so for example if originally your data was in `int16`, then you might want to convert them back, for example `sig.filtfilt(filtExtracel_b, filtExtracel_a, chunk).astype('int16'))`. 

 
 ### Probe file

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
   
However, it gets more complicated if you have multishank data. Suppose you have 32 channels,
8 per shank (and the rest doesn't appear in that shank's graph). Then the rest are "dead channels", and theoretically klusta should disregard them from spike sorting for that shank - however, that doesn't seem to be the case? In some files Kyler used before, for each shank you need to list all the channels that are in your .dat files, regardless if they are dead in this shank or not. So if you have 30 channels, then `channels = list(range(30))`. Otherwise phy won't load your data. However, then processing takes much (much) longer. Another thing you could do is to just process one shank at a time. But then channels have to be for example `[0,1,2,3,..7]`, not `[23,10,5...,17]`, otherwise you'll get an error. So in the prb file you need to replace, for example, 23 with 0, 10 with 1, and so on. It's pretty annoying. I asked on the [phy-users Google Group](https://groups.google.com/forum/#!topic/phy-users/jbJ-RT5oxJk), maybe they'll respond.

### Parameter file

You also need a parameter file. Here's one that should be good. Save it as `test.prb` (or something). Important parts are: number of channels (take from the output of the preprocessing) script, dtype (!!!), raw_data_files (take that from the output of preprocessing). 

We filtered the data on our own, because otherwise if you visualize the data it's too messy to see anything. However, klustakwik also filters the data (with a low-pass filter?) Therefore we want to change its filtering parameters `filter_low=100.`, which is smaller than the frequency of the bandpass filter we used in the Python script, and `filter_butter_order=1`. I don't know. Sofija suggested that, so maybe ask her. It doesn't seem like there's an option to turn off filtering, but maybe there is one? Spike detection program is called spikedetekt, but it doesn't seem well documented.

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

To scale the waveform in TraceView, use your right mouse button. The Increase/Narrow in the menu doesn't work for single channel data (that's what they told me on the mailing list). You can look at PCA in FeatureView, for example selecting a few clusters at once. Then you might want to cut out a part of the cluster (repeated ctrl+click creates a polygon), then Split the cluster and maybe Merge with some other cluster. _Remember to save_, otherwise it's all gone (Clustering -> Save).

### Putting the results back into your arf file

Use the postprocessing script included here. You should only need to change paths of the files. If you have more than one shank in your prb file, then you will have multiple channel groups. Either run the script a few times, changing 0 to 1 etc. in the `channel_group_prefix`, or do a for loop.

The script will put spikes corresponding to each entry into that entry, as dataset of name `dset_name`. You could add commandline option parsing, to make it easier. So if you want to have multiple channel groups, you need to change the name. Of course be careful, because once you add a dataset to an arf file, it's hard to get rid of it. Maybe backup you data first. And then you can look at your spikes in arfview!