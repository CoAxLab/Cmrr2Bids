#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""

def create_record_dict(signal, record_type, start_time, recording_sampling):
    
    import numpy as np
    
    record_dict = dict()
    
    _, n_channels = np.shape(signal)
    
    if n_channels > 1:
        record_dict['Columns'] = [record_type + str(ii) \
                                  for ii in np.arange(1, n_channels + 1)]
    else:
        record_dict['Columns'] = [record_type]
    
    record_dict['StartTime'] = start_time
    record_dict['SamplingFrequency'] = float(recording_sampling)
    
    return record_dict
    

def synchronise_signal(signal, time, sampling_frequency):
    
    """
    Sometimes, physiological sampling does not produce equally spaced 
    samples, which can be problematic when analysing signals separately
    
    This function takes care of this by interpolating the measured values to
    those equally spaced samples given by the recording sampling frequency
    
    """
    
    from scipy.interpolate import interp1d
    import numpy as np
        
    interp = interp1d(time, signal, kind = 'linear', fill_value = 'extrapolate')
    
    n_points, _ = signal.shape
    new_time = np.arange(n_points)/sampling_frequency
    
    return interp(new_time)
