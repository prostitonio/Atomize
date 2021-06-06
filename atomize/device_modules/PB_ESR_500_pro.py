#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from copy import deepcopy 
import numpy as np
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','PB_ESR_500_pro_config.ini')

# configuration data
#config = cutil.read_conf_util(path_config_file)
specific_parameters = cutil.read_specific_parameters(path_config_file)

# TO DO
# pulse_shift and pulse_increment only one pulse

timebase_dict = {'s': 1000000000, 'ms': 1000000, 'us': 1000, 'ns': 1,}
channel_dict = {'CH0': 0, 'CH1': 1, 'CH2': 2, 'CH3': 3, 'CH4': 4, 'CH5': 5, \
                'CH6': 6, 'CH7': 7, 'CH8': 8, 'CH9': 9, 'CH10': 10, 'CH11': 11,\
                'CH12': 12, 'CH13': 13, 'CH14': 14, 'CH15': 15, 'CH16': 16, 'CH17': 17,\
                'CH18': 18, 'CH19': 19, 'CH20': 20, 'CH21': 21, }

# Limits and Ranges (depends on the exact model):
clock = float(specific_parameters['clock'])
timebase = int(float(specific_parameters['timebase'])) # in ns
repetition_rate = specific_parameters['default_rep_rate']

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_rep_rate = '2 Hz'

class PB_ESR_500_Pro:
    def __init__(self):
        if test_flag != 'test':
            #pb_core_clock(clock)
            self.pulse_array = []
            self.pulse_array_init = []
            self.rep_rate = (repetition_rate, )
            self.shift_count = 0
            self.increment_count = 0
            self.reset_count = 0
        
        elif test_flag == 'test':
            self.pulse_array = []
            self.pulse_array_init = []
            self.rep_rate = (repetition_rate, )
            self.shift_count = 0
            self.increment_count = 0
            self.reset_count = 0

    # Module functions
    def pulser_name(self):
        if test_flag != 'test':
            answer = 'PB ESR 500 Pro'
            return answer
        elif test_flag == 'test':
            answer = 'PB ESR 500 Pro'
            return answer

    def pulser_pulse(self, channel = 'CH0', start = '0 ns', length = '100 ns', delta_start = '0 ns', length_increment = '0 ns'):
        """
        A function that added a new pulse at specified channel. The possible arguments:
        START, LENGTH, DELTA_START, LENGTH_INCREMENT
        """
        if test_flag != 'test':
            pulse = {'channel': channel, 'start': start, 'length': length, 'delta_start' : delta_start, 'length_increment': length_increment}

            self.pulse_array.append( pulse )
            # for saving the initial pulse_array without increments
            # deepcopy helps to create a TRULY NEW array and not a link to the object
            self.pulse_array_init = deepcopy(self.pulse_array)

        elif test_flag == 'test':

            pulse = {'channel': channel, 'start': start, 'length': length, 'delta_start' : delta_start, 'length_increment': length_increment}
            # Checks
            temp_length = length.split(" ")
            if temp_length[1] in timebase_dict:
                coef = timebase_dict[temp_length[1]]
                p_length = coef*float(temp_length[0])
                assert(p_length >= 0 and p_length < 2000), 'Pulse is longer than maximum available length or negative'

            temp_start = start.split(" ")
            if temp_start[1] in timebase_dict:
                coef = timebase_dict[temp_start[1]]
                p_start = coef*float(temp_start[0])
                assert(p_start >= 0), 'Pulse start is a negative number'
            
            temp_delta_start = delta_start.split(" ")
            if temp_delta_start[1] in timebase_dict:
                coef = timebase_dict[temp_delta_start[1]]
                p_delta_start = coef*float(temp_delta_start[0])
                assert(p_delta_start >= 0), 'Pulse delta start is a negative number'

            temp_length_increment = length_increment.split(" ")
            if temp_length_increment[1] in timebase_dict:
                coef = timebase_dict[temp_length_increment[1]]
                p_length_increment = coef*float(temp_length_increment[0])
                assert (p_length_increment >= 0 and p_length_increment < 2000), \
                'Pulse length increment is longer than maximum available length or negative'

            if channel in channel_dict:
                self.pulse_array.append( pulse )
                # for saving the initial pulse_array without increments
                # deepcopy helps to create a TRULY NEW array and not a link to the object
                self.pulse_array_init = deepcopy(self.pulse_array)
            else:
                assert (1 == 2), 'Incorrect channel name'

    def pulser_update(self, rep_rate = repetition_rate):
        """
        A function that write instructions to SpinAPI. 
        Repetition rate is taking into account by adding
        a last pulse with delay.
        Currently, all pulses are cycled using BRANCH.
        """
        if test_flag != 'test':
            # get repetition rate
            rep_rate = self.rep_rate[0]
            if rep_rate[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate[:-3])/2)
            elif rep_rate[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate[:-4])/2)
            elif rep_rate[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate[:-4])/2)

            if self.reset_count == 0 or self.shift_count == 1 or self.increment_count == 1:
                # using a special functions for convertion to instructions
                to_spinapi = self.instruction_pulse( self.bit_pulse( self.convertion_to_numpy( self.pulse_array ) ), rep_time )
                general.message( to_spinapi )
                #pb_start_programming(PULSE_PROGRAM)
                i = 0
                while i < len( to_spinapi) - 1:
                    #if i == 0: 
                        # to create a link for BRANCH
                        #start = pb_inst(ON | "0x%X" % to_spinapi[i, 0], CONTINUE, 0, "0x%X" % to_spinapi[i][2])
                    #else:
                        #pb_inst(ON | "0x%X" % to_spinapi[i, 0], CONTINUE, 0, "0x%X" % to_spinapi[i][2])
                    if i == 0:
                        pass
                        #print('ON | ' + "0x%X" % to_spinapi[i][0] + ', CONTINUE, 0, ' + "0x%X" % to_spinapi[i][2] )
                    else:
                        pass
                        #print('ON | ' + "0x%X" % to_spinapi[i][0] + ', CONTINUE, 0, ' + "0x%X" % to_spinapi[i][2] )

                    i += 1

                # last instruction for delay
                #pb_inst(ON | "0x%X" % to_spinapi[i, 0], BRANCH, 0, "0x%X" % to_spinapi[i][2])
                #print('ON | ' + "0x%X" % to_spinapi[i][0] + ', BRANCH, start, ' + "0x%X" % to_spinapi[i][2] )

                #pb_stop_programming()
                #pb_reset()
                #pb_start()
                
                # should be checked
                #pb_close()
                self.reset_count = 1
                self.shift_count = 0
                self.increment_count == 0
            else:
                pass

        elif test_flag == 'test':
            # get repetition rate
            rep_rate = self.rep_rate[0]
            if rep_rate[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate[:-3])/2)
            elif rep_rate[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate[:-4])/2)
            elif rep_rate[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate[:-4])/2)

            if self.reset_count == 0 or self.shift_count == 1 or self.increment_count == 1:
                # using a special functions for convertion to instructions
                to_spinapi = self.instruction_pulse( self.bit_pulse( self.convertion_to_numpy( self.pulse_array ) ), rep_time )
                
                self.reset_count = 1
                self.shift_count = 0
                self.increment_count == 0
            else:
                pass

    def pulser_repetitoin_rate(self, *r_rate):
        """
        A function to get or set repetition rate.
        Repetition rate specifies the delay of the last
        SpinAPI instructions
        """
        if test_flag != 'test':
            if  len(r_rate) == 1:
                self.rep_rate = r_rate
            elif len(r_rate) == 0:
                general.message(self.rep_rate[0])
        elif test_flag == 'test':
            if  len(r_rate) == 1:
                self.rep_rate = r_rate
            elif len(r_rate) == 0:
                pass

    def pulser_shift(self):
        """
        A function to shift the start of the pulses.
        The function directly affects the pulse_array.
        """
        if test_flag != 'test':
            i = 0
            while i < len( self.pulse_array ):
                if int( self.pulse_array[i]['delta_start'][:-3] ) == 0:
                    pass
                else:
                    self.pulse_array[i]['start'] = str( int(self.pulse_array[i]['start'][:-3]) + \
                        int(self.pulse_array[i]['delta_start'][:-3])) + ' ' + \
                        self.pulse_array[i]['delta_start'][-2:]

                i += 1

            self.shift_count = 1

        elif test_flag == 'test':
            i = 0
            while i < len( self.pulse_array ):
                if int( self.pulse_array[i]['delta_start'][:-3] ) == 0:
                    pass
                else:
                    self.pulse_array[i]['start'] = str( int(self.pulse_array[i]['start'][:-3]) + \
                        int(self.pulse_array[i]['delta_start'][:-3])) + ' ' + \
                        self.pulse_array[i]['delta_start'][-2:]

                i += 1

            self.shift_count = 1

    def pulser_increment(self):
        """
        A function to increment the length of the pulses.
        The function directly affects the pulse_array.
        """
        if test_flag != 'test':
            i = 0
            while i < len( self.pulse_array ):
                if int(self.pulse_array[i]['length_increment'][:-3]) == 0:
                    pass
                else:
                    self.pulse_array[i]['length'] = str( int(self.pulse_array[i]['length'][:-3]) + \
                        int(self.pulse_array[i]['length_increment'][:-3])) + ' ' + \
                        self.pulse_array[i]['length_increment'][-2:]

                i += 1

            self.increment_count = 1

        elif test_flag == 'test':
            i = 0
            while i < len( self.pulse_array ):
                if int(self.pulse_array[i]['length_increment'][:-3]) == 0:
                    pass
                else:
                    self.pulse_array[i]['length'] = str( int(self.pulse_array[i]['length'][:-3]) + \
                        int(self.pulse_array[i]['length_increment'][:-3])) + ' ' + \
                        self.pulse_array[i]['length_increment'][-2:]

                i += 1

            self.increment_count = 1

    def pulser_reset(self, rep_rate = repetition_rate):
        """
        Reset all pulses to the initial state it was in at the start of the experiment.
        It includes the complete functionality of pulser_pulse_reset(), but also immediately
        updates the pulser as it is done by calling pulser_update().
        """
        if test_flag != 'test':
            # get repetition rate
            rep_rate = self.rep_rate[0]
            if rep_rate[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate[:-3])/2)
            elif rep_rate[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate[:-4])/2)
            elif rep_rate[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate[:-4])/2)

            # reset the pulses; deepcopy helps to create a TRULY NEW array
            self.pulse_array = deepcopy( self.pulse_array_init )
            # using a special functions for convertion to instructions
            to_spinapi = self.instruction_pulse( self.bit_pulse( self.convertion_to_numpy( self.pulse_array ) ), rep_time )
            general.message(to_spinapi)
            #pb_start_programming(PULSE_PROGRAM)
            i = 0
            while i < len( to_spinapi) - 1:
                #if i == 0: 
                    # to create a link for BRANCH
                    #start = pb_inst(ON | "0x%X" % to_spinapi[i, 0], CONTINUE, 0, "0x%X" % to_spinapi[i][2])
                #else:
                    #pb_inst(ON | "0x%X" % to_spinapi[i, 0], CONTINUE, 0, "0x%X" % to_spinapi[i][2])
                if i == 0:
                    pass
                    #print('ON | ' + "0x%X" % to_spinapi[i][0] + ', CONTINUE, 0, ' + "0x%X" % to_spinapi[i][2] )
                else:
                    pass
                    #print('ON | ' + "0x%X" % to_spinapi[i][0] + ', CONTINUE, 0, ' + "0x%X" % to_spinapi[i][2] )

                i += 1

            # last instruction for delay
            #pb_inst(ON | "0x%X" % to_spinapi[i, 0], BRANCH, 0, "0x%X" % to_spinapi[i][2])
            #print('ON | ' + "0x%X" % to_spinapi[i][0] + ', BRANCH, start, ' + "0x%X" % to_spinapi[i][2] )

            #pb_stop_programming()
            #pb_reset()
            #pb_start()
            
            # should be checked
            #pb_close()
            #return to_spinapi

            self.reset_count = 1
            self.increment_count = 0
            self.shift_count = 0

        elif test_flag == 'test':
            # get repetition rate
            rep_rate = self.rep_rate[0]
            if rep_rate[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate[:-3])/2)
            elif rep_rate[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate[:-4])/2)
            elif rep_rate[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate[:-4])/2)

            # reset the pulses; deepcopy helps to create a TRULY NEW array
            self.pulse_array = deepcopy( self.pulse_array_init )
            # using a special functions for convertion to instructions
            to_spinapi = self.instruction_pulse( self.bit_pulse( self.convertion_to_numpy( self.pulse_array ) ), rep_time )

            self.reset_count = 1
            self.increment_count = 0
            self.shift_count = 0

    def pulser_pulse_reset(self):
        """
        Reset all pulses to the initial state it was in at the start of the experiment.
        It does not update the pulser, if you want to reset all pulses and and also update 
        the pulser use the function pulser_reset() instead.
        """
        if test_flag != 'test':
            self.pulse_array = deepcopy(self.pulse_array_init)
            self.reset_count = 0
            self.increment_count = 0
            self.shift_count = 0

        elif test_flag == 'test':
            self.pulse_array = deepcopy(self.pulse_array_init)
            self.reset_count = 0
            self.increment_count = 0
            self.shift_count = 0

    def pulser_stop(self):
        """
        A function to stop pulse sequence
        """
        if test_flag != 'test':
            #pb_start_programming(PULSE_PROGRAM)
            #pb_inst(ON | "0x%X" % 0, CONTINUE, 0, "0x%X" % 12)
            #general.message('ON | ', "0x%X" % 0, ', CONTINUE, 0, ', "0x%X" % 12)
            #pb_inst(ON | "0x%X" % 0, STOP, 0, "0x%X" % 12)
            general.message('ON | ', "0x%X" % 0, ', STOP, 0, ', "0x%X" % 12)
            #pass
            #pb_stop_programming()
            #pb_reset()
            #pb_start()
            
            # should be checked
            #pb_close()
            #return to_spinapi

        elif test_flag == 'test':
            pass


    # Auxilary functions
    def convertion_to_numpy(self, p_array):
        """
        Convertion the pulse_array into numpy array in the form of
        [channel_number, start, end, delta_start, length_increment]
        channel_number is an integer: 2**(ch), where ch from channel_dict
        start is a pulse start in a pulser clock sample rate
        end is a pulse end in a pulser clock sample rate
        delta_start is a pulse delta_start in a pulser clock sample rate
        length_increment is a pulse length_increment in a pulser clock sample rate
        """
        if test_flag != 'test':
            i = 0
            pulse_temp_array = []
            num_pulses = len( p_array )
            while i < num_pulses:
                # get channel number
                ch = p_array[i]['channel']
                if ch in channel_dict:
                    ch_num = channel_dict[ch]
                # get start
                st = p_array[i]['start']
                if st[-2:] == 'ns':
                    st_time = int(float(st[:-3])/timebase)
                elif st[-2:] == 'us':
                    st_time = int(float(st[:-3])*1000/timebase)
                elif st[-2:] == 'ms':
                    st_time = int(float(st[:-3])*1000000/timebase)
                elif st[-2:] == 's':
                    st_time = int(float(st[:-3])*1000000000/timebase)
                # get length
                leng = p_array[i]['length']
                if leng[-2:] == 'ns':
                    leng_time = int(float(leng[:-3])/timebase)
                elif leng[-2:] == 'us':
                    leng_time = int(float(leng[:-3])*1000/timebase)
                elif leng[-2:] == 'ms':
                    leng_time = int(float(leng[:-3])*1000000/timebase)
                elif leng[-2:] == 's':
                    leng_time = int(float(leng[:-3])*1000000000/timebase)

                # get delta start
                del_st = p_array[i]['delta_start']
                if del_st[-2:] == 'ns':
                    delta_start = int(float(del_st[:-3])/timebase)
                elif del_st[-2:] == 'us':
                    delta_start = int(float(del_st[:-3])*1000/timebase)
                elif del_st[-2:] == 'ms':
                    delta_start = int(float(del_st[:-3])*1000000/timebase)
                elif del_st[-2:] == 's':
                    delta_start = int(float(del_st[:-3])*1000000000/timebase)

                # creating converted array
                # in terms of bits the number of channel is 2**(ch_num - 1)
                pulse_temp_array.append( (2**(ch_num), st_time, st_time + leng_time, delta_start) )

                i += 1

            return np.asarray(pulse_temp_array, dtype = np.int32)

        elif test_flag == 'test':
            i = 0
            pulse_temp_array = []
            num_pulses = len( p_array )
            while i < num_pulses:
                # get channel number
                ch = p_array[i]['channel']
                if ch in channel_dict:
                    ch_num = channel_dict[ch]
                # get start
                st = p_array[i]['start']
                if st[-2:] == 'ns':
                    st_time = int(float(st[:-3])/timebase)
                elif st[-2:] == 'us':
                    st_time = int(float(st[:-3])*1000/timebase)
                elif st[-2:] == 'ms':
                    st_time = int(float(st[:-3])*1000000/timebase)
                elif st[-2:] == 's':
                    st_time = int(float(st[:-3])*1000000000/timebase)
                # get length
                leng = p_array[i]['length']
                if leng[-2:] == 'ns':
                    leng_time = int(float(leng[:-3])/timebase)
                elif leng[-2:] == 'us':
                    leng_time = int(float(leng[:-3])*1000/timebase)
                elif leng[-2:] == 'ms':
                    leng_time = int(float(leng[:-3])*1000000/timebase)
                elif leng[-2:] == 's':
                    leng_time = int(float(leng[:-3])*1000000000/timebase)

                # get delta start
                del_st = p_array[i]['delta_start']
                if del_st[-2:] == 'ns':
                    delta_start = int(float(del_st[:-3])/timebase)
                elif del_st[-2:] == 'us':
                    delta_start = int(float(del_st[:-3])*1000/timebase)
                elif del_st[-2:] == 'ms':
                    delta_start = int(float(del_st[:-3])*1000000/timebase)
                elif del_st[-2:] == 's':
                    delta_start = int(float(del_st[:-3])*1000000000/timebase)

                # creating converted array
                # in terms of bits the number of channel is 2**(ch_num - 1)
                pulse_temp_array.append( (2**(ch_num), st_time, st_time + leng_time, delta_start) )

                i += 1

            return np.asarray(pulse_temp_array, dtype = np.int32)           

    def bit_pulse(self, p_array):
        """
        A function to calculate in which time interval
        two or more different channels are on.
        All the pulses converted in an bit_array of 0 and 1, where
        1 corresponds to the time interval when the channel is on.
        The size of the bit_array is determined by the total length
        of the full pulse sequence.
        Finally, a bit_array is multiplied by a 2**ch in order to
        calculate CH instructions for SpinAPI. 
        """
        if test_flag != 'test':
            max_pulse = np.amax(p_array[:,2])
            bit_array = np.zeros(max_pulse, dtype = int)
            i = 0

            while i < len(p_array):
                ch = p_array[i, 0]
                # convert each pulse in an array of 0 and 1,
                # 1 corresponds to the time interval, where the channel is on
                translation_array_temp = np.concatenate( (np.zeros(p_array[i, 1], dtype = int), \
                        np.ones(p_array[i, 2] - p_array[i, 1], dtype = int)), axis = None)
                translation_array = ch*np.concatenate( (translation_array_temp,  np.zeros(max_pulse\
                     - p_array[i, 2], dtype = int)), axis = None)

                # summing arrays for each pulse into the finalbit_array
                bit_array = bit_array + translation_array

                i += 1

            return bit_array

        elif test_flag == 'test':
            max_pulse = np.amax(p_array[:,2])
            bit_array = np.zeros(max_pulse, dtype = int)
            # for checking of overlapping pulses
            bit_array_pulses = []
            ch_array = []
            i = 0

            while i < len(p_array):
                ch = p_array[i, 0]
                ch_array.append(ch)
                # convert each pulse in an array of 0 and 1,
                # 1 corresponds to the time interval, where the channel is on
                translation_array_temp = np.concatenate( (np.zeros(p_array[i, 1], dtype = int), \
                        np.ones(p_array[i, 2] - p_array[i, 1], dtype = int)), axis = None)
                translation_array = ch*np.concatenate( (translation_array_temp,  np.zeros(max_pulse\
                     - p_array[i, 2], dtype = int)), axis = None)

                # summing arrays for each pulse into the finalbit_array
                bit_array = bit_array + translation_array
                # 
                bit_array_pulses.append(translation_array)

                # checking of overlapping pulses
                # works also for shift and increment
                j = 0
                while j < len(bit_array_pulses) - 1: # -1 for not checking the current pulse
                    if ch_array[j] == ch:
                        # the idea is to compare the sum of two pulses with the same channel value
                        # and check if there is an element in the sumthat is higher
                        # than channel value.
                        assert(np.any(( (translation_array + bit_array_pulses[j]) > (ch) )) == False), \
                            'Overlapping pulses on channel: ' + 'CH' + str(ch - 1)
                    else:
                        pass

                    j += 1

                i += 1

            return bit_array

    def instruction_pulse(self, bit_array, rep_time):
        """
        A function to convert the bit_array into a sequence
        of pulses that can be used as instructions for SpinAPI.
        The final array is in the form of
        [channel_number, start, end]
        channel_number is an integer: 2**(ch), where ch from channel_dict
        start is a pulse start in a pulser clock sample rate
        end is a pulse end in a pulser clock sample rate

        Pulses are not overlap
        """
        if test_flag != 'test':
            i = 0
            # for calculating the length and start of a pulse
            prev_len = 0
            prev_start = 1
            final_array = []
            while i < len( bit_array ) - 1:
                # check if we are inside the pulse
                # that means a current value in the bit_array is the same
                # as the previous one
                if bit_array[i + 1] == bit_array[i]:
                    if  i != len( bit_array ) - 2:
                        pass
                    # the last pulse should be took into account separately
                    # since the current value in the bit_array remains constant 
                    # until the end of the while loop
                    else:
                        ch = bit_array[i]
                        start = prev_start
                        # the +1/ +2 are added empirically
                        prev_start = i + 1
                        length = i + 2 - prev_len
                        prev_len = i + 1
                        # dismiss the zero length pulses
                        if length != 0:
                            final_array.append( [ch, start, length] )
                        else:
                            pass
                # if the value in the bit_array is changed
                # a new pulse should be added in the final_array
                else:
                    ch = bit_array[i]
                    start = prev_start
                    # the +1/ +1 are added empirically
                    prev_start = i + 1
                    length = i + 1 - prev_len
                    prev_len = i + 1
                    # dismiss the zero length pulses
                    if length != 0:
                        final_array.append( [ch, start, length] )
                    else:
                        pass

                i += 1

            final_array.append( [0, final_array[-1][1] + final_array[-1][2], rep_time - final_array[-1][2]] )
            return final_array


        elif test_flag == 'test':
            i = 0
            # for calculating the length and start of a pulse
            prev_len = 0
            prev_start = 1
            final_array = []
            while i < len( bit_array ) - 1:
                # check if we are inside the pulse
                # that means a current value in the bit_array is the same
                # as the previous one
                if bit_array[i + 1] == bit_array[i]:
                    if  i != len( bit_array ) - 2:
                        pass
                    # the last pulse should be took into account separately
                    # since the current value in the bit_array remains constant 
                    # until the end of the while loop
                    else:
                        ch = bit_array[i]
                        start = prev_start
                        # the +1/ +2 are added empirically
                        prev_start = i + 1
                        length = i + 2 - prev_len
                        prev_len = i + 1
                        # dismiss the zero length pulses
                        if length != 0:
                            final_array.append( [ch, start, length] )
                        else:
                            pass
                # if the value in the bit_array is changed
                # a new pulse should be added in the final_array
                else:
                    ch = bit_array[i]
                    start = prev_start
                    # the +1/ +1 are added empirically
                    prev_start = i + 1
                    length = i + 1 - prev_len
                    prev_len = i + 1
                    # dismiss the zero length pulses
                    if length != 0:
                        final_array.append( [ch, start, length] )
                    else:
                        pass

                i += 1

            # append the last pulse for waiting that determine the repetition rate
            if rep_time - final_array[-1][2] > 6:
                final_array.append( [0, final_array[-1][1] + final_array[-1][2], rep_time - final_array[-1][2]] )
                return final_array
            else:
                assert(1 == 2), 'Pulse sequence is longer than one period of the repetition rate'

def main():
    pass

if __name__ == "__main__":
    main()