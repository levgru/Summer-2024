from lab_framework import Manager, analysis
from numpy import sin, cos, deg2rad, inf
import matplotlib.pyplot as plt
import numpy as np

if __name__ == '__main__':
    TRIAL = 0
    angle_A = -30
    angle_B = 180 + angle_A
    SAMP = (6,5)
    '''
    # initialize the manager
    m = Manager(config='../config.json')

    # configure the VV state
    m.make_state('VV')

    # make alice measure in V
    m.log('Sending AQWP to 0')
    m.A_QWP.goto(0)
    m.log('Sending AHWP to 45')
    m.A_HWP.goto(45)
    # put bob's wps to calibrated settings
    m.log('Sending BHWP to 0')
    m.B_HWP.goto(0)
    m.log('Sending BQWP to 0')
    m.B_QWP.goto(0)
    m.log('Sending BCHWP to 0')
    m.B_C_HWP.goto(0)

    # loopydoodledoo
    data_A = []
    data_B = []
    for _ in range(30):
        m.B_C_QWP.goto(angle_A)
        data_A.append(m.take_data(*SAMP, 'C4', note='A'))
        m.B_C_QWP.goto(angle_B)
        data_B.append(m.take_data(*SAMP, 'C4', note='B'))

    # save the output
    m.output_data(f'BCQWP_VBNG_{TRIAL}.csv')
    m.shutdown()

    '''
    df = Manager.load_data('BCQWP_VBNG_0.csv')
    
    data_A = []
    data_B = []
    for i in range(len(df)):
        if df['note'][i] == 'A':
            data_A.append(df['C4'][i])
        elif df['note'][i] == 'B':
            data_B.append(df['C4'][i])
    data_A, data_B = np.array(data_A), np.array(data_B)
    xvals = np.arange(len(data_A))

    analysis.plot_errorbar(xvals, data_A, color='red', label=f'{angle_A} deg')
    analysis.plot_errorbar(xvals, data_B, color='blue', label=f'{angle_B} deg')
    plt.ylabel(f'Count Rate')
    plt.xlabel('Turn Number')
    plt.legend()
    plt.title('Rotating Bob\'s Creation QWP Back and Forth')
    plt.savefig(f'BCQWP_VBNG_{TRIAL}.png', dpi=600)
    plt.show()
