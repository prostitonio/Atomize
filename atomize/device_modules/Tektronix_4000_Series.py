#!/usr/bin/env python3 # -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
import numpy as np 
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','Tektronix_4032_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)

# auxilary dictionaries
number_averag_list = [2, 4, 8, 16, 32, 64, 128, 256, 512]
points_list = [1000, 10000, 100000, 1000000, 10000000];
timebase_dict = {'s': 1, 'ms': 1000, 'us': 1000000, 'ns': 1000000000,};
timebase_helper_list = [1, 2, 4, 10, 20, 40, 100, 200, 400, 1000]
scale_dict = {'V': 1, 'mV': 1000,};
ac_type_dic = {'Norm': "SAMple", 'Ave': "AVErage", 'Hres': "HIRes",'Peak': "PEAKdetect"}

# Ranges and limits
sensitivity_min = 0.001
sensitivity_max = 5

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_start = 1
test_stop = 1000
test_record_length = 2000
test_impedance = 1000000
test_acquisition_type = 'Norm'
test_num_aver = 2
test_timebase = '100 ms'
test_delay = 0
test_coupling = 'AC'
test_tr_mode = 'Normal'
test_tr_channel = 'CH1'
test_trigger_level = 0.

class Tektronix_4000_Series:
    #### Basic interaction functions
    def __init__(self):
        if test_flag != 'test':
            if config['interface'] == 'ethernet':
                rm = pyvisa.ResourceManager()
                try:
                    self.status_flag = 1
                    self.device = rm.open_resource(config['ethernet_address'])
                    self.device.timeout = config['timeout']; # in ms
                    self.device.read_termination = config['read_termination']
                    try:
                        # test should be here
                        self.device_write('*CLS')
                        answer = int(self.device_query('*TST?'))
                        if answer == 0:
                            self.status_flag = 1
                        else:
                            general.message('During internal device test errors are found')
                            self.status_flag = 0
                            sys.exit()
                    except pyvisa.VisaIOError:
                        general.message("No connection")
                        self.status_flag = 0
                        sys.exit()
                    except BrokenPipeError:
                        general.message("No connection")
                        self.status_flag = 0
                        sys.exit()
                except pyvisa.VisaIOError:
                    general.message("No connection")
                    self.status_flag = 0
                    sys.exit()
                except BrokenPipeError:
                    general.message("No connection")
                    self.status_flag = 0;
                    sys.exit()

        elif test_flag == 'test':
            pass

    def close_connection(self):
        if test_flag != 'test':
            self.status_flag = 0;
            gc.collect()
        elif test_flag == 'test':
            pass

    def device_write(self, command):
        if self.status_flag == 1:
            command = str(command)
            self.device.write(command)
        else:
            general.message("No connection")
            self.status_flag = 0
            sys.exit()

    def device_query(self, command):
        if self.status_flag == 1:
            answer = self.device.query(command)
            return answer
        else:
            general.message("No connection")
            self.status_flag = 0
            sys.exit()

    def device_query_ascii(self, command):
        if self.status_flag == 1:
            answer = self.device.query_ascii_values(command, converter='f', separator=',', container=np.array)
            return answer
        else:
            general.message("No connection")
            self.status_flag = 0
            sys.exit()

    def device_read_binary(self, command):
        if self.status_flag == 1:
            answer = self.device.query_binary_values(command, 'b', is_big_endian=True, container=np.array)
            # RPBinary, value from 0 to 255. 'b'
            # Endianness is primarily expressed as big-endian (BE) or little-endian (LE).
            # A big-endian system stores the most significant byte of a word at the smallest memory address 
            # and the least significant byte at the largest. A little-endian system, in contrast, stores 
            # the least-significant byte at the smallest address.
            return answer
        else:
            general.message("No connection")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def oscilloscope_name(self):
        if test_flag != 'test':
            answer = self.device_query('*IDN?')
            return answer
        elif test_flag == 'test':
            answer = config['name']
            return answer

    def oscilloscope_define_window(self, **kargs):
        if test_flag != 'test':        
            try:
                st = int(kargs['start'])
                stop = int(kargs['stop'])
                points = self.oscilloscope_record_length()
                if stop > points or st > points:
                    general.message('Invalid arguments')
                    sys.exit()
                else:
                    self.device_write("DATa:STARt " + str(st))
                    self.device_write("DATa:STOP " + str(stop))
            except KeyError:
                answer1 = int(self.device_query('DATa:STARt?'))
                answer2 = int(self.device_query('DATa:STOP?'))
                return answer1, answer2

        elif test_flag == 'test':
            try:
                st = int(kargs['start'])
                stop = int(kargs['stop'])
                points = self.oscilloscope_record_length()
                assert(stop > points or st > points), 'Invalid window'
            except KeyError:
                answer1 = test_start
                answer2 = test_stop
                return answer1, answer2

    def oscilloscope_record_length(self, *points):
        if test_flag != 'test': 
            if len(points) == 1:
                temp = int(points[0])
                poi = min(points_list, key = lambda x: abs(x - temp))
                if int(poi) != temp:
                    general.message("Desired record length cannot be set, the nearest available value is used")
                self.device_write("HORizontal:RECOrdlength " + str(poi))
            elif len(points) == 0:
                answer = int(self.device_query('HORizontal:RECOrdlength?'))
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(points) == 1:
                temp = int(points[0])
                poi = min(points_list, key = lambda x: abs(x - temp))
            elif len(points) == 0:
                answer = test_record_length
                return answer
            else:
                assert (1 == 2), 'Invalid record length argument'       

    def oscilloscope_acquisition_type(self, *ac_type):
        if test_flag != 'test':        
            if len(ac_type) == 1:
                at = str(ac_type[0])
                if at in ac_type_dic:
                    flag = ac_type_dic[at]
                    self.device_write("ACQuire:MODe "+ str(flag))
                else:
                    general.message("Invalid acquisition type")
                    sys.exit()
            elif len(ac_type) == 0:
                answer = str(self.device_query("ACQuire:MODe?"))
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(ac_type) == 1:
                at = str(ac_type[0])
                if at in ac_type_dic:
                    flag = ac_type_dic[at]
                else:
                    assert(1 == 2), "Invalid acquisition type"
            elif len(ac_type) == 0:
                answer = test_acquisition_type
                return answer
            else:
                assert (1 == 2), 'Invalid acquisition type argument' 

    def oscilloscope_number_of_averages(self, *number_of_averages):
        if test_flag != 'test':
            if len(number_of_averages) == 1:
                temp = int(number_of_averages[0])
                numave = min(number_averag_list, key = lambda x: abs(x - temp))
                if int(numave) != temp:
                    general.message("Desired number of averages cannot be set, the nearest available value is used")
                ac = self.oscilloscope_acquisition_type()
                if ac == 'AVE':
                    self.device_write("ACQuire:NUMAVg " + str(numave))
                elif ac == 'SAM':
                    general.message("Your are in SAMple mode")
                elif ac == 'HIR':
                    general.message("Your are in HRES mode")
                elif ac == 'PEAK':
                    general.message("Your are in PEAK mode")
            elif len(number_of_averages) == 0:
                answer = int(self.device_query("ACQuire:NUMAVg?"))
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(number_of_averages) == 1:
                temp = int(number_of_averages[0])
                numave = min(number_averag_list, key = lambda x: abs(x - temp))
            elif len(number_of_averages) == 0:
                answer = test_num_aver
                return answer
            else:
                assert (1 == 2), 'Invalid number of averages argument' 

    def oscilloscope_timebase(self, *timebase):
        if test_flag != 'test':
            if  len(timebase) == 1:
                temp = timebase[0].split(' ')
                if temp[1] == 'ns' and float(temp[0]) >= 60 and float(temp[0]) <= 90:
                    if timebase != '80 ns':
                        self.device_write("HORizontal:SCAle " + str(80/1000000000))
                        general.message("Desired time constant cannot be set, the nearest available value is used")
                    else:
                        self.device_write("HORizontal:SCAle " + str(80/1000000000))              
                else:
                    number_tb = min(timebase_helper_list, key = lambda x: abs(x - int(temp[0])))
                    if number_tb > 40 and temp[1] == 's':
                        number_tb = 40
                    if number_tb == 1000 and temp[1] == 'ns':
                        number_tb = 1
                        temp[1] = 'us'
                    elif number_tb == 1000 and temp[1] == 'us':
                        number_tb = 1
                        temp[1] = 'ms'
                    elif number_tb == 1000 and temp[1] == 'ms':
                        number_tb = 1
                        temp[1] = 's'
                    if int(number_tb) != float(temp[0]):
                        general.message("Desired time constant cannot be set, the nearest available value is used")
                    if temp[1] in timebase_dict:
                        coef = timebase_dict[temp[1]]
                        self.device_write("HORizontal:SCAle "+ str(number_tb/coef))
                    else:
                        general.message("Incorrect timebase")
                        sys.exit()
            elif len(timebase) == 0:
                answer = float(self.device_query("HORizontal:SCAle?"))*1000000
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if  len(timebase) == 1:
                temp = timebase[0].split(' ')
                number_tb = min(timebase_helper_list, key = lambda x: abs(x - int(temp[0])))
                if number_tb > 40 and temp[1] == 's':
                        number_tb = 40
                if number_tb == 1000 and temp[1] == 'ns':
                    number_tb = 1
                    temp[1] = 'us'
                elif number_tb == 1000 and temp[1] == 'us':
                    number_tb = 1
                    temp[1] = 'ms'
                elif number_tb == 1000 and temp[1] == 'ms':
                    number_tb = 1
                    temp[1] = 's'
                if temp[1] in timebase_dict:
                    coef = timebase_dict[temp[1]]
                else:
                    assert (1 == 2), 'Invalid timebase argument'
            elif len(timebase) == 0:
                answer = test_timebase
                return answer
            else:
                assert (1 == 2), 'Invalid timebase argument'

    def oscilloscope_time_resolution(self):
        if test_flag != 'test':
            points = int(self.oscilloscope_record_length())
            answer = 1000000*float(self.device_query("HORizontal:SCAle?"))/points
            return answer
        elif test_flag == 'test':
            answer = 1000000*float(test_timebase.split(' ')[0])/test_record_length
            return answer

    def oscilloscope_start_acquisition(self):
        if test_flag != 'test':
            #start_time = time.time()
            self.device_query('*ESR?')
            self.device_write('ACQuire:STATE RUN;:ACQuire:STOPAfter SEQ')
            self.device_query('*OPC?') # return 1, if everything is ok;
            # the whole sequence is the following 1-clearing; 2-3-digitizing; 4-checking of the completness
            #end_time=time.time()
            general.message('Acquisition completed') 
            #general.message("Duration of Acquisition: {}".format(end_time - start_time))
        elif test_flag == 'test':
            pass

    def oscilloscope_preamble(self, channel):
        if test_flag != 'test':
            if channel == 'CH1':
                self.device_write('DATa:SOUrce CH1')
                preamble = self.device_query("WFMOutpre?")
            elif channel == 'CH2':
                self.device_write('DATa:SOUrce CH2')
                preamble = self.device_query("WFMOutpre?")
            elif channel == 'CH3':
                self.device_write('DATa:SOUrce CH3')
                preamble = self.device_query("WFMOutpre?")
            elif channel == 'CH4':
                self.device_write('DATa:SOUrce CH4')
                preamble = self.device_query("WFMOutpre?")
            else:
                general.message("Invalid channel is given")
                sys.exit()
            return preamble

        elif test_flag == 'test':
            assert(channel == 'CH1' or channel == 'CH2' or channel == 'CH3'\
             or channel == 'CH4'), 'Invalid channel is given'
            preamble = np.arange(21)
            return preamble

    def oscilloscope_stop(self):
        if test_flag != 'test':
            self.device_write("ACQuire:STATE STOP")
        elif test_flag == 'test':
            pass

    def oscilloscope_run(self):
        if test_flag != 'test':
            self.device_write("ACQuire:STATE RUN")
        elif test_flag == 'test':
            pass

    def oscilloscope_get_curve(self, channel):
        if test_flag != 'test':
            if channel == 'CH1':
                self.device_write('DATa:SOUrce CH1')
            elif channel == 'CH2':
                self.device_write('DATa:SOUrce CH2')
            elif channel == 'CH3':
                self.device_write('DATa:SOUrce CH3')
            elif channel == 'CH4':
                self.device_write('DATa:SOUrce CH4')
            else:
                general.message("Invalid channel is given")
                sys.exit()
                
            self.device_write('DATa:ENCdg RIBinary')

            array_y = self.device_read_binary('CURVe?')
            #x_orig=float(self.device_query("WFMOutpre:XZEro?"))
            #x_inc=float(self.device_query("WFMOutpre:XINcr?"))
            #general.message(preamble)
            y_ref = float(self.device_query("WFMOutpre:YOFf?"))
            y_inc = float(self.device_query("WFMOutpre:YMUlt?"))
            y_orig = float(self.device_query("WFMOutpre:YZEro?"))
            #general.message(y_inc)
            #general.message(y_orig)
            #general.message(y_ref)
            array_y = (array_y - y_ref)*y_inc + y_orig
            #array_x= list(map(lambda x: x_inc*(x+1) + x_orig, list(range(len(array_y)))))
            #final_data = np.asarray(list(zip(array_x,array_y)))
            return array_y

        elif test_flag == 'test':
            assert(channel == 'CH1' or channel == 'CH2' or channel == 'CH3'\
             or channel == 'CH4'), 'Invalid channel is given'
            array_y = np.arange(test_stop - test_start + 1)
            return array_y

    def oscilloscope_sensitivity(self, *channel):
        if test_flag != 'test':
            if len(channel) == 2:
                temp = channel[1].split(" ")
                ch = str(channel[0])
                val = float(temp[0])
                scaling = str(temp[1])
                if scaling in scale_dict:
                    coef = scale_dict[scaling]
                    if val/coef >= sensitivity_min and val/coef <= sensitivity_max:
                        if ch == 'CH1':
                            self.device_write("CH1:SCAle " + str(val/coef))
                        elif ch == 'CH2':
                            self.device_write("CH2:SCAle " + str(val/coef))
                        elif ch == 'CH3':
                            self.device_write("CH3:SCAle " + str(val/coef))
                        elif ch == 'CH4':
                            self.device_write("CH4:SCAle " + str(val/coef))
                        else:
                            general.message("Incorrect channel is given")
                            sys.exit()
                    else:
                        general.message("Incorrect sensitivity range")
                        sys.exit()                    
                else:
                    general.message("Incorrect scaling factor")
                    sys.exit()
            elif len(channel) == 1:
                ch = str(channel[0])
                if ch == 'CH1':
                    answer = float(self.device_query("CH1:SCAle?"))*1000
                    return answer
                elif ch == 'CH2':
                    answer = float(self.device_query("CH2:SCAle?"))*1000
                    return answer
                elif ch == 'CH3':
                    answer = float(self.device_query("CH3:SCAle?"))*1000
                    return answer
                elif ch == 'CH4':
                    answer = float(self.device_query("CH4:SCAle?"))*1000
                    return answer
                else:
                    general.message("Incorrect channel is given")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(channel) == 2:
                temp = channel[1].split(" ")
                ch = str(channel[0])
                val = float(temp[0])
                scaling = str(temp[1])
                if scaling in scale_dict:
                    coef = scale_dict[scaling]
                    assert(val/coef >= sensitivity_min and val/coef <= \
                        sensitivity_max), "Incorrect sensitivity range"                    
                    assert(ch == 'CH1' or ch == 'CH2' or ch == 'CH3'\
                     or ch == 'CH4'), 'Invalid channel is given'
                else:
                    assert(1 == 2), "Incorrect sensitivity argument"
            elif len(channel) == 1:
                ch = str(channel[0])
                assert(ch == 'CH1' or ch == 'CH2' or ch == 'CH3'\
                     or ch == 'CH4'), 'Invalid channel is given'
            else:
                assert(1 == 2), "Incorrect sensitivity argument"

    def oscilloscope_offset(self, *channel):
        if test_flag != 'test':
            if len(channel) == 2:
                temp = channel[1].split(" ")
                ch = str(channel[0])
                val = float(temp[0])
                scaling = str(temp[1]);
                if scaling in scale_dict:
                    coef = scale_dict[scaling]
                    if ch == 'CH1':
                        self.device_write("CH1:OFFSet " + str(val/coef))
                    elif ch == 'CH2':
                        self.device_write("CH2:OFFSet " + str(val/coef))
                    elif ch == 'CH3':
                        self.device_write("CH3:OFFSet " + str(val/coef))
                    elif ch == 'CH4':
                        self.device_write("CH4:OFFSet " + str(val/coef))
                    else:
                        general.message("Incorrect channel is given")
                        sys.exit()
                else:
                    general.message("Incorrect scaling factor")
                    sys.exit()
            elif len(channel) == 1:
                ch = str(channel[0])
                if ch == 'CH1':
                    answer = float(self.device_query("CH1:OFFSet?"))*1000
                    return answer
                elif ch == 'CH2':
                    answer = float(self.device_query("CH2:OFFSet?"))*1000
                    return answer
                elif ch == 'CH3':
                    answer = float(self.device_query("CH3:OFFSet?"))*1000
                    return answer
                elif ch == 'CH4':
                    answer = float(self.device_query("CH4:OFFSet?"))*1000
                    return answer
                else:
                    general.message("Incorrect channel is given")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(channel) == 2:
                temp = channel[1].split(" ")
                ch = str(channel[0])
                val = float(temp[0])
                scaling = str(temp[1])
                if scaling in scale_dict:
                    coef = scale_dict[scaling]
                    assert(ch == 'CH1' or ch == 'CH2' or ch == 'CH3'\
                     or ch == 'CH4'), 'Invalid channel is given'
                else:
                    assert(1 == 2), "Incorrect offset argument"
            elif len(channel) == 1:
                ch = str(channel[0])
                assert(ch == 'CH1' or ch == 'CH2' or ch == 'CH3'\
                     or ch == 'CH4'), 'Invalid channel is given'
            else:
                assert(1 == 2), "Incorrect offset argument"

    def oscilloscope_trigger_delay(self, *delay):
        if test_flag != 'test':
            if len(delay) == 1:
                temp = delay[0].split(" ")
                offset = float(temp[0])
                scaling = temp[1]
                if scaling in timebase_dict:
                    coef = timebase_dict[scaling]
                    self.device_write("HORizontal:DELay:TIMe " + str(offset/coef))
                else:
                    general.message("Incorrect trigger delay")
                    sys.exit()
            elif len(delay) == 0:
                answer = float(self.device_query("HORizontal:DELay:TIMe?"))*1000000
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(delay) == 1:
                temp = delay[0].split(" ")
                offset = float(temp[0])
                scaling = temp[1]
                if scaling in timebase_dict:
                    coef = timebase_dict[scaling]
                else:
                    assert(1 == 2), 'Incorrect trigger delay'
            elif len(delay) == 0:
                answer = test_delay
                return answer
            else:
                assert(1 == 2), 'Incorrect trigger delay argument'

    def oscilloscope_coupling(self, *coupling):
        if test_flag != 'test':
            if len(coupling) == 2:
                ch = str(coupling[0])
                cpl = str(coupling[1])
                if ch == 'CH1':
                    self.device_write("CH1:COUPling " + str(cpl))
                elif ch == 'CH2':
                    self.device_write("CH2:COUPling " + str(cpl))
                elif ch == 'CH3':
                    self.device_write("CH3:COUPling " + str(cpl))
                elif ch == 'CH4':
                    self.device_write("CH4:COUPling " + str(cpl))
                else:
                    general.message("Incorrect channel is given")
                    sys.exit()
            elif len(coupling) == 1:
                ch = str(coupling[0])
                if ch == 'CH1':
                    answer = self.device_query("CH1:COUPling?")
                    return answer
                elif ch == 'CH2':
                    answer = self.device_query("CH2:COUPling?")
                    return answer
                elif ch == 'CH3':
                    answer = self.device_query("CH3:COUPling?")
                    return answer
                elif ch == 'CH4':
                    answer = self.device_query("CH4:COUPling?")
                    return answer
                else:
                    general.message("Incorrect channel is given")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(coupling) == 2:
                ch = str(coupling[0])
                cpl = str(coupling[1])
                assert(ch == 'CH1' or ch == 'CH2' or ch == 'CH3'\
                     or ch == 'CH4'), 'Invalid channel is given'
                assert(cpl == 'AC' or cpl == 'DC'), 'Invalid coupling is given'
            elif len(coupling) == 1:
                ch = str(coupling[0])
                assert(ch == 'CH1' or ch == 'CH2' or ch == 'CH3'\
                     or ch == 'CH4'), 'Invalid channel is given'
                answer = test_coupling
                return answer
            else:
                asser(1 == 2), 'Invalid coupling argument'

    def oscilloscope_impedance(self, *impedance):
        if test_flag != 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                cpl = str(impedance[1])
                if cpl == '1 M':
                    cpl = 'MEG'
                elif cpl == '50':
                    cpl = 'FIFty'
                if ch == 'CH1':
                    self.device_write("CH1:TERmination " + str(cpl))
                elif ch == 'CH2':
                    self.device_write("CH2:TERmination " + str(cpl))
                elif ch == 'CH3':
                    self.device_write("CH3:TERmination " + str(cpl))
                elif ch == 'CH4':
                    self.device_write("CH4:TERmination " + str(cpl))
                else:
                    general.message("Incorrect channel is given")
                    sys.exit()
            elif len(impedance) == 1:
                ch = str(impedance[0])
                if ch == 'CH1':
                    answer = self.device_query("CH1:TERmination?")
                    return answer
                elif ch == 'CH2':
                    answer = self.device_query("CH2:TERmination?")
                    return answer
                elif ch == 'CH3':
                    answer = self.device_query("CH3:TERmination?")
                    return answer
                elif ch == 'CH4':
                    answer = self.device_query("CH4:TERmination?")
                    return answer
                else:
                    general.message("Incorrect channel is given")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                cpl = str(impedance[1])
                assert(ch == 'CH1' or ch == 'CH2' or ch == 'CH3'\
                     or ch == 'CH4'), 'Invalid channel is given'
                assert(cpl == '1 M' or cpl == '50'), 'Invalid impedance is given'
            elif len(impedance) == 1:
                ch = str(impedance[0])
                assert(ch == 'CH1' or ch == 'CH2' or ch == 'CH3'\
                     or ch == 'CH4'), 'Invalid channel is given'
                answer = test_impedance
                return answer
            else:
                assert(1 == 2), 'Invalid impedance argument'

    def oscilloscope_trigger_mode(self, *mode):
        if test_flag != 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md == 'Auto':
                    self.device_write("TRIGger:A:MODe " + 'AUTO')
                elif md == 'Normal':
                    self.device_write("TRIGger:A:MODe " + 'NORMal')
                else:
                    general.message("Incorrect trigger mode is given")
                    sys.exit()
            elif len(mode) == 0:
                answer = self.device_query("TRIGger:A:MODe?")
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(mode) == 1:
                md = str(mode[0])
                assert(md == 'Auto' or md == 'Normal'), 'Incorrect trigger mode is given'
            elif len(mode) == 0:
                answer = test_tr_mode
                return answer
            else:
                assert(1 == 2), 'Incorrect trigger mode argument'

    def oscilloscope_trigger_channel(self, *channel):
        if test_flag != 'test':    
            if len(channel) == 1:
                ch = str(channel[0])
                if ch == 'CH1':
                    self.device_write("TRIGger:A:EDGE:SOUrce " + 'CH1')
                elif ch == 'CH2':
                    self.device_write("TRIGger:A:EDGE:SOUrce " + 'CH2')
                elif ch == 'CH3':
                    self.device_write("TRIGger:A:EDGE:SOUrce " + 'CH3')
                elif ch == 'CH4':
                    self.device_write("TRIGger:A:EDGE:SOUrce " + 'CH4')
                elif ch == 'Line':
                    self.device_write("TRIGger:A:EDGE:SOUrce " + 'LINE')
                else:
                    general.message("Incorrect trigger channel is given")
                    sys.exit()
            elif len(channel) == 0:
                answer = self.device_query("TRIGger:A:EDGE:SOUrce?")
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()
        if test_flag == 'test':        
            if len(channel) == 1:
                ch = str(channel[0])
                assert(ch == 'CH1' or ch == 'CH2' or ch == 'CH3'\
                     or ch == 'CH4' or ch == 'Line'), 'Invalid trigger channel is given'
            elif len(channel) == 0:
                answer = test_tr_channel
                return answer
            else:
                assert(1 == 2), "Invalid trigger channel argument"

    def oscilloscope_trigger_low_level(self, *level):
        if test_flag != 'test':
            if len(level) == 2:
                ch = str(level[0])
                lvl = level[1]
                if lvl != 'ECL' and lvl != 'TTL':
                    lvl = float(level[1])
                if ch == 'CH1':
                    self.device_write("TRIGger:A:LEVel:CH1"+str(lvl))
                elif ch == 'CH2':
                    self.device_write("TRIGger:A:LEVel:CH2 "+str(lvl))
                elif ch == 'CH3':
                    self.device_write("TRIGger:A:LEVel:CH3 "+str(lvl))
                elif ch == 'CH4':
                    self.device_write("TRIGger:A:LEVel:CH4 "+str(lvl))
                else:
                    general.message("Incorrect trigger channel is given")
                    sys.exit()
            elif len(level) == 1:
                ch = str(level[0])
                if ch == 'CH1':
                    answer = float(self.device_query("TRIGger:A:LEVel:CH1?"))
                    return answer
                elif ch == 'CH2':
                    answer = float(self.device_query("TRIGger:A:LEVel:CH2?"))
                    return answer
                elif ch == 'CH3':
                    answer = float(self.device_query("TRIGger:A:LEVel:CH3?"))
                    return answer
                elif ch == 'CH4':
                    answer = float(self.device_query("TRIGger:A:LEVel:CH4?"))
                    return answer
                else:
                    general.message("Incorrect channel is given")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()
        elif test_flag == 'test':
            if len(level) == 2:
                ch = str(level[0])
                lvl = level[1]
                if lvl != 'ECL' and lvl != 'TTL':
                    lvl = float(level[1])
                assert(ch == 'CH1' or ch == 'CH2' or ch == 'CH3'\
                     or ch == 'CH4'), 'Invalid trigger channel is given'
            elif len(level) == 1:
                ch = str(level[0])
                assert(ch == 'CH1' or ch == 'CH2' or ch == 'CH3'\
                     or ch == 'CH4'), 'Invalid trigger channel is given'
                answer = test_trigger_level
                return answer
            else:
                assert(1 == 2), "Invalid trigger level argument"

    def oscilloscope_command(self, command):
        if test_flag != 'test':
            self.device_write(command)
        elif test_flag == 'test':
            pass

    def oscilloscope_query(self, command):
        if test_flag != 'test':
            answer = self.device_query(command)
            return answer
        elif test_flag == 'test':
            answer = None
            return answer

def main():
    pass

if __name__ == "__main__":
    main()

