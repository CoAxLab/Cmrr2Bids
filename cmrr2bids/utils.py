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
    
    
