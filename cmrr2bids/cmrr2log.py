#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""

import subprocess
import shlex
from os.path import join as opj
from glob import glob

class Cmrr2Log(object):
    
    def __init__(self,  
                 input_dcm, 
                 output_dir, 
                 options = '-b n -f {p}'):
        
        self.input_dcm = input_dcm
        self.options = options
        self.output_dir = output_dir
        
        
        
    def run(self):
        
        command = 'cmrr2log {} --output_dir {} {}'
        command = command.format(self.options, 
                                 self.output_dir, 
                                 self.input_dcm)
        
        subprocess.check_output(shlex.split(command))
        
        self.logFiles = glob(opj(self.output_dir, "*.log"))
        