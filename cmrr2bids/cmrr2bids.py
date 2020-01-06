#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""


"""

import numpy as np
from pathlib import Path
from os.path import join as opj
import json
import os
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter

from .cmrr2log import Cmrr2Log
from .reading import read_log_file
from .utils import create_record_dict

class Cmrr2Bids(object):
    
    def __init__(self, 
                 input_dcm,  
                 participant_label,
                 sampling_frequency,
                 basename = '',
                 bids_dir = '',
                 session_label = '',
                 ):
        
        self.input_dcm = input_dcm
        self.basename = basename
        self.participant_label = participant_label
        self.session_label = session_label
        self.sampling_frequency = float(sampling_frequency)
        self.bids_dir = bids_dir
            
        # Create  output_dir
        if session_label:   
            path_output = Path(opj(bids_dir, "sub-" + participant_label,
                                   "ses-" + session_label, "func"))
        else:
            path_output = Path(opj(bids_dir, "sub-" + participant_label,
                                   "func"))
            
        path_output.mkdir(parents = True, exist_ok = True)
    
        self.output_dir = path_output.as_posix()
        
    def run(self):
       cmrr2log = Cmrr2Log(input_dcm = self.input_dcm,
                           output_dir = self.bids_dir)
       
       # Run cmrr2log to generate the log files
       cmrr2log.run()
       
       basename = self.__get_basename()
       
       #Retrieve log files
       log_files = cmrr2log.logFiles
       
       info_log_file = ''
       for file in log_files:
           if 'Info' in file:
               info_log_file = file
               
       acq, params = read_log_file(info_log_file, 'ACQUISITION_INFO', 'EJA_1', 0, 0)
       start_acq_time = acq[0, 0]/self.sampling_frequency
        
       first_tck_time = params['FirstTime']
       last_tck_time = params['LastTime']
       if last_tck_time <= first_tck_time:
           raise ValueError('Last timestamp is not greater than first timestamp, aborting...')
       actual_samples = last_tck_time - first_tck_time + 1 
       expected_samples = actual_samples + 8 # some padding at the end for worst case EXT sample at last timestamp    
       
       # Remove log file
       os.unlink(info_log_file)

       for file in log_files:
           # create cardiac files
           if 'ECG' in file:
               acq, params = read_log_file(file, 'ECG', 'EJA_1', first_tck_time, expected_samples)
               signal = acq[:, 1:]
               start_time = acq[0, 0]/self.sampling_frequency - start_acq_time
               recording_sampling = self.sampling_frequency/params['SampleTime']
               record_dict = create_record_dict(signal,  
                                                'cardiac', 
                                                start_time, 
                                                recording_sampling)
               
               #save signal
               np.savetxt(opj(self.output_dir, basename + '_recording-cardiac_physio.tsv.gz'),
                          signal, fmt = '%.3f',
                          delimiter='\t')
               #save json 
               with open(opj(self.output_dir, basename + '_recording-cardiac_physio.json'), 'w') as f:
                   json.dump(record_dict, f, indent=4)
               
               # Remove log file
               os.unlink(file)

           # create respiratory files    
           elif 'RESP' in file:
               acq, params = read_log_file(file, 'RESP', 'EJA_1', first_tck_time, expected_samples)
               signal = acq[:, 1:]
               start_time = acq[0, 0]/self.sampling_frequency - start_acq_time
               recording_sampling = self.sampling_frequency/params['SampleTime']
               record_dict = create_record_dict(signal, 
                                                'respiratory', 
                                                start_time, 
                                                recording_sampling)
               
               #save signal
               np.savetxt(opj(self.output_dir, basename + '_recording-respiratory_physio.tsv.gz'),
                          signal, fmt = '%.3f',
                          delimiter='\t')
               
               #save json file
               with open(opj(self.output_dir, basename + '_recording-respiratory_physio.json'), 'w') as f:
                   json.dump(record_dict, f, indent=4)
               
                # Remove log file
               os.unlink(file)

           # create pulse files        
           elif 'PULS' in file:
               acq, params = read_log_file(file, 'PULS', 'EJA_1', first_tck_time, expected_samples)
               signal = acq[:, 1:]
               start_time = acq[0, 0]/self.sampling_frequency - start_acq_time
               recording_sampling = self.sampling_frequency/params['SampleTime']
               record_dict= create_record_dict(signal, 
                                               'pulse', 
                                               start_time, 
                                               recording_sampling)
               #save signal
               np.savetxt(opj(self.output_dir, basename + '_recording-pulse_physio.tsv.gz'),
                          signal, fmt = '%.3f',
                          delimiter='\t')
               
               #save json file
               with open(opj(self.output_dir, basename + '_recording-pulse_physio.json'), 'w') as f:
                   json.dump(record_dict, f, indent=4)
               
               # Remove log file
               os.unlink(file)

   
    def __get_basename(self):
        
        # Prepend sub and session label        
        basename = "sub-" + self.participant_label
        
        if self.session_label:
            basename = basename + "_ses-" + self.session_label    

        #Prepend to input basename            
        basename = basename + "_" + self.basename
        
        return basename
    

def get_parser():
    
    parser = ArgumentParser(description='cmrr2bids',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    
    parser.add_argument('input_dcm', 
                        action='store', 
                        type=Path,
                        help='the input dicom file')
    
    parser.add_argument('-p', 
                        dest='participant_label', 
                        type=str,
                        required=True,
                        help='participant label')
    
    parser.add_argument('--freq', 
                        dest='sampling_frequency', 
                        type=float,
                        required=True,
                        help='sampling frequency')
    parser.add_argument('--name', 
                        dest = 'basename',
                        type=str,
                        help='basename to preprend participant and session labels')
                 
    parser.add_argument('--bids_dir', action='store', type=Path,
                        help='the output path for the outcome physio files')
    
    parser.add_argument('-s', 
                        dest='session_label', 
                        type=str,
                        help='Session Label')
    
    return parser
    

    
def main():
    """
    main function
    
    """
    opts = get_parser().parse_args()
    
    if opts.bids_dir:
        opts.bids_dir = opts.bids_dir.absolute().as_posix()
    else:
        # output_dir same as the same directory of the input dicom
        opts.bids_dir = Path(opts.input_dcm).parent.absolute().as_posix()
    
    cmrr2bids = Cmrr2Bids(input_dcm = opts.input_dcm,
                          bids_dir = opts.bids_dir,
                          participant_label = opts.participant_label,
                          session_label = opts.session_label,
                          basename=opts.basename,
                          sampling_frequency = opts.sampling_frequency,
                          )

    cmrr2bids.run()

if __name__ == '__main__':
    main()
    
    
        
        
        
        