import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Keysight_3000_Xseries as key
import atomize.device_modules.BH_15 as bh

### Experimental parameters
POINTS = 200
STEP = 4
FIELD = 3473
AVERAGES = 1000

cycle_data_x = np.zeros(POINTS)
cycle_data_y = np.zeros(POINTS)
data_x = np.zeros(POINTS)
data_y = np.zeros(POINTS)
x_axis = np.arange(0, POINTS*STEP, STEP)
###

pb = pb_pro.PB_ESR_500_Pro()
t3034 = key.Keysight_3000_Xseries()
bh15 = bh.BH_15()

bh15.magnet_setup(FIELD, 1)
bh15.magnet_field(FIELD)

t3034.oscilloscope_trigger_channel('CH1')
#tb = t3034.oscilloscope_time_resolution()
t3034.oscilloscope_record_length(250)
t3034.oscilloscope_acquisition_type('Average')
t3034.oscilloscope_number_of_averages(AVERAGES)
t3034.oscilloscope_stop()

#PROBE
pb.pulser_pulse(name = 'P0', channel = 'MW', start = '2100 ns', length = '16 ns', phase_list = ['+x', '-x'])
pb.pulser_pulse(name = 'P1', channel = 'MW', start = '2440 ns', length = '32 ns', delta_start = '8 ns', phase_list = ['+x', '+x'])
pb.pulser_pulse(name = 'P2', channel = 'MW', start = '3780 ns', length = '32 ns', delta_start = '16 ns', phase_list = ['+x', '+x'])
#PUMP
pb.pulser_pulse(name = 'P3', channel = 'AWG', start = '2680 ns', length = '20 ns', delta_start = '4 ns')
pb.pulser_pulse(name = 'P4', channel = 'TRIGGER_AWG', start = '526 ns', length = '20 ns', delta_start = '4 ns')
#DETECTION
pb.pulser_pulse(name = 'P5', channel = 'TRIGGER', start = '4780 ns', length = '100 ns', delta_start = '16 ns')

pb.pulser_repetitoin_rate('1000 Hz')

k = 1 
while k < 9:
    
    j = 0
    while j < k:
        pb.pulser_shift('P1', 'P2', 'P3', 'P4', 'P5')
        pb.pulser_shift('P3', 'P4')
        pb.pulser_shift('P3', 'P4')
        pb.pulser_shift('P3', 'P4')

        j += 1

    if k % 2 == 1:
        pb.pulser_next_phase()
    elif k % 2 == 0:
        pb.pulser_next_phase()
        pb.pulser_next_phase()

    i = 0
    while i < POINTS:

        pb.pulser_update()

        t3034.oscilloscope_start_acquisition()
        area_x = t3034.oscilloscope_area('CH4')
        area_y = t3034.oscilloscope_area('CH3')

        cycle_data_x[i] = area_x
        cycle_data_y[i] = area_y

        pb.pulser_shift('P3','P4')

        general.plot_1d('DEER_Cycle', x_axis, cycle_data_x, xname = 'Delay',\
            xscale = 'ns', yname = 'Area', yscale = 'V*s', label = 'X')
        general.plot_1d('DEER_Cycle', x_axis, cycle_data_y, xname = 'Delay',\
            xscale = 'ns', yname = 'Area', yscale = 'V*s', label = 'Y')

        i += 1

    data_x = (data_x*(k-1) + cycle_data_x)/k
    data_y = (data_y*(k-1) + cycle_data_y)/k

    general.plot_1d('DEER_All', x_axis, data_x, xname = 'Delay',\
        xscale = 'ns', yname = 'Area', yscale = 'V*s', label = 'X')
    general.plot_1d('DEER_All', x_axis, data_y, xname = 'Delay',\
        xscale = 'ns', yname = 'Area', yscale = 'V*s', label = 'Y')

    pb.pulser_reset()

    k += 1

pb.pulser_stop()

