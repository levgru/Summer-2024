# file to read and process experimentally collected density matrices
import numpy as np
from os.path import join, dirname, abspath
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from sample_rho import *
from rho_methods import *

# set path
current_path = dirname(abspath(__file__))
DATA_PATH = join(current_path, '../../framework/decomp_test/')

def get_rho_from_file_depricated(filename, rho_actual):
    '''Function to read in experimental density matrix from file. Depricated since newer experiments will save the target density matrix in the file; for trials <= 14'''
    # read in data
    try:
        rho, unc, Su = np.load(join(DATA_PATH,filename), allow_pickle=True)
    except:
        rho, unc = np.load(join(DATA_PATH,filename), allow_pickle=True)

    # print results
    print('measublue rho\n---')
    print(rho)
    print('uncertainty \n---')
    print(unc)
    print('actual rho\n ---')
    print(rho_actual)
    print('fidelity', get_fidelity(rho, rho_actual))
    print('purity', get_purity(rho))

    print('trace of measublue rho', np.trace(rho))
    print('eigenvalues of measublue rho', np.linalg.eigvals(rho))

def get_rho_from_file(filename, verbose=True, angles=None):
    '''Function to read in experimental density matrix from file. For trials > 14. N.b. up to trial 23, angles were not saved (but recorded in lab_notebook markdown file). Also note that in trials 20 (E0 eta = 45), 21 (blueo of E0 (eta = 45, chi = 0, 18)), 22 (E0 eta = 60), and 23 (E0 eta = 60, chi = -90), there was a sign error in the phi phase in the Jones matrices, so will recalculate the correct density matrix; ** the one saved in the file as the theoretical density matrix is incorrect **
    --
    Parameters
        filename : str, Name of file to read in
        verbose : bool, Whether to print out results
        angles: list, List of angles used in the experiment. If not None, will assume angles provided in the data file.
    '''

    def split_filename():
            ''' Splits up the file name and identifies the trial number, eta, and chi values'''

            # split filename
            split_filename = filename.split('_')
            # get trial number
            trial = int(split_filename[-1].split('.')[0])
            # get eta
            eta = float(split_filename[1].split(',')[1].split('(')[1])
            chi = float(split_filename[1].split(',')[2].split(')')[0].split(' ')[1])

            return trial, eta, chi

    # read in data
    try:

        rho, unc, Su, rho_actual, angles, fidelity, purity = np.load(join(DATA_PATH,filename), allow_pickle=True)

        ## update df with info about this trial ##
        if "E0" in filename: # if E0, split up into eta and chi
            trial, eta, chi = split_filename()

        # print results
        if verbose:
            print('angles\n---')
            print(angles)
            print('measured rho\n---')
            print(rho)
            print('uncertainty \n---')
            print(unc)
            print('actual rho\n ---')
            print(rho_actual)
            print('fidelity', fidelity)
            print('purity', purity)

            print('trace of measublue rho', np.trace(rho))
            print('eigenvalues of measublue rho', np.linalg.eigvals(rho))

        return trial, rho, unc, Su, rho_actual, fidelity, purity, eta, chi, angles

    except:
        rho, unc, Su, rho_actual, _, purity = np.load(join(DATA_PATH,filename), allow_pickle=True)

        ## since angles were not saved, this means we also have the phi sign error as described in the comment to the function, so will need to recalculate the target. ##

        def split_filename():
            ''' Splits up the file name and identifies the trial number, eta, and chi values'''

            # split filename
            split_filename = filename.split('_')
            # get trial number
            trial = int(split_filename[-1].split('.')[0])
            # get eta
            eta = float(split_filename[1].split(',')[1].split('(')[1])
            chi = float(split_filename[1].split(',')[2].split(')')[0].split(' ')[1])

            return trial, eta, chi

        if "E0" in filename: # if E0, split up into eta and chi
            trial, eta, chi = split_filename()

            chi*=-1 # have to switch sign of chi

            # calculate target rho
            targ_rho = get_E0(np.deg2rad(eta), np.deg2rad(chi))
            fidelity = get_fidelity(rho, targ_rho)

            # print results
            if verbose:
                print('trial', trial)
                print('eta', eta)
                print('chi', chi)
                print('measublue rho\n---')
                print(rho)
                print('uncertainty \n---')
                print(unc)

                print('actual rho\n ---')
                print(rho_actual)
                print('fidelity', fidelity)
                print('purity', purity)

            return trial, rho, unc, Su, rho_actual, fidelity, purity, eta, chi, angles

        else: # if not E0, just print results
            trial = int(split_filename('.')[0].split('_')[-1])
            print('measublue rho\n---')
            print(rho)
            print('uncertainty \n---')
            print(unc)
            print('actual rho\n ---')
            print(rho_actual)
            print('fidelity', fidelity)
            print('purity', purity)

            return trial, rho, unc, Su, rho_actual, fidelity, purity, angles

def analyze_rhos(filenames, settings=None, id='id'):
    '''Extending get_rho_from_file to include multiple files; 
    __
    inputs:
        filenames: list of filenames to analyze
        settings: dict of settings for the experiment
        id: str, special identifier of experiment; used for naming the df
    __
    returns: df with:
        - trial number
        - eta (if they exist)
        - chi (if they exist)
        - fidelity
        - purity
        - W theory (adjusted for purity) and W expt and W unc
        - W' theory (adjusted for purity) and W' expt and W' unc
    '''
    # initialize df
    df = pd.DataFrame()

    for i, file in tqdm(enumerate(filenames)):
        if settings is None:
            try:
                trial, rho, unc, Su, rho_actual, fidelity, purity, eta, chi, angles = get_rho_from_file(file, verbose=False)
            except:
                trial, rho, unc, Su, rho_actual, fidelity, purity, angles = get_rho_from_file(file, verbose=False)
                eta, chi = None, None
        else:
            try:
                trial, rho, _, Su, rho_actual, fidelity, purity, eta, chi, angles = get_rho_from_file(file, angles = settings[i], verbose=False)
            except:
                trial, rho, _, Su, rho_actual, fidelity, purity, angles = get_rho_from_file(file, verbose=False,angles=settings[i] )
                eta, chi = None, None


        # calculate W and W' theory
        W_T_ls = compute_witnesses(rho = rho_actual) # theory
        W_AT_ls = compute_witnesses(rho = rho_actual, expt_purity=purity) # adjusted theory

        # calculate W and W' expt
        W_expt_ls = compute_witnesses(rho = rho, expt=True, stokes_unc=Su)

        # parse lists
        W_min_T = W_T_ls[0]
        Wp_t1_T = W_T_ls[1]
        Wp_t2_T = W_T_ls[2]
        Wp_t3_T = W_T_ls[3]
        # ---- #
        W_min_AT = W_AT_ls[0]
        Wp_t1_AT = W_AT_ls[1]
        Wp_t2_AT = W_AT_ls[2]
        Wp_t3_AT = W_AT_ls[3]
        # ---- #
        W_min_expt = W_expt_ls[0][0][0]
        W_min_unc = W_expt_ls[0][1][0]
        Wp_t1_expt = W_expt_ls[1][0]
        Wp_t1_unc = W_expt_ls[1][1]
        Wp_t2_expt = W_expt_ls[2][0]
        Wp_t2_unc = W_expt_ls[2][1]
        Wp_t3_expt = W_expt_ls[3][0]
        Wp_t3_unc = W_expt_ls[3][1]

        if eta is not None and chi is not None:
            df = pd.concat([df, pd.DataFrame.from_records([{'trial':trial, 'eta':eta, 'chi':chi, 'fidelity':fidelity, 'purity':purity, 
            'W_min_T': W_min_T, 'Wp_t1_T':Wp_t1_T, 'Wp_t2_T':Wp_t2_T, 'Wp_t3_T':Wp_t3_T,'W_min_AT':W_min_AT, 'W_min_expt':W_min_expt, 'W_min_unc':W_min_unc, 'Wp_t1_AT':Wp_t1_AT, 'Wp_t2_AT':Wp_t2_AT, 'Wp_t3_AT':Wp_t3_AT, 'Wp_t1_expt':Wp_t1_expt, 'Wp_t1_unc':Wp_t1_unc, 'Wp_t2_expt':Wp_t2_expt, 'Wp_t2_unc':Wp_t2_unc, 'Wp_t3_expt':Wp_t3_expt, 'Wp_t3_unc':Wp_t3_unc, 'UV_HWP':angles[0], 'QP':angles[1], 'B_HWP':angles[2]}])])

        else:
            df = pd.concat([df, pd.DataFrame.from_records([{'trial':trial, 'fidelity':fidelity, 'purity':purity, 'W_min_AT':W_min_AT, 'W_min_expt':W_min_expt, 'W_min_unc':W_min_unc, 'Wp_t1_AT':Wp_t1_AT, 'Wp_t2_AT':Wp_t2_AT, 'Wp_t3_AT':Wp_t3_AT, 'Wp_t1_expt':Wp_t1_expt, 'Wp_t1_unc':Wp_t1_unc, 'Wp_t2_expt':Wp_t2_expt, 'Wp_t2_unc':Wp_t2_unc, 'Wp_t3_expt':Wp_t3_expt, 'Wp_t3_unc':Wp_t3_unc, 'UV_HWP':angles[0], 'QP':angles[1], 'B_HWP':angles[2]}])])

    # save df
    print('saving!')
    df.to_csv(join(DATA_PATH, f'rho_analysis_{id}.csv'))

def make_plots_E0(dfname):
    '''Reads in df generated by analyze_rhos and plots witness value comparisons as well as fidelity and purity
    __
    dfname: str, name of df to read in
    '''

    id = dfname.split('.')[0].split('_')[-1] # extract identifier from dfname

    # read in df
    df = pd.read_csv(join(DATA_PATH, dfname))
    purity_45 = df['purity'].to_numpy()[:6]
    purity_60 = df['purity'].to_numpy()[6:]
    fidelity_45 = df['fidelity'].to_numpy()[:6]
    fidelity_60 = df['fidelity'].to_numpy()[6:]
    chi_45 = df['chi'].to_numpy()[:6]
    chi_60 = df['chi'].to_numpy()[6:]

    fig, ax = plt.subplots(2, 2, figsize=(20, 10), sharex=True)

    # do purity and fidelity plots
    ax[1,0].scatter(chi_45, purity_45, label='Purity', color='gold')
    ax[1,0].scatter(chi_45, fidelity_45, label='Fidelity', color='turquoise')
    ax[1,0].set_xlabel('$\chi$')
    ax[1,0].set_ylabel('Value')
    ax[1,0].legend()

    ax[1,1].scatter(chi_60, purity_60, label='Purity', color='gold')
    ax[1,1].scatter(chi_60, fidelity_60, label='Fidelity', color='turquoise')
    ax[1,1].set_xlabel('$\chi$')
    ax[1,1].set_ylabel('Value')
    ax[1,1].legend()


    # do witness plots
    # for 45
    W_T_45 = df['W_min_T'].to_numpy()[:6]
    Wp_T_45 = df[['Wp_t1_T', 'Wp_t2_T', 'Wp_t3_T']].min(axis=1).to_numpy()[:6]
    W_AT_45 = df['W_min_AT'].to_numpy()[:6]
    Wp_AT_45 = df[['Wp_t1_AT', 'Wp_t2_AT', 'Wp_t3_AT']].min(axis=1).to_numpy()[:6]
    W_expt_45 = df['W_min_expt'].to_numpy()[:6]
    Wp_expt_45 = df[['Wp_t1_expt', 'Wp_t2_expt', 'Wp_t3_expt']].min(axis=1).to_numpy()[:6]
    W_unc_45 = df['W_min_unc'].to_numpy()[:6]
    Wp_unc_45 = df[['Wp_t1_unc', 'Wp_t2_unc', 'Wp_t3_unc']].min(axis=1).to_numpy()[:6]

    # for 60
    W_T_60 = df['W_min_T'].to_numpy()[6:]
    Wp_T_60 = df[['Wp_t1_T', 'Wp_t2_T', 'Wp_t3_T']].min(axis=1).to_numpy()[6:]
    W_AT_60 = df['W_min_AT'].to_numpy()[6:]
    Wp_AT_60 = df[['Wp_t1_AT', 'Wp_t2_AT', 'Wp_t3_AT']].min(axis=1).to_numpy()[6:]
    W_expt_60 = df['W_min_expt'].to_numpy()[6:]
    Wp_expt_60 = df[['Wp_t1_expt', 'Wp_t2_expt', 'Wp_t3_expt']].min(axis=1).to_numpy()[6:]
    W_unc_60 = df['W_min_unc'].to_numpy()[6:]
    Wp_unc_60 = df[['Wp_t1_unc', 'Wp_t2_unc', 'Wp_t3_unc']].min(axis=1).to_numpy()[6:]

    # do fits
    def sinsq2(x, a, b, c, d):
        return a*np.sin(b*np.deg2rad(x) + c)**2 + d

    popt_E0_W_T_45, pcov_E0_W_T_45 = curve_fit(sinsq2, chi_45, W_T_45)
    popt_E0_Wp_T_45, pcov_E0_Wp_T_45 = curve_fit(sinsq2, chi_45, Wp_T_45)
    popt_E0_W_AT_45, pcov_E0_W_AT_45 = curve_fit(sinsq2, chi_45, W_AT_45)
    popt_E0_Wp_AT_45, pcov_E0_Wp_AT_45 = curve_fit(sinsq2, chi_45, Wp_AT_45)
    popt_E0_W_expt_45, pcov_E0_W_expt_45 = curve_fit(sinsq2, chi_45, W_expt_45, sigma=W_unc_45, absolute_sigma=True, p0=[0,0,0,0])
    popt_E0_Wp_expt_45, pcov_E0_Wp_expt_45 = curve_fit(sinsq2, chi_45, Wp_expt_45, sigma=Wp_unc_45, absolute_sigma=True)

    chi_ls = np.linspace(min(chi_45),max(chi_45), 1000)


    ax[0,0].scatter(chi_45, W_T_45, color='navy')
    ax[0,0].scatter(chi_45, W_AT_45, color='blue')
    ax[0,0].errorbar(chi_45, W_expt_45, yerr = W_unc_45, fmt='s', color='slateblue')

    ax[0,0].scatter(chi_45, Wp_T_45, color='crimson')
    ax[0,0].scatter(chi_45, Wp_AT_45, color='red')
    ax[0,0].errorbar(chi_45, Wp_expt_45, yerr = Wp_unc_45, fmt='s', color='salmon')

    ax[0,0].plot(chi_ls, sinsq2(chi_ls, *popt_E0_W_T_45), color='navy', label="$W_{T}$")
    ax[0,0].plot(chi_ls, sinsq2(chi_ls, *popt_E0_W_AT_45), linestyle='dashed', color='blue', label="$W_{AT}$")
    ax[0,0].plot(chi_ls, sinsq2(chi_ls, *popt_E0_W_expt_45), linestyle='dashdot', color='slateblue', label="$W_{expt}$")

    ax[0,0].plot(chi_ls, sinsq2(chi_ls, *popt_E0_Wp_T_45), color='crimson', label="$W_{T}'$")
    ax[0,0].plot(chi_ls, sinsq2(chi_ls, *popt_E0_Wp_AT_45), linestyle='dashed', color='red', label="$W_{AT}'$")
    ax[0,0].plot(chi_ls, sinsq2(chi_ls, *popt_E0_Wp_expt_45), linestyle='dashdot', color='salmon', label="$W_{expt}'$")


    ax[0,0].set_ylabel('$W$')
    ax[0,0].set_title('$\eta = 45\degree$')
    ax[0,0].legend(ncol=2)

    ax[0,1].scatter(chi_60, W_T_60,color='navy')
    ax[0,1].scatter(chi_60, W_AT_60, color='blue')
    ax[0,1].errorbar(chi_60, W_expt_60, yerr = W_unc_60, fmt='s', color='slateblue')

    ax[0,1].scatter(chi_60, Wp_T_60, color='crimson')
    ax[0,1].scatter(chi_60, Wp_AT_60, color='red')
    ax[0,1].errorbar(chi_60, Wp_expt_60, yerr = Wp_unc_60, fmt='s', color='salmon')


    # do fits
    popt_E0_W_T_60, pcov_E0_W_T_60 = curve_fit(sinsq2, chi_60, W_T_60)
    popt_E0_Wp_T_60, pcov_E0_Wp_T_60 = curve_fit(sinsq2, chi_60, Wp_T_60)
    popt_E0_W_AT_60, pcov_E0_W_AT_60 = curve_fit(sinsq2, chi_60, W_AT_60)
    popt_E0_Wp_AT_60, pcov_E0_Wp_AT_60 = curve_fit(sinsq2, chi_60, Wp_AT_60)
    popt_E0_W_expt_60, pcov_E0_W_expt_60 = curve_fit(sinsq2, chi_60, W_expt_60, sigma=W_unc_60, absolute_sigma=True, p0=[0,0,0,0])
    popt_E0_Wp_expt_60, pcov_E0_Wp_expt_60 = curve_fit(sinsq2, chi_60, Wp_expt_60, sigma=Wp_unc_60, absolute_sigma=True)

    ax[0,1].plot(chi_ls, sinsq2(chi_ls, *popt_E0_W_T_60), color='navy', label='$W_T$')
    ax[0,1].plot(chi_ls, sinsq2(chi_ls, *popt_E0_W_AT_60), linestyle='dashed', color='blue', label='$W_{AT}$')
    ax[0,1].plot(chi_ls, sinsq2(chi_ls, *popt_E0_W_expt_60), linestyle='dashdot', color='slateblue', label='$W_{expt}$')

    ax[0,1].plot(chi_ls, sinsq2(chi_ls, *popt_E0_Wp_T_60), color='crimson', label="$W_T'$")
    ax[0,1].plot(chi_ls, sinsq2(chi_ls, *popt_E0_Wp_AT_60), linestyle='dashed', color='red', label="$W_{AT}$'")
    ax[0,1].plot(chi_ls, sinsq2(chi_ls, *popt_E0_Wp_expt_60), linestyle='dashdot',color='salmon', label="$W_{expt}'$")

    ax[0,1].set_ylabel('$W$')
    ax[0,1].set_title('$\eta = 60\degree$'
    )
    ax[0,1].legend(ncol=2)
    
    plt.suptitle('Witnesses for $E_0$ states, $\cos(\eta)|\Psi^+\\rangle + \sin(\eta)e^{i \chi}|\Psi^-\\rangle $')
    plt.tight_layout()
    plt.savefig(join(DATA_PATH, f'exp_witnesses_E0_{id}.pdf'))
    plt.show()

    # save df of params for fit, uncert, and chi2_blue
    def save_info():
        def chi2_blue(data, fit, uncert):
            return np.sum(((data-fit)/uncert)**2)/(len(data)-len(popt_E0_W_T_45))

        chi2_blue_E0_W_expt_45 = chi2_blue(W_expt_45, sinsq2(chi_45, *popt_E0_W_expt_45), W_unc_45)
        chi2_blue_E0_Wp_expt_45 = chi2_blue(Wp_expt_45, sinsq2(chi_45, *popt_E0_Wp_expt_45), Wp_unc_45)

        chi2_blue_E0_W_expt_60 = chi2_blue(W_expt_60, sinsq2(chi_60, *popt_E0_W_expt_60), W_unc_60)
        chi2_blue_E0_Wp_expt_60 = chi2_blue(Wp_expt_60, sinsq2(chi_60, *popt_E0_Wp_expt_60), Wp_unc_60)

        df = pd.DataFrame({'eta':[], 'w_type':[], 'a':[], 's_a':[], 'b':[], 's_b':[], 'c':[], 's_c':[], 'd':[], 's_d':[], 'chi2_red_W_expt':[], 'chi2_red_Wp_expt':[]})

        df = pd.concat([df, pd.DataFrame({'eta':[45], 'w_type':['W_T'],'a':[popt_E0_W_T_45[0]], 's_a':[np.sqrt(pcov_E0_W_T_45[0,0])], 'b':[popt_E0_W_T_45[1]], 's_b':[np.sqrt(pcov_E0_W_T_45[1,1])], 'c':[popt_E0_W_T_45[2]], 's_c':[np.sqrt(pcov_E0_W_T_45[2,2])], 'd':[popt_E0_W_T_45[3]], 's_d':[np.sqrt(pcov_E0_W_T_45[3,3])], 'chi2_red_W_expt':[None], 'chi2_red_Wp_expt':[None]})], ignore_index=True)

        df = pd.concat([df, pd.DataFrame({'eta':[45], 'w_type':['Wp_T'],'a':[popt_E0_Wp_T_45[0]], 's_a':[np.sqrt(pcov_E0_Wp_T_45[0,0])], 'b':[popt_E0_Wp_T_45[1]], 's_b':[np.sqrt(pcov_E0_Wp_T_45[1,1])], 'c':[popt_E0_Wp_T_45[2]], 's_c':[np.sqrt(pcov_E0_Wp_T_45[2,2])], 'd':[popt_E0_Wp_T_45[3]], 's_d':[np.sqrt(pcov_E0_Wp_T_45[3,3])], 'chi2_red_W_expt':[None], 'chi2_red_Wp_expt':[None]})], ignore_index=True)

        df = pd.concat([df, pd.DataFrame({'eta':[45], 'w_type':['W_AT'],'a':[popt_E0_W_AT_45[0]], 's_a':[np.sqrt(pcov_E0_W_AT_45[0,0])], 'b':[popt_E0_W_AT_45[1]], 's_b':[np.sqrt(pcov_E0_W_AT_45[1,1])], 'c':[popt_E0_W_AT_45[2]], 's_c':[np.sqrt(pcov_E0_W_AT_45[2,2])], 'd':[popt_E0_W_AT_45[3]], 's_d':[np.sqrt(pcov_E0_W_AT_45[3,3])], 'chi2_red_W_expt':[None], 'chi2_red_Wp_expt':[None]})], ignore_index=True)

        df = pd.concat([df, pd.DataFrame({'eta':[45], 'w_type':['Wp_AT'],'a':[popt_E0_Wp_AT_45[0]], 's_a':[np.sqrt(pcov_E0_Wp_AT_45[0,0])], 'b':[popt_E0_Wp_AT_45[1]], 's_b':[np.sqrt(pcov_E0_Wp_AT_45[1,1])], 'c':[popt_E0_Wp_AT_45[2]], 's_c':[np.sqrt(pcov_E0_Wp_AT_45[2,2])], 'd':[popt_E0_Wp_AT_45[3]], 's_d':[np.sqrt(pcov_E0_Wp_AT_45[3,3])], 'chi2_red_W_expt':[None], 'chi2_red_Wp_expt':[None]})], ignore_index=True)

        df = pd.concat([df, pd.DataFrame({'eta':[45], 'w_type':['W_expt'],'a':[popt_E0_W_expt_45[0]], 's_a':[np.sqrt(pcov_E0_W_expt_45[0,0])], 'b':[popt_E0_W_expt_45[1]], 's_b':[np.sqrt(pcov_E0_W_expt_45[1,1])], 'c':[popt_E0_W_expt_45[2]], 's_c':[np.sqrt(pcov_E0_W_expt_45[2,2])], 'd':[popt_E0_W_expt_45[3]], 's_d':[np.sqrt(pcov_E0_W_expt_45[3,3])], 'chi2_red_W_expt':[chi2_blue_E0_W_expt_45], 'chi2_red_Wp_expt':[chi2_blue_E0_Wp_expt_45]})], ignore_index=True)

        df = pd.concat([df, pd.DataFrame({'eta':[45], 'w_type':['Wp_expt'],'a':[popt_E0_Wp_expt_45[0]], 's_a':[np.sqrt(pcov_E0_Wp_expt_45[0,0])], 'b':[popt_E0_Wp_expt_45[1]], 's_b':[np.sqrt(pcov_E0_Wp_expt_45[1,1])], 'c':[popt_E0_Wp_expt_45[2]], 's_c':[np.sqrt(pcov_E0_Wp_expt_45[2,2])], 'd':[popt_E0_Wp_expt_45[3]], 's_d':[np.sqrt(pcov_E0_Wp_expt_45[3,3])], 'chi2_red_W_expt':[chi2_blue_E0_W_expt_45], 'chi2_red_Wp_expt':[chi2_blue_E0_Wp_expt_45]})], ignore_index=True)

        df = pd.concat([df, pd.DataFrame({'eta':[60], 'w_type':['W_expt'], 'a':[popt_E0_W_expt_60[0]], 's_a':[np.sqrt(pcov_E0_W_expt_60[0,0])], 'b':[popt_E0_W_expt_60[1]], 's_b':[np.sqrt(pcov_E0_W_expt_60[1,1])], 'c':[popt_E0_W_expt_60[2]], 's_c':[np.sqrt(pcov_E0_W_expt_60[2,2])], 'd':[popt_E0_W_expt_60[3]], 's_d':[np.sqrt(pcov_E0_W_expt_60[3,3])], 'chi2_red_W_expt':[chi2_blue_E0_W_expt_60], 'chi2_red_Wp_expt':[chi2_blue_E0_Wp_expt_60]})], ignore_index=True)

        df = pd.concat([df, pd.DataFrame({'eta':[60], 'w_type':['Wp_expt'], 'a':[popt_E0_Wp_expt_60[0]], 's_a':[np.sqrt(pcov_E0_Wp_expt_60[0,0])], 'b':[popt_E0_Wp_expt_60[1]], 's_b':[np.sqrt(pcov_E0_Wp_expt_60[1,1])], 'c':[popt_E0_Wp_expt_60[2]], 's_c':[np.sqrt(pcov_E0_Wp_expt_60[2,2])], 'd':[popt_E0_Wp_expt_60[3]], 's_d':[np.sqrt(pcov_E0_Wp_expt_60[3,3])], 'chi2_red_W_expt':[chi2_blue_E0_W_expt_60], 'chi2_red_Wp_expt':[chi2_blue_E0_Wp_expt_60]})], ignore_index=True)

        df.to_csv(join(DATA_PATH, 'exp_witnesses_E0.csv'), index=False)

    def make_settings_plots():
        '''Make plots of the settings for the different experiments'''
        from matplotlib.colors import ListedColormap

        # load data
        UV_HWP = np.deg2rad(df['UV_HWP'].to_numpy())
        QP = np.deg2rad(df['QP'].to_numpy())
        B_HWP = np.deg2rad(df['B_HWP'].to_numpy())
        trials = df['trial'].to_numpy()
        chi_total = np.append(chi_45, chi_60)
        chi_total = np.deg2rad(chi_total)
        eta_total = np.deg2rad(df['eta'].to_numpy())

        # UV_HWP = df['UV_HWP'].to_numpy()
        # QP = df['QP'].to_numpy()
        # B_HWP = df['B_HWP'].to_numpy()
        # trials = df['trial'].to_numpy()
        # chi_total = np.append(chi_45, chi_60)
        # eta_total = df['eta'].to_numpy()

        fig, ax = plt.subplots(1, 3, figsize=(15, 5), subplot_kw={'projection': 'polar'})

        colormap = plt.cm.get_cmap('tab20')
        colors = [colormap(i) for i in range(len(UV_HWP))]

        # plot UV HWP settings
        for i, angle in enumerate(UV_HWP):
            ax[0].plot(angle, 1, label='$(%.3g^\degree, %.3g^\degree, %.3g)$' % (np.rad2deg(eta_total[i]), np.rad2deg(chi_total[i]), trials[i]), marker='o', color=colors[i])
        ax[0].set_title('UV HWP settings')
        ax[0].set_xlim(min(UV_HWP)-0.1, max(UV_HWP)+0.1)
        ax[0].legend(ncol=2)

        # plot QP settings
        for i, angle in enumerate(QP):
            ax[1].plot(angle, 1, label='$(%.3g^\degree, %.3g^\degree, %.3g)$' % (np.rad2deg(eta_total[i]), np.rad2deg(chi_total[i]), trials[i]), marker='o', color=colors[i])
        ax[1].set_title('QP settings')
        ax[1].set_xlim(min(QP)-0.1, max(QP)+0.1)
        ax[1].legend(ncol=2)

        # plot B HWP settings
        for i, angle in enumerate(B_HWP):
            ax[2].plot(angle, 1, label='$(%.3g^\degree, %.3g^\degree, %.3g)$' % (np.rad2deg(eta_total[i]), np.rad2deg(chi_total[i]),  trials[i]), marker='o', color=colors[i])
        ax[2].set_title('B HWP settings')
        ax[2].set_xlim(min(B_HWP)-.1, max(B_HWP)+.1)
        ax[2].legend(ncol=2)

        fig.suptitle('Settings for different experiments')

        plt.savefig(join(DATA_PATH, f'settings_{id}.pdf'))

        plt.show()

    save_info()

    make_settings_plots()

if __name__ == '__main__':
    # set filenames for computing W values
    ## new names ##
    # filenames_45 = ["rho_('E0', (45.0, 0.0))_26.npy", "rho_('E0', (45.0, 18.0))_26.npy", "rho_('E0', (45.0, 36.0))_26.npy", "rho_('E0', (45.0, 54.0))_26.npy", "rho_('E0', (45.0, 72.0))_26.npy", "rho_('E0', (45.0, 90.0))_26.npy"]
    # filenames_60= ["rho_('E0', (59.99999999999999, 0.0))_26.npy", "rho_('E0', (59.99999999999999, 18.0))_26.npy", "rho_('E0', (59.99999999999999, 36.0))_26.npy", "rho_('E0', (59.99999999999999, 54.0))_26.npy", "rho_('E0', (59.99999999999999, 72.0))_26.npy", "rho_('E0', (59.99999999999999, 90.0))_26.npy"]
    # filenames = filenames_45 + filenames_60

    ## old ##
    # filenames_45 = ["rho_('E0', (45.0, 0.0))_20.npy", "rho_('E0', (45.0, 18.0))_20.npy", "rho_('E0', (45.0, 36.0))_20.npy", "rho_('E0', (45.0, 54.0))_20.npy", "rho_('E0', (45.0, 72.0))_20.npy", "rho_('E0', (45.0, 90.0))_20.npy"]
    # filenames_60= ["rho_('E0', (59.99999999999999, 0.0))_22.npy", "rho_('E0', (59.99999999999999, 18.0))_22.npy", "rho_('E0', (59.99999999999999, 36.0))_22.npy", "rho_('E0', (59.99999999999999, 54.0))_22.npy", "rho_('E0', (59.99999999999999, 72.0))_22.npy", "rho_('E0', (59.99999999999999, 90.0))_22.npy"]

    # filenames = filenames_45 + filenames_60

    # settings_45 = [[45.0,13.107759739471968,45.0], [40.325617881787,32.45243475604995,45.0], [35.319692011068646,32.80847131578413,45.0], [29.99386625322187,32.59712114540248,45.0], [26.353505137451158,32.91656908476468,44.71253931908844], [20.765759133476752,32.763298596034836,45.0]]
    # settings_60 = [[36.80717351236577,38.298986094951985,45.0], [35.64037134135345,36.377936778443754,44.99999], [32.421520781235735,35.46619180422062,44.99998], [28.842682522467676,34.97796909446873,44.61235], [25.8177216842833,34.72228985431089,44.74163766], [21.614459228879422,34.622127766985436,44.9666]]
    # settings = settings_45 + settings_60
    # analyze rho files
    # analyze_rhos(filenames, settings=settings,id='a')

    make_plots_E0('rho_analysis_fita.csv')

    # get_rho_from_file_depricated("rho_('PhiP',)_19.npy", PhiP)