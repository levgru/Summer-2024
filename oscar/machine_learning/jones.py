# file for jones matrix computations

# main package imports #
from os.path import isdir, join
import os
import numpy as np
from scipy.optimize import minimize, approx_fprime

# special methods for density matrices #
from rho_methods import *
from random_gen import *

#### jones matrices ####
def R(alpha): 
    ''' Rotation matrix for angle alpha'''
    return np.array([[np.cos(alpha), np.sin(alpha)], [-np.sin(alpha), np.cos(alpha)]])
def H(theta): 
    ''' HWP matrix for angle theta'''
    return np.array([[np.cos(2*theta), np.sin(2*theta)], [np.sin(2*theta), -np.cos(2*theta)]])
def Q(alpha): 
    ''' QWP matrix for angle alpha'''
    return R(alpha) @ np.array(np.diag([np.e**(np.pi / 4 * 1j), np.e**(-np.pi / 4 * 1j)])) @ R(-alpha)
def get_QP(phi): 
    ''' QP matrix for angle phi'''
    return np.array(np.diag([1, np.e**(phi*1j)]))
### BBO matrix ###
BBO = np.array([[0, 0, 0, 1], [1, 0,0,0]]).T
def init_state_bg(beta, gamma): 
    ''' Initial polarization state matrix for angles beta, gamma: |psi> = cos(beta)|H> + e^(gamma*i)sin(beta)|V>'''
    return np.array([[np.cos(2*beta),0],[0,np.e**(gamma*1j)*np.sin(2*beta)]])
# initial state for simple=False
Is0 = init_state_bg(0,0)

def get_Jrho(angles, setup = 'C', check=False):
    ''' Main function to get density matrix using Jones Matrix setup.
    Params:
        angles: list of angles for setup. see the conditionals for specifics
        setup: either 'C' for current setup or 'I' for ideal setup
       (i*gamma)|1> or to use a combination of HWP and QP or HWP and 2x QP for C and I respectively
        check: boolean to check if density matrix is valid; don't call when minimizing bc throwing an error will distrupt minimzation process. the check is handled in the while statement in jones_decomp -- for this reason, set to False by default
    '''

    if setup == 'C':
        ''' Jones matrix with *almost* current setup, just adding one QWP on Alice. Computes the rotated polarization state using the following setup:
        UV_HWP -> QP -> BBO -> A_QWP -> A_Detectors
                            -> B_HWP -> B_QWP -> B_Detectors
        '''
        
        ''' Starts with input state with beta = gamma = 0. Input angles:
            UV_HWP, QP, Bob's HWP, Bob's QWP, Alice's QWP
        '''
        # UVHWP 
        theta0 = angles[0]
        # QP
        phi = angles[1]
        # B HWP
        B_theta = angles[2]
        # B and A QWPs
        B_alpha = angles[3]
        A_alpha = angles[4]

        H_UV = H(theta0)
        QP = get_QP(phi)
        H_B = H(B_theta)
        Q_B = Q(B_alpha)
        Q_A = Q(A_alpha)
        
        U = np.kron(Q_A, Q_B @ H_B) @ BBO @ QP @ H_UV
        P = U @ Is0 @ adjoint(U)
        rho = P @ adjoint(P)

    elif setup == 'I':
        ''' Jones matrix method with Ideal setup. Computes the rotated polarization state using the following setup:
            UV_HWP -> QP -> BBO -> A_HWP -> A_QWP -> A_QWP -> A_Detectors
                                -> B_HWP -> B_QWP -> B_QWP -> B_Detectors
        '''
        
        
        ''' Starts with input state with beta = gamma = 0. Input angles:
        UV_HWP, QP0, QP1, Bob's HWP, Alice's HWP, Bob's QWP1, Bob's QWP2, Alice's QWP1, Alice's QWP2
        '''
        # UVHWP 
        theta_0 = angles[0]
        # initial QWPs
        Q_init = angles[1:3]
        # HWPs
        theta_B = angles[3]
        theta_A = angles[4]
        # B and A QWPs
        alpha_B_ls = angles[5:7]
        alpha_A_ls = angles[7:9]

        H_UV = H(theta_0)
        Q0= Q(Q_init[0])
        Q1 = Q(Q_init[1])
        H_B = H(theta_B)
        H_A = H(theta_A)
        Q_B1 = Q(alpha_B_ls[0])
        Q_B2 = Q(alpha_B_ls[1])
        Q_A1 = Q(alpha_A_ls[0])
        Q_A2 = Q(alpha_A_ls[1])

        U = np.kron(Q_A1 @ Q_A2 @ H_A, Q_B1 @ Q_B2 @ H_B) @ BBO @ Q1 @ Q0 @ H_UV
        P = U @ Is0 @ adjoint(U)

        rho = P @ adjoint(P)

    elif setup=='Ca':
        ''' Jones matrix with *almost* current setup, just adding one QWP on Alice. Computes the rotated polarization state using the following setup:
        UV_HWP -> QP -> BBO -> A_QWP -> A_Detectors
                            -> B_HWP -> B_QWP -> B_Detectors
        '''
        
        ''' Starts with input state with beta = gamma = 0. Input angles:
            UV_HWP, QP, Bob's HWP, Bob's QWP, Alice's QWP
        '''
        # UVHWP 
        theta0 = angles[0]
        # QP
        phi = angles[1]
        # B HWP
        B_theta = angles[2]
   
        H_UV = H(theta0)
        QP = get_QP(phi)
        H_B = H(B_theta)

        U = np.kron(np.eye(2), H_B) @ BBO @ QP @ H_UV
        P = U @ Is0 @ adjoint(U)
        rho = P @ adjoint(P)

    else:
        raise ValueError(f'Invalid setup. You have {setup} but needs to be either "C" or "I".')

    ## return density matrix ##
    if check:
        if is_valid_rho(rho):
            return rho
        else:
            print(rho)
            raise ValueError('Invalid density matrix')

    else:
        return rho



def get_random_Jangles(setup):
    ''' Returns random angles for the Jrho_C setup. Confirms that the density matrix is valid.
    params: setup: either 'C' for current setup or 'I' for ideal setup
    '''

    def get_angles():

        if setup=='C':
            # UV HWP
            theta_UV = np.random.rand()*np.pi/4
            # QP
            phi = np.random.rand()*np.pi/2
            # B HWP
            theta_B = np.random.rand()*np.pi/4
            # QWPs
            alpha_ls = np.random.rand(2)*np.pi/2
            angles= [theta_UV, phi, theta_B, *alpha_ls]
        elif setup=='I':
            # UVHWP 
            theta_0 = np.random.rand()*np.pi/4
            # initial QWPs
            Q_init = np.random.rand(2)*np.pi/2
            # HWPs
            theta_ls = np.random.rand(2)*np.pi/4
            # B and A QWPs
            alpha_ls = np.random.rand(4)*np.pi/2

            angles= [theta_0, *Q_init, *theta_ls, *alpha_ls]

        elif setup=='Ca':
            # UV HWP
            theta_UV = np.random.rand()*np.pi/4
            # QP
            phi = np.random.rand()*2*np.pi
            # B HWP
            theta_B = np.random.rand()*np.pi/4
            angles= [theta_UV, phi, theta_B]

        else:
            raise ValueError(f'Invalid setup. You have {setup} but needs to be either "C" or "I" or "Ca".')

        return angles

    # confirm angles are valid #
    angles = get_angles()
    while not(is_valid_rho(get_Jrho(angles=angles, setup=setup))):
        angles = get_angles()
    return angles


def get_random_jones(setup='C', return_params=False):
    ''' Computes random angles in the ranges specified and generates the resulting states'''
    # get random angles
    angles = get_random_Jangles(setup=setup)
    # get density matrix
    rho = get_Jrho(setup=setup, angles=angles)

    if return_params: return [rho, angles]
    else: return rho

def jones_decompose(targ_rho, targ_name='Test', setup = 'C', adapt=0, frac = 0.001, zeta = 0.01, gd_tune=False, save_rho = False, debug=False, verbose=True, epsilon=0.999, N = 10000):
    ''' Function to decompose a given density matrix into jones matrices
    params:
        targ_rho: target density matrix
        targ_name: name of target state
        setup: either 'C' for current setup or 'I' for ideal setup
        adapt: 0: random hop, 1: random fan, 2: gradient descent
        frac: what percentage of the domain of the angles to change each time in adapt
        zeta: learning rate for gradient descent
        state_num: number of the state to decompose for progress tracking
        gd_tune: whether to output parameters for gd tuning
        save_rho: whether to save the density matrix
        verbose: whether to include print statements.
        debug: whether to enforce try/excpet to block errors
        epsilon: maximum tolerance for fidelity; if reached, halleljuah and break early!
        N: max number of times to try to optimize
    returns:
        angles: list of angles matching setup return. note beta and gamma, which set the initial polarization state, are the first two elements
        fidelity: fidelity of the resulting guessed state
    note: if you use Cntrl-C to break out of the function, it will return the best guess so far
    RETURNS: targ_name, setup, adapt, n, max_best_fidelity, max_best_angles, proj_pred[:4], proj_targ[:4], proj_pred[4:8], proj_targ[4:8], proj_pred[8:], proj_targ[8:]
    '''

    # set zeta to be more aggressive for C based on tuning
    if setup=='C':
        zeta=0.07

    elif setup=='Ca':
        frac=.02
        zeta=1

    def decompose():
        func = lambda angles: get_Jrho(angles=angles, setup=setup)

        # iset bounds for guesses
        H_bound = (0, np.pi/4)
        Q_bound = (0, np.pi/2)
        QP_bound = (0, 2*np.pi)
        if setup=='C':
            # theta_0, phi, theta_B, alpha_B1, alpha_B2
            # bounds = [(0, np.pi/4), (0, np.pi/2), (0, np.pi/4), (0, np.pi/2), (0, np.pi/2)]
            bounds = [H_bound, QP_bound, H_bound, Q_bound, Q_bound]
        elif setup=='I':
            # theta_uv, alpha_0, alpha_1, theta_B, theta_A, alpha_B1, alpha_B2, alpha_A1, alpha_A2
            # bounds = [(0, np.pi/4),  (0, np.pi/2), (0, np.pi/2), (0, np.pi/4), (0, np.pi/4), (0, np.pi/2), (0, np.pi/2), (0, np.pi/2), (0, np.pi/2)]
            bounds = [H_bound, Q_bound, Q_bound, H_bound, H_bound, Q_bound, Q_bound, Q_bound, Q_bound]
        elif setup=='Ca':
            # theta_uv, phi, theta_B
            bounds = [H_bound, QP_bound, H_bound]
        else:
            raise ValueError(f'Invalid setup. Must be either "C" or "I" or "Ca". You have {setup}.')

        def loss_fidelity(angles):
            ''' Function to quantify the distance between the targ and pred density matrices'''
            pred_rho = func(angles)
            fidelity = get_fidelity(pred_rho, targ_rho)
            
            return 1-np.sqrt(fidelity)

        # get initial result
        def minimize_angles(x0):
            result = minimize(loss_fidelity, x0=x0, bounds=bounds)
            best_angles = result.x
            rho = func(best_angles)
            fidelity = get_fidelity(rho, targ_rho)
            return best_angles, fidelity, rho

        x0 = get_random_Jangles(setup=setup)
        best_angles, fidelity, rho = minimize_angles(x0)
        
        # iterate eiher until we hit max bound or we get a valid rho with fidelity above the min
        if is_valid_rho(rho) and (fidelity < 1 or np.isclose(fidelity, 1, rtol=1e-9)):
            max_best_fidelity = fidelity
            max_best_angles = best_angles
        else:
            max_best_fidelity = 0
            max_best_angles = [0 for _ in best_angles]
        grad_angles = max_best_angles # keep track of the angles for gradient descent

        n=0 # keep track of overall number of iterations
        index_since_improvement = 0 # keep track of number of iterations since the max fidelity last improved
        while n < N and max_best_fidelity<epsilon:
            try:
                if verbose: 
                    print('n', n)
                    print(fidelity, max_best_fidelity)
                
                ### different strategies ###
                ## random fan ##
                if adapt==1 and not(np.all(max_best_angles == np.zeros(len(max_best_angles)))):
                    m+=1
                    if m>0:
                        if m==frac*N:
                            x0 = get_random_Jangles(setup=setup)
                            m=-frac*N

                        x0 = [np.random.uniform(max(bounds[i][0], max_best_angles[i] * (1 - m * ((bounds[i][1] - bounds[i][0]) / (frac * N)))),
                            min(bounds[i][1], max_best_angles[i] * (1 + m * ((bounds[i][1] - bounds[i][0]) / (frac * N)))))
        for i in range(len(max_best_angles))]

                    else: # cool down
                        x0 = get_random_Jangles(setup=setup)

                ## gradient descent ##
                elif adapt==2:            
                    if index_since_improvement % (frac*N)==0: # periodic random search (hop)
                        x0 = get_random_Jangles(setup=setup)
                    else:
                        gradient = approx_fprime(grad_angles, loss_fidelity, epsilon=1e-8) # epsilon is step size in finite difference
                        if verbose: print(gradient)
                        # update angles
                        x0 = [max_best_angles[i] - zeta*gradient[i] for i in range(len(max_best_angles))]
                        grad_angles = x0


                ## random hop ##
                else:
                    x0 = get_random_Jangles(setup=setup)

                best_angles, fidelity, rho = minimize_angles(x0)

                if fidelity > max_best_fidelity and is_valid_rho(rho) and (fidelity < 1 or np.isclose(fidelity, 1, rtol=1e-9)):
                    max_best_fidelity = fidelity
                    max_best_angles = best_angles
                    index_since_improvement = 0
                elif not(is_valid_rho(rho)):
                    n-=1
                else:
                    index_since_improvement += 1

                n+=1

            except KeyboardInterrupt:
                print('interrupted...saving best result so far')
                break

        # compute projections in 12 basis states
        best_pred_rho = func(max_best_angles)
        proj_pred = get_12s_redundant_projections(func(max_best_angles))
        proj_targ = get_12s_redundant_projections(targ_rho)

        # if verbose:
        # print('index of state generated', i)
        print('actual state', targ_rho)
        print('predicted state', func(max_best_angles) )
        print('num iterations', n)
        print('fidelity', max_best_fidelity)
        print('projections of predicted', proj_pred)
        print('projections of actual', proj_targ)

        if not(gd_tune):
            if save_rho: # save best predicted and actual rho
                # create new directory
                if not(isdir(join('decomp', targ_name, setup))):
                    os.makedirs(join('decomp', targ_name, setup))
                # save rho
                np.save(join('decomp', targ_name, setup, f'pred_rho_{n}_{max_best_fidelity}'), best_pred_rho)
                np.save(join('decomp', targ_name, setup, f'targ_rho'), targ_rho)

            return targ_name, setup, adapt, n, max_best_fidelity, max_best_angles, best_pred_rho, targ_rho

        else:
            return setup, frac, zeta, n, max_best_fidelity

    if not(debug):
        try:
            return decompose()
        except Exception as e:
            print('Error!', e)
    else:
        return decompose()

if __name__=='__main__':
    # for loading data
    import pandas as pd
    # for progress bar
    from tqdm import tqdm, trange
    # for parallel processing
    from multiprocessing import cpu_count, Pool
    # # for viewing arguments of function
    import matplotlib.pyplot as plt
    from matplotlib import cm

    # import predefined states for testing
    from sample_rho import *
    from random_gen import *


    def do_full_ex_decomp(setup,adapt=0, bell=False, e0=False,e1=False, random=False, jones_C=False, jones_I=False, roik=False, num_random=100, savename='test') :
        ''' Run example decompositions using the C setup.
        Params:
            setup: 'C' or 'I' or 'B' for both.
            adapt: 0 for no adaptation, 1 for random fan, 2 for gradient descent
            savename: name of file to save results to
            bell: whether to include bell states
            num_random: number of random states to decompose
            (optional) num_random: number of random states to decompose
        '''
        
        states = []
        states_names = []
        ## compile states ##
        if bell:
            for i in range(num_random):
                states_bell = [PhiP, PhiM, PsiP, PsiM]
                states_bell_names = ['PhiP', 'PhiM', 'PsiP', 'PsiM']
                states += states_bell
                states_names += states_bell_names
        if e0:
            # get random Eritas states
            states_E0_all = [get_random_E0() for i in range(num_random)]
            states_E0 = [states_E0_all[i][0] for i in range(num_random)]
            states_E0_names = [f'E0_{states_E0_all[i][1][0]}_{states_E0_all[i][1][1]}' for i in range(num_random)]

            states+=states_E0
            states_names+=states_E0_names

        if e1:
            states_E1_all = [get_random_E1() for i in range(num_random)]
            states_E1 = [states_E1_all[i][0] for i in range(num_random)]   
            states_E1_names = [f'E1_{states_E1_all[i][1][0]}_{states_E1_all[i][1][1]}' for i in range(num_random)]

            states+=states_E1
            states_names+=states_E1_names
        if random:
            states_RS_all = [get_random_simplex(return_params=True) for i in range(num_random)]
            states_RS = [states_RS_all[i][0] for i in range(num_random)]
            states_RS_names = [f'RS_{states_RS_all[i][1][0]}_{states_RS_all[i][1][1]}_{states_RS_all[i][1][2]}_{states_RS_all[i][1][3]}__{states_RS_all[i][1][4]}__{states_RS_all[i][1][5]}__{states_RS_all[i][1][6]}' for i in range(num_random)]
       
            states+=states_RS
            states_names+=states_RS_names
        if jones_C:
            # get random Jones states
            states_jones_all = [get_random_jones(setup='C', return_params=True) for i in range(num_random)]
            states_jones = [states_jones_all[i][0] for i in range(num_random)]
            states_jones_names = [f'jones_{states_jones_all[i][1]}' for i in range(num_random)]

            states+=states_jones
            states_names+=states_jones_names
        if jones_I:
            # get random Jones states
            states_jones_all = [get_random_jones(setup='I', return_params=True) for i in range(num_random)]
            states_jones = [states_jones_all[i][0] for i in range(num_random)]
            states_jones_names = [f'jones_{states_jones_all[i][1]}' for i in range(num_random)]

            states+=states_jones
            states_names+=states_jones_names
        if roik:
            print('generating random separable roik states...')
            states_roik_all = []
            for i in trange(num_random):
                states_roik_all.append(get_random_roik(.95))
            states_roik = [states_roik_all[i][0] for i in range(num_random)]
            states_roik_names = [f'roik_{states_roik_all[i][1]}' for i in range(num_random)]

            states+=states_roik
            states_names+=states_roik_names
        
        print('num states:', len(states))
        # list to hold the parameters (i, setup, simple) to pass to the pool multiprocessing object
        decomp_ls = []
        for i in trange(len(states)):
            if setup=='B':
                for option in ['Ca', 'C','I']:
                    decomp_ls.append((i, option, adapt))
            else:
                decomp_ls.append((i, setup, adapt))
        
        print(decomp_ls)

        ## build multiprocessing pool ##
        pool = Pool(cpu_count())

        inputs = [(states[decomp_in[0]], states_names[decomp_in[0]], decomp_in[1], decomp_in[2], i) for  i, decomp_in in enumerate(decomp_ls)]        
        results = pool.starmap_async(jones_decompose, inputs).get()

        ## end multiprocessing ##
        pool.close()
        pool.join()

        # filter None results out
        results = [result for result in results if result is not None] 

        ## save to df ##
        columns = ['state', 'setup', 'adapt', 'n', 'fidelity', 'angles', 'targ_rho', 'pred_rho']
        decomp_df = pd.DataFrame.from_records(results, columns=columns)
        decomp_df.to_csv(join('decomp', savename+'.csv'))

    def tune_gd(f_min=0.001, f_max = 0.1, f_it =10, zeta_min=0.001, zeta_max=1, zeta_it=10, num_to_avg=10, do_compute=False, do_plot=False):
        ''' Function to tune the gradient descent algorithm based on the PhiM state.
        Params:
            f_min: minimum fraction of N to do hop
            f_max: maximum fraction of N to do hop
            f_it: number of iterations between f_min and f_max
            zeta_min: minimum zeta (learning rate)
            zeta_max: maximum zeta (learning rate)
            zeta_it: number of iterations between zeta_min and zeta_max
            num_to_avg: number of times to repeat each config to get average and sem
            do_compute: whether to compute new data
            do_plot: whether to plot data
        N.b. defaults based on initial run.
        '''
        assert do_compute or do_plot, 'must do at least one of compute or plot'

        savename=f'gd_tune_{f_min}_{f_max}_{f_it}_{zeta_min}_{zeta_max}_{zeta_it}_{num_to_avg}_all'

        f_ls = np.logspace(np.log10(f_min), np.log10(f_max), f_it)
        zeta_ls = np.logspace(np.log10(zeta_min), np.log10(zeta_max), zeta_it)
        sfz_ls = []
        sfz_unique = []
        f_plot_ls = []
        zeta_plot_ls = []
        for frac in f_ls:
            for zeta in zeta_ls:
                f_plot_ls.append(frac)
                zeta_plot_ls.append(zeta)
                for setup in ['Ca', 'C', 'I']:
                    sfz_unique.append([setup, frac, zeta]) # get unique configs
                    for j in range(num_to_avg): # repeat each config num_to_avg times
                        sfz_ls.append([setup, frac, zeta])
                # sfz_unique.append(['Ca', frac, zeta]) # get unique configs
                # for j in range(num_to_avg): # repeat each config num_to_avg times
                #     sfz_ls.append(['Ca', frac, zeta])
        
        print(sfz_ls, len(sfz_ls))
        print(savename)
        
        def compute():

            ## build multiprocessing pool ##
            pool = Pool(cpu_count())

            # targ_rho, targ_name='Test', setup = 'C', adapt=0, frac = 0.1, zeta = 0, state_num = 0, gd_tune=False, debug

            # old: use PhiM
            # inputs = [(PhiM, 'PhiM', sfz[0], 2, sfz[1], sfz[2], True) for  sfz in sfz_ls]        

            # new: use random states
            inputs = [(get_random_simplex(), 'RS', sfz[0], 2, sfz[1], sfz[2], i, True) for i, sfz in enumerate(sfz_ls)]
            results = pool.starmap_async(jones_decompose, inputs).get()

            # end multiprocessing
            pool.close()
            pool.join()

            # filter None results out
            results = [result for result in results if result is not None]

            # get all unique configs
            cols = ['setup', 'frac', 'zeta', 'n', 'fidelity']
            df = pd.DataFrame.from_records(results, columns=cols)
            df.to_csv(join('decomp', savename+'.csv'))

        def plot():
            n_Ca_ls =[]
            n_Ca_sem_ls = []
            fidelity_Ca_ls = []
            fidelity_Ca_sem_ls = []
            n_C_ls = []
            n_C_sem_ls = []
            fidelity_C_ls = []
            fidelity_C_sem_ls = []
            n_I_ls = []
            n_I_sem_ls = []
            fidelity_I_ls = []
            fidelity_I_sem_ls = []

            for sfz in sfz_unique:
                setup = sfz[0]
                df_sfz = df.loc[(df['setup'] == setup) & np.isclose(df['frac'], sfz[1], rtol=1e-4) & np.isclose(df['zeta'], sfz[2], rtol=1e-4) & (df['n'] > 0) & ((np.isclose(df['fidelity'], 1, rtol=1e-4)) | (df['fidelity']<1))]
                df_test = df.loc[(df['setup']==setup) & np.isclose(df['frac'], sfz[1], rtol=1e-4) & np.isclose(df['zeta'], sfz[2], rtol=1e-4)]
                df_test_n = df_test.loc[df_test['n'] != 0]
                assert len(df_sfz) > 0, f'no results for this config {sfz}_{df_test_n}'

                n_avg = np.mean(df_sfz['n'].to_numpy())
                n_sem = np.std(df_sfz['n'].to_numpy())/np.sqrt(len(df_sfz['n'].to_numpy()))
                fidelity_avg = np.mean(df_sfz['fidelity'].to_numpy())
                fidelity_sem = np.std(df_sfz['fidelity'].to_numpy())/np.sqrt(len(df_sfz['fidelity'].to_numpy()))

                if setup=='Ca':
                    n_Ca_ls.append(n_avg)
                    n_Ca_sem_ls.append(n_sem)
                    fidelity_Ca_ls.append(fidelity_avg)
                    fidelity_Ca_sem_ls.append(fidelity_sem)
                elif setup=='C':
                    n_C_ls.append(n_avg)
                    n_C_sem_ls.append(n_sem)
                    fidelity_C_ls.append(fidelity_avg)
                    fidelity_C_sem_ls.append(fidelity_sem)
                elif setup=='I':
                    n_I_ls.append(n_avg)
                    n_I_sem_ls.append(n_sem)
                    fidelity_I_ls.append(fidelity_avg)
                    fidelity_I_sem_ls.append(fidelity_sem)

            # save csv summary of results #
            summary = pd.DataFrame()
            summary['frac'] = f_plot_ls
            summary['zeta'] = zeta_plot_ls
            summary['n_Ca'] = n_Ca_ls
            summary['n_Ca_sem'] = n_Ca_sem_ls
            summary['fidelity_Ca'] = fidelity_Ca_ls
            summary['fidelity_Ca_sem'] = fidelity_Ca_sem_ls
            summary['n_C'] = n_C_ls
            summary['n_C_sem'] = n_C_sem_ls
            summary['fidelity_C'] = fidelity_C_ls
            summary['fidelity_C_sem'] = fidelity_C_sem_ls
            summary['n_I'] = n_I_ls
            summary['n_I_sem'] = n_I_sem_ls
            summary['fidelity_I'] = fidelity_I_ls
            summary['fidelity_I_sem'] = fidelity_I_sem_ls
            summary.to_csv(join('decomp', savename+'_summary.csv'))
            
            pd.set_option('display.max_columns', None)
            # print best configurations #
            print('best Ca config:\n', summary.sort_values(['n_Ca', 'fidelity_Ca'], ascending=[True, False]).head())
            print('best C config:\n', summary.sort_values(['n_C', 'fidelity_C'], ascending=[True, False]).head())
            print('------------')
            print('best I config:\n', summary.sort_values(['n_I', 'fidelity_I'], ascending=[True, False]).head())

            fig= plt.figure()
            ax0 = fig.add_subplot(311, projection='3d')
            sc0= ax0.scatter(f_plot_ls, zeta_plot_ls, n_Ca_ls, marker='o', c=np.array(fidelity_Ca_ls), cmap=plt.cm.viridis)
            cb0 = fig.colorbar(sc0, ax=ax0, shrink=1)
            cb0.ax.set_position(cb0.ax.get_position().translated(0.09, 0))
            ax0.set_xlabel('$f$')
            ax0.set_ylabel('$\zeta$')
            ax0.set_zlabel('$\overline{n}$')
            ax0.set_title('Ca setup')

            ax1 = fig.add_subplot(312, projection='3d')
            sc1= ax1.scatter(f_plot_ls, zeta_plot_ls, n_C_ls, marker='o', c=np.array(fidelity_C_ls), cmap=plt.cm.viridis)
            cb1 = fig.colorbar(sc1, ax=ax1, shrink=1)
            cb1.ax.set_position(cb1.ax.get_position().translated(0.09, 0))
            ax1.set_xlabel('$f$')
            ax1.set_ylabel('$\zeta$')
            ax1.set_zlabel('$\overline{n}$')
            ax1.set_title('C setup')

            ax2 = fig.add_subplot(313, projection='3d')
            sc2= ax2.scatter(f_plot_ls, zeta_plot_ls, n_I_ls, marker='o', c=np.array(fidelity_I_ls), cmap=plt.cm.viridis)
            cb2 = fig.colorbar(sc2, ax=ax2, shrink=1)
            cb2.ax.set_position(cb2.ax.get_position().translated(0.09, 0))
            ax2.set_xlabel('$f$')
            ax2.set_ylabel('$\zeta$')
            ax2.set_zlabel('$\overline{n}$')
            ax2.set_title('I setup')

            # fig.set_size_inches(6, 15)
            # plt.tight_layout()

            plt.savefig(join('decomp', savename+'.pdf'))
            plt.show()
    
        if do_compute: compute()
        if do_plot:
            df = pd.read_csv(join('decomp', savename+'.csv'))
            plot()


    resp = int(input('0 to run decomp_ex_all, 1 to tune gd, 2 to test eritas states on ca'))
    
    ## test states and get average fidelity ##
    if resp == 0:
        setup = input('Enter setup: C or I, or B for both')
        assert setup in ['C', 'I', 'B', 'Ca'], f'invalid setup. you have {setup}'
        adapt = int(input('0 for random hop, 1 for random fan, 2 for gradient descent'))
        assert adapt in [0, 1, 2], f'invalid adapt. you have {adapt}'
        bell = bool(int(input('include bell states?')))
        e0 = bool(int(input('include eritas 0 state?')))
        e1 = bool(int(input('include eritas 1 state?')))
        random = bool(int(input('include random states?')))
        jones_C = bool(int(input('include jones states in C setup?')))
        jones_I = bool(int(input('include jones states in I setup?')))
        roik = bool(int(input('include roik states?')))
        special = input('special name to append to file?')
        num_random = int(input('number of random states to generate?'))
        savename = f'decomp_all_{bell}_{e0}_{e1}_{random}_{special}'
        print(setup, adapt, bell, e0, e1, random, jones_C, jones_I, roik)

        do_full_ex_decomp(setup=setup, bell=bell, e0=e0, e1=e1,random=random, jones_C = jones_C, jones_I = jones_I, roik=roik, savename=savename, num_random=num_random)

    elif resp==1:
         ## optimize gradient descent params, f and zeta ##
        do_compute = bool(int(input('run computation? ')))
        do_plot = bool(int(input('plot results? ')))
        num_to_avg= int(input('number of times to average? '))
        if not(isdir('decomp')): os.makedirs('decomp')
        tune_gd(do_compute=do_compute, do_plot=do_plot, f_it=20, zeta_it=20, num_to_avg=num_to_avg)

    
    elif resp==2:
        # eta_ls = np.linspace(0, np.pi/2, 3)
        # chi_ls = np.linspace(0, 2*np.pi,3)
        eta_ls = np.random.rand(3)*np.pi/2
        chi_ls = np.random.rand(3)*2*np.pi
        E0_states = []
        E1_states = []
        state_angles = []
        for eta in eta_ls:
            for chi in chi_ls:
                E0_states.append(get_E0(eta, chi))
                E1_states.append(get_E1(eta, chi))
                state_angles.append([eta, chi])

        e_df = pd.DataFrame({'state': [], 'eta, chi':[], 'fidelity':[],'angles':[], 'pred rho':[], 'targ rho':[]})

        
        for i, E0_state in enumerate(tqdm(E0_states)):
            targ_name, setup, adapt, n, fidelity, angles, pred_rho, targ_rho = jones_decompose(E0_state, targ_name='E0', setup = 'Ca')

            e_df = pd.concat([e_df, pd.DataFrame.from_records([{'state': 'E0', 'eta, chi':state_angles[i], 'fidelity':fidelity,'angles':angles, 'pred rho':pred_rho, 'targ rho':targ_rho}])])


        for i, E1_state in enumerate(tqdm(E1_states)):
            targ_name, setup, adapt, n, fidelity, angles, pred_rho, targ_rho = jones_decompose(E0_state, targ_name='E1', setup = 'Ca')

            e_df = pd.concat([e_df, pd.DataFrame.from_records([{'state': 'E1', 'eta, chi':state_angles[i], 'fidelity':fidelity,'angles':angles, 'pred rho':pred_rho, 'targ rho':targ_rho}])])

        e_df.to_csv(join('decomp', 'eritas_states.csv'))
        print(e_df)

