#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""


import numpy as np    

def read_log_file(file, log_data_type, expected_version, first_time, expected_samples):
    
    print('Reading %s file...' % log_data_type);
    fp = open(file)
    in_data = fp.readlines() 
    fp.close()
    
    #TODO: See how to put this in a more pythonic way
    varargout = dict()
    
    # echoes parameter was not added until R015a, so prefill a default value
    # for compatibility with older data
    num_echoes = np.uint16(1)
    varargout['NumEchoes'] = num_echoes

    times, arr = [], []

    for line in in_data:
        line = line.strip()
        
        #strip any comments
        if line.find("#") > 0:
            c_test = line.find("#")
            line = line[:c_test]                  
        
        if "=" in line:
            # this is an assigned value; parse it
            var_name, value = line.split("=")
            var_name = var_name.strip()
            value = value.strip()
            #varargout{1} = value;
            if var_name == 'UUID':
                varargout[var_name] = value
                
            if var_name == 'LogVersion':
                if value != expected_version:
                    raise ValueError('File format %s not supported'
                               'by this function (expected %s).' % value, expected_version)
                    
            if var_name == 'LogDataType':
                if value != log_data_type:
                    raise ValueError('Expected %s data,'
                               'found %s? Check filenames?.' % log_data_type, value)
                    
            if var_name == 'SampleTime':
                if log_data_type == 'ACQUISITION_INFO':
                    raise ValueError('Invalid %s parameter found' % var_name)
                sample_time = np.int16(float(value))
                varargout[var_name] = sample_time

            if var_name == 'NumSlices':
                if log_data_type != 'ACQUISITION_INFO':
                    raise ValueError('Invalid %s parameter found' % var_name)
                num_slices = np.int16(float(value))
                varargout[var_name] = num_slices
                
            if var_name == 'NumVolumes':
                if log_data_type != 'ACQUISITION_INFO':
                    raise ValueError('Invalid %s parameter found' % var_name)
                num_volumes = np.int16(float(value))
                varargout[var_name] = num_volumes
                
            if var_name == 'FirstTime':
                if log_data_type != 'ACQUISITION_INFO':
                    raise ValueError('Invalid %s parameter found' % var_name)
                first_time = np.int32(float(value))
                varargout[var_name] = first_time
                
            if var_name == 'LastTime':
                if log_data_type != 'ACQUISITION_INFO':
                    raise ValueError('Invalid %s parameter found' % var_name)
                last_time = np.int32(float(value))
                varargout[var_name] = last_time
            
            if var_name == 'NumEchoes':
                if log_data_type != 'ACQUISITION_INFO':
                    raise ValueError('Invalid %s parameter found' % var_name)
                num_echoes = np.int16(float(value))
                varargout[var_name] = num_echoes
        
        if line:
            # this must be data; currently it is 3-5 columns so we can
            # parse it easily with textscan
            data_cells = line.split()
            # if the first column isn't numeric, it is probably the header
            try:
                float(data_cells[0])
            except:
                continue
            
            if log_data_type == 'ACQUISITION_INFO':
                if('NumVolumes' not in varargout.keys() or num_volumes < 1
                    or 'NumSlices' not in varargout.keys() or num_slices < 1
                        or 'NumEchoes' not in varargout.keys() or num_echoes < 1):
                            raise ValueError('Failed reading ACQINFO header!')
                            
                if len(arr) == 0:
                    arr = np.zeros(shape=(2, num_volumes, num_slices, num_echoes), 
                                   dtype= np.uint32)
                    
                cur_vol    = np.uint16(float(data_cells[0])) #+ 1
                cur_slc    = np.uint16(float(data_cells[1])) #+ 1
                cur_start  = np.uint32(float(data_cells[2]))
                cur_finish = np.uint32(float(data_cells[3])) 
                
                try:
                    cur_eco = np.uint16(float(data_cells[4])) #+ 1
                    if arr[:, cur_vol, cur_slc, cur_eco].any():
                        raise ValueError('Received duplicate timing data' 
                                   'for vol %d slc %d eco %d!' % (cur_vol, cur_slc, cur_eco)
                                   )
                except:
                    cur_eco = np.uint16(0) #+ 1
                    if arr[:, cur_vol, cur_slc, cur_eco].any():
                        raise ValueError('Received duplicate timing data' 
                                   'for vol %d slc %d (ignore for '
                                   'pre-R015a multi-echo data)!' % (cur_vol, cur_slc)
                                   )
                                 
                
                arr[:, cur_vol, cur_slc, cur_eco] = [cur_start, cur_finish]                        
            else:
                cur_start = np.uint32(float(data_cells[0])) - first_time #+ 1
                cur_channel = data_cells[1]
                cur_value =  np.uint16(float(data_cells[2]))
                
                if log_data_type == 'ECG':
                    if len(arr) == 0:
                        arr = np.zeros(shape = (expected_samples, 4),
                                       dtype = np.uint16)
                        
                        times = np.zeros(shape = expected_samples,
                                       dtype = np.uint32)
                    if cur_channel == 'ECG1':
                        cha_idx = 0
                    elif cur_channel == 'ECG2':
                        cha_idx = 1
                    elif cur_channel == 'ECG3':
                        cha_idx = 2
                    elif cur_channel == 'ECG4':
                        cha_idx = 3
                    else:
                        raise ValueError('Invalid ECG channel ID [%s]' % cur_channel)
                        
                    arr[cur_start, cha_idx] = cur_value #*np.ones(sample_time, np.uint16)
                    times[cur_start] = cur_start
                #TODO: See this source
                elif log_data_type == 'EXT':
#                    if len(arr) == 0:
#                        arr = np.zeros(shape = (expected_samples, 2),
#                                       dtype = np.uint16)
                    temp = np.zeros(2, np.uint16)
                    if cur_channel == 'EXT':
                        cha_idx = 0
                    elif cur_channel == 'EXT2':
                        cha_idx = 1
                    else:
                        raise ValueError('Invalid EXT channel ID [%s]' % cur_channel)
                     #temp[cha_idx]  = cur_value
                    
                else:
                    arr.append(cur_value)
                    times.append(cur_start)
                
                    
    if log_data_type == 'ACQUISITION_INFO':
        arr = arr - first_time
        times = np.arange(np.min(arr), np.max(arr)).reshape(-1, 1)
        arr = np.ones(times.size,  dtype=np.uint16).reshape(-1, 1)
        signal_mat = np.concatenate((times, arr), axis=1)
    elif log_data_type == 'ECG':
        times = times.reshape(-1, 1)
        signal_mat = np.concatenate((times, arr), axis=1)
    else:
        times = np.array(times).reshape(-1, 1)
        arr = np.array(arr).reshape(-1, 1)
        signal_mat = np.concatenate((times, arr), axis=1)
    
    return signal_mat, varargout

    