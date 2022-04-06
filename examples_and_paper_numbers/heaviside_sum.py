#class to store a sum of heaviside functions representing intervals

import random
from bisect import bisect_left
import numpy as np
from copy import deepcopy

class SumHeavisides():
    def __init__(self):
        self.interval_limits = []
        self.amplitude_change = []
        self.cumsum_valid = False
        self.cumsum = None
    
    def add_heaviside(self, a, b, amplitude):
        if a>b:
            temp = b
            b = a
            a = temp
        index_insert_a = bisect_left(self.interval_limits, a)
        self.interval_limits.insert(index_insert_a, a)
        self.amplitude_change.insert(index_insert_a, amplitude)
        index_insert_b = bisect_left(self.interval_limits, b)
        self.interval_limits.insert(index_insert_b, b)
        self.amplitude_change.insert(index_insert_b, -amplitude)
        
        self.cumsum_valid = False
    
    def get_fn_at(self, x):
        if not self.cumsum_valid:
            self.cumsum = np.cumsum(self.amplitude_change)
            self.cumsum_valid = True
        index_search = bisect_left(self.interval_limits, x)
        return self.cumsum[index_search-1]
    
    def get_fn_at_interval(self, x, interval_width):
        if len(self.amplitude_change)==0:
            return 0.
        
        if not self.cumsum_valid:
            self.cumsum = np.cumsum(self.amplitude_change)
            self.cumsum_valid = True
        index_search = bisect_left(self.interval_limits, x-interval_width/2)
        previous_interval = x-interval_width/2
        total_amplitude = 0.
        total_interval = 0.
        total_points = 0
        while index_search+1<len(self.interval_limits) and self.interval_limits[index_search]<x+interval_width/2:
            current_interval = self.interval_limits[index_search]
            total_amplitude += self.cumsum[index_search-1]*(current_interval-previous_interval)
            total_interval +=(current_interval-previous_interval)
            previous_interval = current_interval
            index_search += 1
            total_points += 1
        total_amplitude += self.cumsum[index_search-1]*(x+interval_width/2-previous_interval)
        total_interval +=(x+interval_width/2-previous_interval)
        total_points += 1
        return total_amplitude/total_interval, total_points
    
    def join_heaviside(self, other_heaviside):
        res = []
        res_amp = []
        l1 = deepcopy(self.interval_limits)
        l2 = deepcopy(other_heaviside.interval_limits)
        l1_amp = deepcopy(self.amplitude_change)
        l2_amp = deepcopy(other_heaviside.amplitude_change)
        while l1 and l2:
            if l1[0] < l2[0]:
                res.append(l1.pop(0))
                res_amp.append(l1_amp.pop(0))
            else:
                res.append(l2.pop(0))
                res_amp.append(l2_amp.pop(0))
        res += l1
        res += l2
        res_amp += l1_amp
        res_amp += l2_amp
        self.interval_limits = res
        self.amplitude_change = res_amp
        self.cumsum_valid = False
    
    def apply_fn_to_amplitudes(self, fn):
        for index in range(len(self.amplitude_change)):
            self.amplitude_change[index] = fn(self.amplitude_change[index])
