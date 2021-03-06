import numpy as np
from utils import *
from skfem.helpers import *
from scipy.sparse.linalg import LinearOperator, minres, cg
from skfem.assembly import BilinearForm, LinearForm
import datetime
import pandas as pd
from skfem.visuals.matplotlib import draw, plot, show
import sys
import time

tol = 1e-11
intorder = 8
solver_type = 'mgcg'
refine_time = 6
epsilon_range = 7
element_type = 'P1'
sigma = 5
penalty = False
# epsilon = 1e-5
example = 'ex4'
save_path = 'log/' + example + '_' + element_type + '_' + ('pen' if penalty else 'nopen') + '_' +'{}'.format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))

# output to txt 
class Logger(object):
    def __init__(self, filename=save_path+'.txt', stream=sys.stdout):
	    self.terminal = stream
	    self.log = open(filename, 'a')

    def write(self, message):
	    self.terminal.write(message)
	    self.log.write(message)

    def flush(self):
	    pass

sys.stdout = Logger(save_path+'.txt', sys.stdout)

def solve_problem1(m, element_type='P1', solver_type='pcg', intorder=6, tol=1e-8, epsilon=1e-6):
    '''
    switching to mgcg solver for problem 1
    '''
    if element_type == 'P1':
        element = {'w': ElementTriP1(), 'u': ElementTriMorley()}
    elif element_type == 'P2':
        element = {'w': ElementTriP2(), 'u': ElementTriMorley()}
    else:
        raise Exception("Element not supported")

    basis = {
        variable: InteriorBasis(m, e, intorder=intorder)
        for variable, e in element.items()
    }
    
    K1 = asm(laplace, basis['w'])
    f1 = asm(f_load, basis['w'])
    wh = np.zeros(basis['w'].N)
    boundary_dofs = basis['w'].find_dofs()['all'].all()
    wh[boundary_dofs] = exact_u(basis['w'].doflocs[0][boundary_dofs], basis['w'].doflocs[1][boundary_dofs])
    wh = solve(*condense(K1, f1, wh, D=boundary_dofs), solver=solver_iter_mgcg(tol=tol))

    K2 = epsilon**2 * asm(a_load, basis['u']) + asm(b_load, basis['u'])
    f2 = asm(wv_load, basis['w'], basis['u']) * wh
    boundary_dofs = basis['u'].find_dofs()['all'].all()

    uh0 = project(exact_u, basis_to=basis['u'])
    uh0 = solve(*condense(K2, f2, uh0, D=boundary_dofs), solver=solver_iter_mgcg(tol=tol))
    return uh0, basis

@LinearForm
def f_load(v, w):
    '''
    for $(f, x_{h})$
    '''
    lu = 0
    llu = 0
    return (epsilon**2 * llu - lu) * v

# m = MeshTri().init_lshaped()
# # m = MeshTri()
# # m = MeshTri().init_symmetric()
# m.refine(5)

# epsilon = 1
# ep = epsilon

# uh0, basis = solve_problem1(m, element_type, solver_type, intorder, tol, epsilon)

# x = basis['u'].doflocs[0]
# y = basis['u'].doflocs[1]
# u = exact_u(x, y)
# plot(basis['u'], u-uh0, colorbar=True)


time_start = time.time()

print('=======Arguments=======')
print('penalty:\t{}'.format(penalty))
print('element_type:\t{}'.format(element_type))
print('solver_type:\t{}'.format(solver_type))
print('tol:\t{}'.format(tol))
print('intorder:\t{}'.format(intorder))
print('refine_time:\t{}'.format(refine_time))
print('sigma:\t{}'.format(sigma))
print('=======Results=======')

df_list = []
for j in [1e-5, 1e-6]:
    # epsilon = 1 * 10**(-j)
    epsilon = j
    ep = epsilon
    L2_list = []
    Du_list = []
    D2u_list = []
    h_list = []
    epu_list = []
    m = MeshTri().init_lshaped()
    # m = MeshTri()
#     draw(m)

    for i in range(1, refine_time+1):
        
        m.refine()

        uh0, basis = solve_problem1(m, element_type, solver_type, intorder, tol, epsilon)

        U = basis['u'].interpolate(uh0).value

        # compute errors

        L2u = np.sqrt(L2uError.assemble(basis['u'], w=U))
        Du = get_DuError(basis['u'], uh0)
        H1u = Du + L2u
        if penalty:
            D2u = np.sqrt(get_D2uError(basis['u'], uh0)**2 + L2pnvError.assemble(fbasis, w=fbasis.interpolate(uh0)))
        else:
            D2u = get_D2uError(basis['u'], uh0)
        epu = np.sqrt(epsilon**2 * D2u**2 + Du**2)
        h_list.append(m.param())
        Du_list.append(Du)
        L2_list.append(L2u)
        D2u_list.append(D2u)
        epu_list.append(epu)
        
    hs = np.array(h_list)
    L2s = np.array(L2_list)
    Dus = np.array(Du_list)
    D2us = np.array(D2u_list)
    epus = np.array(epu_list)
    H1s = L2s + Dus
    H2s = H1s + D2us
    
    # store data
    data = np.array([L2s, H1s, H2s, epus])
    df = pd.DataFrame(data.T, columns=['L2', 'H1', 'H2', 'Energy'])
    df_list.append(df)
    
    print('epsilion:', epsilon)
    show_result(L2s, H1s, H2s, epus)

time_end = time.time()

result = df_list[0].append(df_list[1:])
result.to_csv(save_path+'.csv')
print('======= Errors saved in:', save_path+'.csv ==========')
print('Total Time Cost {:.2f} s'.format(time_end-time_start))