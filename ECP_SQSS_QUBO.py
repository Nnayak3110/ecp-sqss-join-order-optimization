#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Imports - General purposes
import itertools
import random
import numpy as np
from itertools import combinations
import csv
import pandas as pd

# Imports - D-Wave
import dimod
from dwave.system import DWaveSampler, EmbeddingComposite
from dimod import ConstrainedQuadraticModel, BinaryQuadraticModel
from dimod.binary_quadratic_model import BinaryQuadraticModel
from itertools import combinations
from neal import SimulatedAnnealingSampler
from dimod.serialization.format import Formatter
import dwave.inspector


# Imports - Qiskit
from docplex.mp.model import Model
from qiskit import Aer, IBMQ, execute
from qiskit.algorithms.minimum_eigensolvers import QAOA, NumPyMinimumEigensolver,VQE,SamplingVQE
from qiskit.algorithms.optimizers import SPSA, COBYLA,SLSQP
from qiskit.circuit.library import EfficientSU2
from qiskit_optimization.algorithms import MinimumEigenOptimizer,SolutionSample,OptimizationResultStatus
from qiskit_optimization.converters import QuadraticProgramToQubo
from qiskit_optimization.translators import from_docplex_mp
from qiskit.providers.basicaer import QasmSimulatorPy
from qiskit.utils import QuantumInstance
from qiskit.visualization import *
from qiskit.utils import algorithm_globals
from qiskit.tools.visualization import circuit_drawer
from qiskit_optimization.runtime import VQEClient
from qiskit_optimization.runtime import QAOAClient
from qiskit.circuit.library import QAOAAnsatz
import matplotlib.pyplot as plt
from typing import List, Tuple
from qiskit.primitives import Sampler
from scipy.optimize import minimize
from qiskit.circuit.library import TwoLocal
from qiskit import *

# algorithm_globals.massive=True
# np.set_printoptions(threshold=sys.maxsize)
# from qiskit import IBMQ
# provider=IBMQ.load_account()


# In[3]:


# ================================================================================================= #
# ================================================================================================= #
#                                                                                                   #
# -------------------------------------JOIN ORDER OPTIMIZATION------------------------------------- #
#                                                                                                   #
# ================================================================================================= #
# ================================================================================================= #


# ================================================================================================= #
# ----------------------------------------QUBO Formulation----------------------------------------- #
# ================================================================================================= #


relation_dict = {} #this relation dictionary only valid for ErgastF1 database
relation_dict['driverId'] = ['drivers','qualifying','sprintresult','results','driverstandings','pitstops','laptimes']
relation_dict['constructorId'] = ['constructors','qualifying','results','constructorstandings','constructorresults']
relation_dict['circuitId'] = ['circuits','races']
relation_dict['year'] = ['seasons','races']
relation_dict['raceId'] = ['races','qualifying','sprintresults','pitstops','laptimes','results','driverstandings','constructorstandings','constructorresults']
relation_dict['statusId'] = ['status','sprintresult','results']



class QUBO_formulation:
    """
    The QUBO-formulation class is used to create a quadratic model with the aim of finding the optimal join order.
    """

    def __init__(self, relations):
        self.relations = relations

    def relation_sublists(relations):
        # Creates the power set from the relations
        relations_sublists = sum([list(map(list, combinations(relations, i))) for i in range(len(relations) + 1)], [])

        # Removes the superfluous initial relations and the empty set from the power set
        for i in range(len(relations)+1):
            relations_sublists.pop(0)
        return relations_sublists
    
    def find_joins(relations):
        joins = []
        for key, values in relation_dict.items():
            temp = list(set(values).intersection(set(relations)))
            if len(temp) > 1:
                joins.extend(list(combinations(temp, 2)))
        return joins


    def vars_with_joins(relations):
        joins = QUBO_formulation.find_joins(relations)
        n = len(relations)
        variables = list()
        if n == 3:
            variables = joins
        if n == 4:
            variables += joins
            comb = combinations(joins,2)
            for v in comb:
                if set(v[0]).intersection(set(v[1])):
                    variables.append(list(set(v[1]).union(set(v[0]))))
        if n == 5:
            joins_3 = list()
            joins_4 = list()
            variables += joins

            comb = combinations(joins,2)
            for v in comb:
                if set(v[0]).intersection(set(v[1])):
                    joins_3.append(list(set(v[1]).union(set(v[0]))))
            variables += joins_3

            temp = list()
            for v2 in joins:
                for v3 in joins_3:
                    if len(set(v3).difference(set(v2))) == 2:
                        temp.append(list(set(v2).union(set(v3))))
            [joins_4.append(x) for x in temp if x not in joins_4]
            variables += joins_4
            temp = list()
            for v31 in joins_3:
                for v32 in joins_3:
                    if len(set(v32).difference(set(v31))) == 1:
                        temp.append(list(set(v31).union(set(v32))))
            [joins_4.append(x) for x in temp if x not in joins_4]
            variables += joins_4

        if n == 6:
            joins_3 = list()
            joins_4 = list()
            joins_5 = list()
            variables += joins

            comb = combinations(joins,2)
            for v in comb:
                if set(v[0]).intersection(set(v[1])):
                    joins_3.append(list(set(v[1]).union(set(v[0]))))
            variables += joins_3

            temp = list()
            for v2 in joins:
                for v3 in joins_3:
                    if len(set(v3).difference(set(v2))) == 2:
                        temp.append(list(set(v2).union(set(v3))))
            [joins_4.append(x) for x in temp if x not in joins_4]
            variables += joins_4
            temp = list()
            for v31 in joins_3:
                for v32 in joins_3:
                    if len(set(v32).difference(set(v31))) == 1:
                        temp.append(list(set(v31).union(set(v32))))
            [joins_4.append(x) for x in temp if x not in joins_4]
            variables += joins_4

            temp = list()
            for v2 in joins:
                for v4 in joins_4:
                    if len(set(v4).difference(set(v2))) == 3:
                        temp.append(list(set(v2).union(set(v4))))
            [joins_5.append(x) for x in temp if x not in joins_5]
            temp = list()
            for v3 in joins_3:
                for v4 in joins_4:
                    if len(set(v4).difference(set(v3))) == 2:
                        temp.append(list(set(v3).union(set(v4))))
            [joins_5.append(x) for x in temp if x not in joins_5]
            variables += joins_5
            temp = list()
            for v41 in joins_4:
                for v42 in joins_4:
                    if len(set(v42).difference(set(v41))) == 1:
                        temp.append(list(set(v41).union(set(v42))))
            [joins_5.append(x) for x in temp if x not in joins_5]
            variables += joins_5

        if n == 7:
            joins_3 = list()
            joins_4 = list()
            joins_5 = list()
            joins_6 = list()

            variables += joins
            comb = combinations(joins,2)

            for v in comb:
                if set(v[0]).intersection(set(v[1])):
                    joins_3.append(list(set(v[1]).union(set(v[0]))))
            variables += joins_3

            temp = list()
            for v2 in joins:
                for v3 in joins_3:
                    if len(set(v3).difference(set(v2))) == 2:
                        temp.append(list(set(v2).union(set(v3))))
            [joins_4.append(x) for x in temp if x not in joins_4]
            variables += joins_4
            temp = list()
            for v31 in joins_3:
                for v32 in joins_3:
                    if len(set(v32).difference(set(v31))) == 1:
                        temp.append(list(set(v31).union(set(v32))))
            [joins_4.append(x) for x in temp if x not in joins_4]
            variables += joins_4

            temp = list()
            for v2 in joins:
                for v4 in joins_4:
                    if len(set(v4).difference(set(v2))) == 3:
                        temp.append(list(set(v2).union(set(v4))))
            [joins_5.append(x) for x in temp if x not in joins_5]
            temp = list()
            for v3 in joins_3:
                for v4 in joins_4:
                    if len(set(v4).difference(set(v3))) == 2:
                        temp.append(list(set(v3).union(set(v4))))
            [joins_5.append(x) for x in temp if x not in joins_5]
            variables += joins_5
            temp = list()
            for v41 in joins_4:
                for v42 in joins_4:
                    if len(set(v42).difference(set(v41))) == 1:
                        temp.append(list(set(v41).union(set(v42))))
            [joins_5.append(x) for x in temp if x not in joins_5]
            variables += joins_5

            temp = list()
            for v3 in joins_3:
                for v4 in joins_4:
                    if len(set(v4).difference(set(v3))) == 3:
                        temp.append(list(set(v3).union(set(v4))))
            [joins_6.append(x) for x in temp if x not in joins_6]
            variables += joins_6
            temp = list()
            for v41 in joins_4:
                for v42 in joins_4:
                    if len(set(v42).difference(set(v41))) == 2:
                        temp.append(list(set(v41).union(set(v42))))
            [joins_6.append(x) for x in temp if x not in joins_6]
            variables += joins_6
            temp = list()
            for v1 in joins:
                for v5 in joins_5:
                    if len(set(v5).difference(set(v1))) == 4:
                        temp.append(list(set(v1).union(set(v5))))
            [joins_6.append(x) for x in temp if x not in joins_6]
            variables += joins_6
            temp = list()
            for v3 in joins_3:
                for v5 in joins_5:
                    if len(set(v5).difference(set(v3))) == 3:
                        temp.append(list(set(v3).union(set(v5))))
            [joins_6.append(x) for x in temp if x not in joins_6]
            variables += joins_6
            temp = list()
            for v4 in joins_4:
                for v5 in joins_5:
                    if len(set(v5).difference(set(v4))) == 2:
                        temp.append(list(set(v4).union(set(v5))))
            [joins_6.append(x) for x in temp if x not in joins_6]
            variables += joins_6
            temp = list()
            for v51 in joins_5:
                for v52 in joins_5:
                    if len(set(v52).difference(set(v51))) == 1:
                        temp.append(list(set(v51).union(set(v52))))
            [joins_6.append(x) for x in temp if x not in joins_6]
            variables += joins_6

        if n == 8:
            joins_3 = list()
            joins_4 = list()
            joins_5 = list()
            joins_6 = list()
            joins_7 = list()
            variables += joins
            comb = combinations(joins,2)

            for v in comb:
                if set(v[0]).intersection(set(v[1])):
                    joins_3.append(list(set(v[1]).union(set(v[0]))))
            variables += joins_3

            temp = list()
            for v2 in joins:
                for v3 in joins_3:
                    if len(set(v3).difference(set(v2))) == 2:
                        temp.append(list(set(v2).union(set(v3))))
            [joins_4.append(x) for x in temp if x not in joins_4]
            variables += joins_4
            temp = list()
            for v31 in joins_3:
                for v32 in joins_3:
                    if len(set(v32).difference(set(v31))) == 1:
                        temp.append(list(set(v31).union(set(v32))))
            [joins_4.append(x) for x in temp if x not in joins_4]
            variables += joins_4

            temp = list()
            for v2 in joins:
                for v4 in joins_4:
                    if len(set(v4).difference(set(v2))) == 3:
                        temp.append(list(set(v2).union(set(v4))))
            [joins_5.append(x) for x in temp if x not in joins_5]
            temp = list()
            for v3 in joins_3:
                for v4 in joins_4:
                    if len(set(v4).difference(set(v3))) == 2:
                        temp.append(list(set(v3).union(set(v4))))
            [joins_5.append(x) for x in temp if x not in joins_5]
            variables += joins_5
            temp = list()
            for v41 in joins_4:
                for v42 in joins_4:
                    if len(set(v42).difference(set(v41))) == 1:
                        temp.append(list(set(v41).union(set(v42))))
            [joins_5.append(x) for x in temp if x not in joins_5]
            variables += joins_5

            temp = list()
            for v3 in joins_3:
                for v4 in joins_4:
                    if len(set(v4).difference(set(v3))) == 3:
                        temp.append(list(set(v3).union(set(v4))))
            [joins_6.append(x) for x in temp if x not in joins_6]
            variables += joins_6
            temp = list()
            for v41 in joins_4:
                for v42 in joins_4:
                    if len(set(v42).difference(set(v41))) == 2:
                        temp.append(list(set(v41).union(set(v42))))
            [joins_6.append(x) for x in temp if x not in joins_6]
            variables += joins_6
            temp = list()
            for v1 in joins:
                for v5 in joins_5:
                    if len(set(v5).difference(set(v1))) == 4:
                        temp.append(list(set(v1).union(set(v5))))
            [joins_6.append(x) for x in temp if x not in joins_6]
            variables += joins_6
            temp = list()
            for v3 in joins_3:
                for v5 in joins_5:
                    if len(set(v5).difference(set(v3))) == 3:
                        temp.append(list(set(v3).union(set(v5))))
            [joins_6.append(x) for x in temp if x not in joins_6]
            variables += joins_6
            temp = list()
            for v4 in joins_4:
                for v5 in joins_5:
                    if len(set(v5).difference(set(v4))) == 2:
                        temp.append(list(set(v4).union(set(v5))))
            [joins_6.append(x) for x in temp if x not in joins_6]
            variables += joins_6
            temp = list()
            for v51 in joins_5:
                for v52 in joins_5:
                    if len(set(v52).difference(set(v51))) == 1:
                        temp.append(list(set(v51).union(set(v52))))
            [joins_6.append(x) for x in temp if x not in joins_6]
            variables += joins_6

            temp = list()
            for v41 in joins_4:
                for v42 in joins_4:
                    if len(set(v41).difference(set(v42))) == 3:
                        temp.append(list(set(v41).union(set(v42))))
            [joins_7.append(x) for x in temp if x not in joins_7]
            variables += joins_7
            temp = list()
            for v3 in joins_3:
                for v5 in joins_5:
                    if len(set(v5).difference(set(v3))) == 4:
                        temp.append(list(set(v3).union(set(v5))))
            [joins_7.append(x) for x in temp if x not in joins_7]
            variables += joins_7
            temp = list()
            for v4 in joins_4:
                for v5 in joins_5:
                    if len(set(v5).difference(set(v4))) == 3:
                        temp.append(list(set(v4).union(set(v5))))
            [joins_7.append(x) for x in temp if x not in joins_7]
            variables += joins_7
            temp = list()
            for v51 in joins_5:
                for v52 in joins_5:
                    if len(set(v52).difference(set(v51))) == 2:
                        temp.append(list(set(v51).union(set(v52))))
            [joins_7.append(x) for x in temp if x not in joins_7]
            variables += joins_7
            temp = list()
            for v2 in joins:
                for v6 in joins_6:
                    if len(set(v6).difference(set(v2))) == 5:
                        temp.append(list(set(v2).union(set(v6))))
            [joins_7.append(x) for x in temp if x not in joins_7]
            variables += joins_7
            temp = list()
            for v3 in joins_3:
                for v6 in joins_6:
                    if len(set(v6).difference(set(v3))) == 4:
                        temp.append(list(set(v3).union(set(v6))))
            [joins_7.append(x) for x in temp if x not in joins_7]
            variables += joins_7
            temp = list()
            for v4 in joins_4:
                for v6 in joins_6:
                    if len(set(v6).difference(set(v4))) == 3:
                        temp.append(list(set(v4).union(set(v6))))
            [joins_7.append(x) for x in temp if x not in joins_7]
            variables += joins_7
            for v5 in joins_5:
                for v6 in joins_6:
                    if len(set(v6).difference(set(v5))) == 2:
                        temp.append(list(set(v5).union(set(v6))))
            [joins_7.append(x) for x in temp if x not in joins_7]
            variables += joins_7
            for v61 in joins_6:
                for v62 in joins_6:
                    if len(set(v62).difference(set(v61))) == 1:
                        temp.append(list(set(v61).union(set(v62))))
            [joins_7.append(x) for x in temp if x not in joins_7]
            variables += joins_7
        
        return variables

    def Elimination_vars_weights(All_vars,list2:'variables',costs):
        repeating_vars = list()
        variables_ae = list()
        new_weights = list()
        for i in range(len(All_vars)):
            for j in list2:
                if set(All_vars[i]) == set(j):
                    repeating_vars.append(All_vars[i])
        repeating_vars.append(All_vars[-1])
        [variables_ae.append(x) for x in repeating_vars if x not in variables_ae]
        for i in range(len(variables_ae)):
            for j in range(len(All_vars)):
                if variables_ae[i] == All_vars[j]:
                    new_weights.append(costs[j])
        return variables_ae, new_weights


    def construct_QUBO(relations,weights):
        """
        Method for creating the QUBO model.

        Parameter:
        relations: An n-element list of the relations involved in the join tree.
        """

        # Forming the power set and removing the single relations and the empty set
        list1 = QUBO_formulation.relation_sublists(relations)
        list2 = QUBO_formulation.vars_with_joins(relations)
        variables_ae, weights_ae = QUBO_formulation.Elimination_vars_weights(list1, list2, weights)



        # Number of relation combinations
        n = len(variables_ae)

        # S_1
        s_1_helper = variables_ae

        # S2_new
        s_2_helper = []
        for i in range(n):
            for j in range(i,n):
                if (i != j):
                    if(set(variables_ae[i]).intersection(set(variables_ae[j]))):
                        if(len(variables_ae[i])<=len(variables_ae[j])):
                            if(not set(variables_ae[i]).issubset(set(variables_ae[j]))):
                                s_2_helper.append([i,j])

        return s_1_helper, s_2_helper, n

    
    def construct_QUBO_opt_jo_higher_vars(lst):
        """
        Method for creating the QUBO model.

        Parameter:
        lst : a list of join order variables.
        
        """

        # Forming the power set and removing the single relations and the empty set
        #relations_sublists = QUBO_formulation.relation_sublists(relations)

        # Number of relation combinations
        n = len(lst)

        # S_1
        s_1_helper = lst 
        
        # S_2
        s_2_helper = []
        for i in range(n):
            for j in range(i,n):
                if (i != j):
                    if(set(lst[i]).intersection(set(lst[j]))):
                        if(len(lst[i]) <= len(lst[j])):
                            if(not set(lst[i]).issubset(set(lst[j]))):
                                s_2_helper.append([i,j])
                                
        return s_1_helper, s_2_helper, n
    
    def construct_qubo_for_inner_split(lst,l1,l2):
        '''
        this function is defined for realizing the contraints for the qubo formulation
        this formulation is specially defined to solve the inner split of a search space.
        e.g. n = (m+p)+1+1...+1    where m & p < n
        Parameter:
        lst: list of variables containing total cost element as well as single cost
        we also need to define the number of variables with total cost.
        l1 : number of total cost varibale that is m.
        l2 : number of total cost varibale that is p.
        '''
        l3 = l1 + l2
        n = len(lst)
        
        # S_1
        s_1_helper = lst

        # S_2
        s_2_helper = []
        for i in range(n):
            for j in range(i,n):
                if(i!=j):
                    if(set(lst[i]).intersection(set(lst[j]))):
                        if(len(lst[i]) <= len(lst[j])):
                            if(not set(lst[i]).issubset(set(lst[j]))):
                                s_2_helper.append([i,j])
        # S_3
        s_3_helper = []
        for i in range(l1):
            for j in range(l1,l3):
                if(not set(lst[i]).isdisjoint(set(lst[j]))):
                    s_3_helper.append([i,j])
                    
        # S_3_adding more constraints
        for i in range(l1):
            for j in range(i,l1):
                if(i!=j):
                    if(set(lst[i]).isdisjoint(set(lst[j]))):
                        s_3_helper.append([i,j])

        return s_1_helper, s_2_helper, s_3_helper, n


class Solvers_qiskit:
    """
    The Solvers class is used to solve the modeled QUBO problem.
    """
    shots = 1000

    def prepare_model(s_1_helper, s_2_helper, n, weights):
        """
        Method for generating the QUBO problem.

        Parameter:
        s_1_helper: List of relation combinations
        s_2_helper: Index structure of the constraints S_2
        s_3_helper: Index structure of the constraints S_3
        s_4_helper: Index structure of the constraints S_4
        n: Number of relation combinations
        weights: list of weights
        """
        # Initialization of the QUBO model
        mdl = Model(name='Join Ordering')

        # Definition of the binary random variable
        p = [mdl.binary_var() for i in range(0, n)]

        w_max = max(weights) * 2

        # Setting up the Hamilton formula
        s_1 = mdl.sum(p[i] * (weights[i] - w_max) for i in range(0, len(s_1_helper)))
        s_2 = mdl.sum(w_max * p[s_2_helper[i][0]] * p[s_2_helper[i][1]] for i in range(0, len(s_2_helper)))
        # s_3 = mdl.sum(w_max * p[s_3_helper[i][0]] * p[s_3_helper[i][1]] for i in range(0, len(s_3_helper)))
        objective = s_1 + s_2

        # Setting the goal of optimization
        mdl.minimize(objective)
        quadratic_program = from_docplex_mp(mdl)

        return quadratic_program


    def prepare_model_with_s3(s_1_helper, s_2_helper, s_3_helper, n, weights):

        w_max = max(weights) * 2

        # Initialization of the QUBO model
        mdl = Model(name='Join Ordering')

        # Definition of the binary random variable
        p = [mdl.binary_var() for i in range(0, n)]

        # Setting up the Hamilton formula
        s_1 = mdl.sum(p[i] * (weights[i] - w_max) for i in range(0, len(s_1_helper)))
        s_2 = mdl.sum(w_max * p[s_2_helper[i][0]] * p[s_2_helper[i][1]] for i in range(0, len(s_2_helper)))
        s_3 = mdl.sum(w_max * p[s_3_helper[i][0]] * p[s_3_helper[i][1]] for i in range(0, len(s_3_helper)))
        objective = s_1 + s_2 + s_3
        
        # Setting the goal of optimization
        mdl.minimize(objective)
        quadratic_program = from_docplex_mp(mdl)

        return quadratic_program

    # Calculation of the exact result
    def exact_result(quadratic_program, local_optimizer):
        """
        Method for exactly calculating an optimal join order.

        Parameter:
        quadratic_program: Quadratic Programm, on which to run the optimization algorithm.
        """
        exact_mes = NumPyMinimumEigensolver()
        exact = MinimumEigenOptimizer(exact_mes)
        results_exact = exact.solve(quadratic_program)
        return results_exact
    
    def sampling_vqe_sim(quadratic_program, local_optimizer):
        """
        Method for simulating a quantum computer using the VQE algorithm.

        Parameter:
        quadratic_program: Quadratic Programm, on which to run the optimization algorithm.
        """
        iterations = 125
        random.seed(10)
        if(local_optimizer == 'cobyla'):
            optimizer = COBYLA(maxiter=iterations)
        if(local_optimizer == 'spsa'):
            optimizer = SPSA(maxiter=iterations)
        operator, offset = QuadraticProgramToQubo().convert(quadratic_program).to_ising()
        ansatz = TwoLocal(operator.num_qubits,rotation_blocks="ry",entanglement_blocks="cz",reps=2, entanglement="linear")
        quantum_method_vqe = SamplingVQE(sampler=Sampler(),ansatz=ansatz,optimizer = optimizer)
        min_eigen_optimizer_vqe = MinimumEigenOptimizer(min_eigen_solver = quantum_method_vqe)
        results_vqe = min_eigen_optimizer_vqe.solve(quadratic_program)
        return results_vqe
    
    # Simulation of the VQE algorithm
    def vqe_sim(quadratic_program, local_optimizer):
        """
        Method for simulating a quantum computer using the VQE algorithm.

        Parameter:
        quadratic_program: Quadratic Programm, on which to run the optimization algorithm.
        """
        if(local_optimizer == 'cobyla'):
            optimizer = COBYLA(maxiter=10000)
        if(local_optimizer == 'spsa'):
            optimizer = SPSA(maxiter=10000)
        quantum_instance_vqe = QuantumInstance(backend = Aer.get_backend('qasm_simulator'), shots=Solvers_qiskit.shots)
        quantum_method_vqe = VQE(quantum_instance = quantum_instance_vqe, optimizer = optimizer)
        min_eigen_optimizer_vqe = MinimumEigenOptimizer(min_eigen_solver = quantum_method_vqe)
        results_vqe = min_eigen_optimizer_vqe.solve(quadratic_program)
        return results_vqe
    
    # Simulation of the QAOA algorithm
    def qaoa_sim(quadratic_program, local_optimizer):
        """
        Method for simulating a quantum computer using the QAOA algorithm.

        Parameter:
        quadratic_program: Quadratic Programm, on which to run the optimization algorithm.
        """
        random.seed(10)
        if(local_optimizer == 'cobyla'):
            optimizer = COBYLA(maxiter=125)
        if(local_optimizer == 'spsa'):
            optimizer = SPSA(maxiter=125)
        if(local_optimizer=='slsqp'):
            optimizer = SLSQP(maxiter=125)
        #operator, offset = QuadraticProgramToQubo().convert(quadratic_program).to_ising()
        qaoa_mes = QAOA(sampler=Sampler(), reps=2, optimizer = optimizer)
        qaoa_meo = MinimumEigenOptimizer(min_eigen_solver = qaoa_mes)
        results_qaoa = qaoa_meo.solve(quadratic_program)
        return results_qaoa
    
    def vqe_circuit_sim(quadratic_program, local_optimizer):
        """
        Another way to simulate a quantum computer using the VQE algorithm with a defined quantum circuit
        Parameter:
        quadratic_program: Quadratic Programm, on which to run the optimization algorithm.
        """
        if(local_optimizer == 'cobyla'):
            optimizer = COBYLA(maxiter=10000)
        if(local_optimizer == 'spsa'):
            optimizer = SPSA(maxiter=10000)
        operator, offset = QuadraticProgramToQubo().convert(quadratic_program).to_ising()
        ESU2_circuit = EfficientSU2(num_qubits = operator.num_qubits, entanglement = 'linear', insert_barriers = True, reps = 1)
        initial_point = np.random.random(ESU2_circuit.num_parameters)

        intermediate_info = {
            'nfev': [],
            'parameters': [],
            'energy': [],
            'stddev': []
        }

        local_vqe = VQE(ansatz=ESU2_circuit,
                optimizer=optimizer,
                initial_point=initial_point,
                quantum_instance=QasmSimulatorPy(),
                callback=Solvers_qiskit.callback)

        results_sim = local_vqe.compute_minimum_eigenvalue(operator)

        #print('Eigenvalue:', results_sim.eigenvalue)
        #print('Eigenstate:', results_sim.eigenstate)
        #print('Mean error:', np.mean(intermediate_info['stddev']))

        return results_sim

    def vqe_quantencomputer(quadratic_program, local_optimizer):
        """
        Method to run the algorithm on a quantum computer using VQE algorithm.

        Parameter:
        quadratic_program: Quadratic program on which to run the optimization algorithm.
        """
        IBMQ.save_account('f5655ec72023acc0fb3856b99b598384bc3347503df4fb495411d0c2d66e618811ba84df4cb02ad0ea4ce3e7a2b6c72ac84dc48c8735dcefa879c427bacb14bb', overwrite=True)
        IBMQ.load_account()
        
        provider = IBMQ.get_provider(hub = 'ibm-q', group = 'open', project = 'main')
        backend = provider.get_backend('ibm_nairobi')

        if(local_optimizer == 'cobyla'):
            optimizer = COBYLA(maxiter=10000)
        if(local_optimizer == 'spsa'):
            optimizer = SPSA(maxiter=10000)
        operator, offset = QuadraticProgramToQubo().convert(quadratic_program).to_ising()
        ESU2_circuit = EfficientSU2(num_qubits = operator.num_qubits, entanglement = 'full', insert_barriers = True, reps = 1)
        initial_point = np.random.random(ESU2_circuit.num_parameters)

        runtime_vqe = VQEClient(ansatz=ESU2_circuit,
                         optimizer=optimizer,
                         initial_point=initial_point,
                         provider=provider,
                         backend=backend,
                         shots=100)
        runtime_result = runtime_vqe.compute_minimum_eigenvalue(operator)
        

        return runtime_result

    def qaoa_quantencomputer(quadratic_program, local_optimizer):
        """
        Method to run the algorithm on a quantum computer using VQE algorithm.

        Parameter:
        quadratic_program: Quadratic program on which to run the optimization algorithm.
        """
        IBMQ.save_account('f5655ec72023acc0fb3856b99b598384bc3347503df4fb495411d0c2d66e618811ba84df4cb02ad0ea4ce3e7a2b6c72ac84dc48c8735dcefa879c427bacb14bb', overwrite=True)
        IBMQ.load_account()
        
        provider = IBMQ.get_provider(hub = 'ibm-q', group = 'open', project = 'main')
        backend = provider.get_backend('ibm_nairobi')

        if(local_optimizer == 'cobyla'):
            optimizer = COBYLA(maxiter=10000)
        if(local_optimizer == 'spsa'):
            optimizer = SPSA(maxiter=10000)
        operator, offset = QuadraticProgramToQubo().convert(quadratic_program).to_ising()

        runtime_qaoa = QAOAClient(optimizer=optimizer,
                         provider=provider,
                         backend=backend,
                         shots=Solvers_qiskit.shots,
                         callback=Solvers_qiskit.callback,
                         optimization_level=3)
        
        meo_qaoa = MinimumEigenOptimizer(min_eigen_solver = runtime_qaoa)
        runtime_result= meo_qaoa.solve(operator)
        return runtime_result

    def callback(nfev, parameters, energy, stddev):
        """
        Helper method for returning values.

        Parameter:
        nfev: The number of executions.
        parameters: The parameters with which the algorithm is run in each iteration
        energy: The intermediate result of the objective function.
        stddev: The standard deviation.
        """
        intermediate_info = {
            'nfev': [],
            'parameters': [],
            'energy': [],
            'stddev': []
        }

        intermediate_info['nfev'].append(nfev)
        intermediate_info['parameters'].append(parameters)
        intermediate_info['energy'].append(energy)
        intermediate_info['stddev'].append(stddev)
# ================================================================================================= #


# In[5]:


# ================================================================================================= #
# -----------------------------------Solution Algorithms - D-Wave---------------------------------- #
# ================================================================================================= #


class Solvers_dwave:
    """
    The Solvers_dwave class is used to solve the modeled QUBO problem on D-Wave quantum computers.
    """
    def prepare_model(s_1_helper, s_2_helper, n, weights_lst):

        w_max = max(weights_lst) * 2

        constrained_quadratic_model = ConstrainedQuadraticModel() # initialize the quadratic model.
        objective = BinaryQuadraticModel(vartype='BINARY') # initialize the objective.

        for i in range(n):
            objective.add_variable(i)

        # S_1
        for i in range(0, len(s_1_helper)):
            objective.set_linear(i, (weights_lst[i] - w_max))
        
        # S_2
        for i in range(0, len(s_2_helper)):
            objective.set_quadratic(s_2_helper[i][0], s_2_helper[i][1], + w_max)
            
        constrained_quadratic_model.set_objective(objective)
        
        #print(objective)

        return constrained_quadratic_model
    
    def prepare_model_with_s3(s_1_helper, s_2_helper, s_3_helper, n, weights_lst):

        w_max = max(weights_lst) * 2

        constrained_quadratic_model = ConstrainedQuadraticModel() # initialize the quadratic model.
        objective = BinaryQuadraticModel(vartype='BINARY') # initialize the objective.

        for i in range(n):
            objective.add_variable(i)

        # S_1
        for i in range(0, len(s_1_helper)):
            objective.set_linear(i, (weights_lst[i] - w_max))
        
        # S_2
        for i in range(0, len(s_2_helper)):
            objective.set_quadratic(s_2_helper[i][0], s_2_helper[i][1], + w_max)
            
        # S_3
        for i in range(0, len(s_3_helper)):
            objective.set_quadratic(s_3_helper[i][0], s_3_helper[i][1], + w_max)
            
        constrained_quadratic_model.set_objective(objective)
        
        #print(objective)

        return constrained_quadratic_model

    
    def exact_result(constrained_quadratic_model):
        """
        Method for exactly calculating an optimal join order.

        Parameter:
        quadratic_program: Quadratic program on which to run the optimization algorithm.
        """
        binary_quadratic_model, invert = dimod.cqm_to_bqm(constrained_quadratic_model)
        result = dimod.ExactSolver().sample(binary_quadratic_model)
        return result

    def simulated_annealing(constrained_quadratic_model):
        """
        Method for calculating an optimal join order using simulated annealing.

        Parameter:
        quadratic_program: Quadratic program on which to run the optimization algorithm.
        """
        #algorithm_globals.random_seed = 1234
        binary_quadratic_model, invert = dimod.cqm_to_bqm(constrained_quadratic_model)
        result = SimulatedAnnealingSampler().sample(binary_quadratic_model, num_reads=10)
        return result
    
    def dwave_sampler(constrained_quadratic_model):
        """
        Method for calculating an optimal join order using D-Wave QPU.

        Parameter:
        quadratic_program: Quadratic program on which to run the optimization algorithm.
        """
        endpoint = 'https://cloud.dwavesys.com/sapi'
        token = 'DEV-5ebbbf87b61f5e75519357a172f93d7365bc88a4'
        
        #solver = 'DW_2000Q_6'
        solver = 'Advantage_system4.1'

        binary_quadratic_model, invert = dimod.cqm_to_bqm(constrained_quadratic_model)
        dw = DWaveSampler(endpoint=endpoint, token=token, solver=solver)
        sampler = EmbeddingComposite(dw)
        #sampler = EmbeddingComposite(DWaveSampler(endpoint=endpoint, token=token, solver={'topology__type': 'zephyr'}))
        #sampler = EmbeddingComposite(DWaveSampler(endpoint=endpoint, token=token, solver={'topology__type': 'pegasus'}))

        result = sampler.sample(binary_quadratic_model, num_reads=1000)

        return result


class Helping_functions:
    """
    This class contains helper functions for the experimental execution of the QUBO algorithm.
    """
    def init_weights(relations):
        """
        Helper method for initializing random join costs.

        Parameter:
        relations: A list of relations.
        """
        powerset = sum([list(map(list, combinations(relations, i))) for i in range(len(relations) + 1)], [])
        return [random.randint(1,100) for _ in range(len(powerset)-(len(relations) + 1))]
    def print_relations_and_weights(relations, weights):
        """
        Auxiliary method for visualizing all possible relation combinations and their weights.

        Parameter:
        relations: A list of relations.
        weights: Cost of each join.
        """
        file = open("Qiskit-Tests.txt", "a", encoding='utf-8')
        relation_combinations = QUBO_formulation.relation_sublists(relations)
        # Overview of all sets and their weights
        for i in range (len(relation_combinations)):
            #print('Variable:-', i, ' (weight:-', weights[i], ') -> ', list(relation_combinations[i]),sep="")
            file.write('\n')
            file.write('Variable ')
            file.write(str(i))
            file.write(' (weight: ')
            file.write(str(weights[i]))
            file.write(') -> ')
            file.write(str(list(relation_combinations[i])))
        file.write('\n')
        file.close()


    def dynamic_programming(relations, cost):
        t = {}
        list1 = QUBO_formulation.relation_sublists(relations)
        list2 = QUBO_formulation.vars_with_joins(relations)
        variables_ae, weights_ae = QUBO_formulation.Elimination_vars_weights(list1, list2, cost)
        #relations_sublists = QUBO_formulation.relation_sublists(relations)
        sets = [frozenset([e]) for e in relations]
        #sets += [frozenset(e) for e in relations_sublists]
        sets += [frozenset(e) for e in variables_ae]
        for e in relations:
            t[frozenset([e])] = (e,0)
        n=len(relations)
        for i, S in enumerate(variables_ae):
            #if(len(S)==s):
            #while(len(S)==s):
                values = []
                for (a,b) in itertools.combinations(sets,2):
                    if a.isdisjoint(b) and a.union(b)==frozenset(S):
                        values.append(([t[a][0],t[b][0]], t[a][1] + t[b][1] + weights_ae[i]))
                t[frozenset(S)] = (min(values, key=lambda e: e[1]))
        #s+=1
        return t[frozenset(relations)]
    
    def dynamic_programming_wo_ecp(relations, weights):
        t = {}
        relations_sublists = QUBO_formulation.relation_sublists(relations)
        sets = [frozenset([e]) for e in relations]
        sets += [frozenset(e) for e in relations_sublists]
        for e in relations:
            t[frozenset([e])] = (e,0)
        n=len(relations)
        for i, S in enumerate(relations_sublists):
            #if(len(S)==s):
            #while(len(S)==s):
                values = []
                for (a,b) in itertools.combinations(sets,2):
                    if a.isdisjoint(b) and a.union(b)==frozenset(S):
                        values.append(([t[a][0],t[b][0]], t[a][1] + t[b][1] + weights[i]))
                t[frozenset(S)] = (min(values, key=lambda e: e[1]))
        #s+=1
        return t[frozenset(relations)]
    
    
    def make_join_order_tree(possible_state, vars_list,relations):
        state_vars = list()
        if len(possible_state) != len(vars_list):
            last_var = vars_list[-1]
            vars_list = vars_list[:-1]
            for i in range(len(possible_state)):
                if possible_state[i]==1:
                    state_vars.append(vars_list[i])
            state_vars.append(last_var)
        else: 
            for i in range(len(possible_state)):
                if possible_state[i]==1:
                    state_vars.append(vars_list[i])
        forest = {}
        for r in relations:
            forest[frozenset([r])] = [r]
        for v in state_vars:
            for [left, right] in itertools.combinations(forest,2):
                # left and right have to be disjoint and together form the set v
                if left.isdisjoint(right) and left.union(right) == set(v):
                    # remove single element list [a]+[b]==[a,b]!=[[a],[b]]
                    leftValue = forest[left][0] if len(left)==1 else forest[left]
                    rightValue = forest[right][0] if len(right)==1 else forest[right]
                    # add new tree to forest
                    forest[frozenset(v)]= [leftValue, rightValue]
                    # remove used trees
                    forest.pop(left)
                    forest.pop(right)
        if len(forest)==1:
            return forest.popitem()[1], state_vars, None
        else: 
            return [] , vars_list, "More than one tree remained at the end"
        
        
    @staticmethod
    def separate_variables(op_vars_list, all_vars, cost_list, length):
        temp = [var for var in op_vars_list if len(var) == length]
        temp_1 = [var for var in op_vars_list if set(var).issubset(set(temp[0]))]
        for var in temp_1:
            op_vars_list.remove(var)
        cost_1 = sum(cost_list[all_vars.index(var)] for var in op_vars_list)
        cost_2 = sum(cost_list[all_vars.index(var)] for var in temp_1)
        op_vars_list.append(cost_1)
        temp_1.append(cost_2)
        return op_vars_list, temp_1
    
    
    def single_cost_var(vars_list, weight_assigned, num_relns):
        '''
        This function is to extract the variables from power
        set P for a specified number of relations  with their respective weights.
        '''
        var_list = [var for var in vars_list if len(var) in num_relns]
        cost_list = [weight_assigned[vars_list.index(var)] for var in var_list]
        return var_list, cost_list
    
    def quboToTree(result, lst, relations):
        #relation_combinations = QUBO_formulation.relation_sublists(relations)
        vars=list()
        for i in range(len(result)):
            if result[i]==1:
                vars.append(lst[i])
        if len(vars)!=len(relations)-1:
            return [], vars, "Wrong number of joins. Should be {} but {} found.".format(len(relations)-1,len(vars))
        forest = {}
        for r in relations:
            forest[frozenset([r])] = [r]
        for v in vars:
            for [left, right] in itertools.combinations(forest,2):
                # left and right have to be disjoint and together form the set v
                if left.isdisjoint(right) and left.union(right)==set(v):
                    # remove single element list [a]+[b]==[a,b]!=[[a],[b]]
                    leftValue = forest[left][0] if len(left)==1 else forest[left]
                    rightValue = forest[right][0] if len(right)==1 else forest[right]
                    # add new tree to forest
                    forest[frozenset(v)]= [leftValue, rightValue]
                    # remove used trees
                    forest.pop(left)
                    forest.pop(right)
        if len(forest)==1:
            return forest.popitem()[1], vars, None
        else: 
            return [] , vars, "More than one tree remained at the end"
        
    def show_number_of_qubits_dwave(result):
        """
        Helper method to display the number of qubits used in embedding.

        Parameter:
        result: Result of the calculation of the D-Wave quantum computer.
        """
        embedding = result.info['embedding_context']['embedding']
        print(f"Number of logical variables: {len(embedding.keys())}")
        print(f"Number of physical qubits used in embedding: {sum(len(chain) for chain in embedding.values())}")

    def run_itr_bushy_trees(relations,elm_vars,l):
        k = len(relations)
        if k != 2*l:
            lst1 = [list(var) for var in combinations(relations,k-l)]
            lst2 = [list(var) for var in combinations(relations,l)]
            m = len(lst1) 
            temp_list = [[lst1[i],lst2[m-i-1]] for i in range(m)]
            temp_list = [itr for itr in temp_list if itr[0] not in elm_vars and itr[1] not in elm_vars]
        else:
            lst1 = [list(var) for var in combinations(relations,k-l)]
            lst2 = [list(var) for var in combinations(relations,l)]
            m = len(lst1) 
            temp_list = [[lst1[i],lst2[m-i-1]] for i in range(m)]
            temp_list = [itr for itr in temp_list if itr[0] not in elm_vars and itr[1] not in elm_vars]
            n = int(len(temp_list)/2)
            temp_list = temp_list[:n]
        return temp_list


class Experiments_class():
    '''
    Dwave experiment class
    '''
    def dwave_experiment(relations, weights, solver):
        """
        Method of making measurements in the D-Wave framework.

        Parameter:
        relations: A list of input relations.
        weights: Weights of all possible joins
        solver: The solver to use
        """
        a,b,c = QUBO_formulation.construct_QUBO(relations)
        constrained_quadratic_model = Solvers_dwave.prepare_model(a, b, c, weights)
        if solver == 'exact_result':
            result = Solvers_dwave.exact_result(constrained_quadratic_model)
        elif solver == 'dwave':
            result = Solvers_dwave.dwave_sampler(constrained_quadratic_model)
            #dwave.inspector.show(result)
            Helping_functions.show_number_of_qubits_dwave(result)
        elif solver == 'simulated_annealing':
            result = Solvers_dwave.simulated_annealing(constrained_quadratic_model)

        #file=Helping_functions.print_qubo_results_dwave(constrained_quadratic_model, relations, result)
        #Formatter(width=200).fprint(result)
        possible_outcome = result.lowest().record[0][0]
        relation_combinations = QUBO_formulation(relations).relation_sublists()
        optimized_jo_var = [relation_combinations[i] for i in range(len(possible_outcome)) if possible_outcome[i] == 1]
        total_cost = sum(weights[relation_combinations.index(var)] for var in optimized_jo_var)
        return result, total_cost, optimized_jo_var
    
    @staticmethod
    def dwave_experiment_opt_jo_by_vars_list(lst, cost, solver):
        """
        Method of making measurements in the D-Wave framework.

        Parameter:
        lst: A list of input variables.
        cost: cost of joins in the lst
        solver: The solver to use
        """
        #algorithm_globals.random_seed = 1234
        last_var = lst[-1]
        lst.pop()
        last_cost = cost[-1]
        cost.pop()
        a, b, c = QUBO_formulation.construct_QUBO_opt_jo_higher_vars(lst)
        constrained_quadratic_model = Solvers_dwave.prepare_model(a, b, c, cost)

        if solver == 'exact_result':
            result = Solvers_dwave.exact_result(constrained_quadratic_model)
        elif solver == 'dwave':
            result = Solvers_dwave.dwave_sampler(constrained_quadratic_model)
            #dwave.inspector.show(result)
            Helping_functions.show_number_of_qubits_dwave(result)
        elif solver == 'simulated_annealing':
            result = Solvers_dwave.simulated_annealing(constrained_quadratic_model)

        #file=Helping_functions.print_qubo_results_dwave(constrained_quadratic_model, relations, result)
        #Formatter(width=200).fprint(result)
        possible_outcome=result.lowest().record[0][0]
        optimized_jo_var = [lst[i] for i in range(len(possible_outcome)) if possible_outcome[i] == 1]
        optimized_jo_var.append(last_var)
        cost.append(last_cost)
        lst.append(last_var)
        total_cost = sum(cost[lst.index(var)] for var in optimized_jo_var)
        return result, total_cost, optimized_jo_var
    
    def dwave_experiment_inner_split_joo(lst, cost, l1, l2, solver):
        a,b,c,d = QUBO_formulation.construct_qubo_for_inner_split(lst,l1,l2)
        constrained_quadratic_model = Solvers_dwave.prepare_model_with_s3(a, b, c, d, cost)
        if solver == 'simulated_annealing':
            result = Solvers_dwave.simulated_annealing(constrained_quadratic_model)
        elif solver == 'dwave':
            result = Solvers_dwave.dwave_sampler(constrained_quadratic_model)
            Helping_functions.show_number_of_qubits_dwave(result)
        possible_outcome=result.lowest().record[0][0]
        optimized_jo_var = [lst[i] for i in range(len(possible_outcome)) if possible_outcome[i] == 1]
        total_cost = sum(cost[lst.index(var)] for var in optimized_jo_var)
        return result, total_cost, optimized_jo_var


    def qiskit_experiment(self, relations, weights,solver, local_optimizer):
        """
        Method for performing measurements in the Qiskit framework.

        Parameter:
        relations: A list of input relations.
        weights: Weights of all possible joins
        solver: The solver to use
        """

        # Generation and calculation of the QUBO:
        a,b,c,d,e = QUBO_formulation.construct_QUBO(relations, weights)
        new_weights_list = Helping_functions.get_new_weights_list(relations,weights)
        quadratic_program = Solvers_qiskit.prepare_model(a, b, c, d, e,new_weights_list)

        #Helping_functions.print_relations_and_weights(relations, weights)

        if(solver == 'exact_result'):
            result = Solvers_qiskit.exact_result(quadratic_program, local_optimizer).x
        if(solver == 'qaoa'):
            output_detail = Solvers_qiskit.qaoa_quantencomputer(quadratic_program, local_optimizer)
            result=[int(x) for x in list(dict(sorted(output_detail.eigenstate.items(), key=lambda item: item[1])).items())[-1][0]]
        if(solver == 'vqe'):
            output_detail = Solvers_qiskit.vqe_quantencomputer(quadratic_program, local_optimizer)
            result=[int(x) for x in list(dict(sorted(output_detail.eigenstate.items(), key=lambda item: item[1])).items())[-1][0]]
        if(solver == 'qaoa_sim'):
            result = Solvers_qiskit.qaoa_sim(quadratic_program, local_optimizer,).x
        if(solver == 'vqe_sim'):
            result = Solvers_qiskit.vqe_sim(quadratic_program, local_optimizer).x
        if(solver == 'vqe_circuit_sim'):
            output_detail = Solvers_qiskit.vqe_circuit_sim(quadratic_program, local_optimizer)
            result=[int(x) for x in list(dict(sorted(output_detail.eigenstate.items(), key=lambda item: item[1])).items())[-1][0]]
        if(solver == 'sampling_vqe_sim'):
            result= Solvers_qiskit.sampling_vqe_sim(quadratic_program, local_optimizer).x
        return Helping_functions.quboToTree(result, relations)

    
    def qiskit_experiment_for_list_vars(relations, lst, weights, solver, local_optimizer):
        """
        Method for performing measurements in the Qiskit framework.

        Parameter:
        relations: A list of input relations.
        weights: Weights of all possible joins
        solver: The solver to use
        """

        # Generation and calculation of the QUBO:
        a, b, c = QUBO_formulation.construct_QUBO_opt_jo_higher_vars(lst)
        quadratic_program = Solvers_qiskit.prepare_model(a, b, c, weights)

        #Helping_functions.print_relations_and_weights(relations, weights)

        if(solver == 'exact_result'):
            result = Solvers_qiskit.exact_result(quadratic_program, local_optimizer).x
        if(solver == 'qaoa'):
            output_detail = Solvers_qiskit.qaoa_quantencomputer(quadratic_program, local_optimizer)
            result=[int(x) for x in list(dict(sorted(output_detail.eigenstate.items(), key=lambda item: item[1])).items())[-1][0]]
        if(solver == 'vqe'):
            output_detail = Solvers_qiskit.vqe_quantencomputer(quadratic_program, local_optimizer)
            result=[int(x) for x in list(dict(sorted(output_detail.eigenstate.items(), key=lambda item: item[1])).items())[-1][0]]
        if(solver == 'qaoa_sim'):
            result = Solvers_qiskit.qaoa_sim(quadratic_program, local_optimizer,)
        if(solver == 'vqe_sim'):
            result = Solvers_qiskit.vqe_sim(quadratic_program, local_optimizer).x
        if(solver == 'vqe_circuit_sim'):
            output_detail = Solvers_qiskit.vqe_circuit_sim(quadratic_program, local_optimizer)
            result=[int(x) for x in list(dict(sorted(output_detail.eigenstate.items(), key=lambda item: item[1])).items())[-1][0]]
        if(solver == 'sampling_vqe_sim'):
            result = Solvers_qiskit.sampling_vqe_sim(quadratic_program, local_optimizer)
        order, optimized_jo_vars, error = Helping_functions.quboToTree(result.x, lst, relations)
        return result, order, optimized_jo_vars, error


class QUBO_Split_Optimization_func():

    def __init__(self, filename):
        self.logfile = open("servers/qubo/{}.log".format(filename),"w")

    def __del__(self):
        self.logfile.close()


    def logDwaveResult(self, result, relations, weights, vars_list, dp_optimal_cost, total_cost, count_info, solver, bit_info, dp_optimal_cost_wo_ecp):
        if solver == 'dwave':
            embedding = result.info['embedding_context']['embedding']
            lq = {len(embedding.keys())}
            pq = {sum(len(chain) for chain in embedding.values())}
            self.logfile.write("# {} ; {} ; {} ; {} ; {} ; {} ; {} ; {} ; {}\n".format(",".join(relations), str(lq), str(pq), str(count_info[0]), str(count_info[1]), str(count_info[2]), ",".join(str(e) for e in weights), str(total_cost), ','.join(str(e) for e in vars_list)))
        else:
            self.logfile.write("# {} ; {} ; {} ; {} ; {} ; {} ; {} ; {} ; {} ; {}\n".format(",".join(relations), str(bit_info), str(dp_optimal_cost), str(dp_optimal_cost_wo_ecp), str(count_info[0]), str(count_info[1]), str(count_info[2]), ",".join(str(e) for e in weights), str(total_cost), ','.join(str(e) for e in vars_list)))
        lowest_energy = result.aggregate().lowest().record[0][1]
        for r in result.aggregate().data():
            logData = [",".join(relations)]
            logData.append(r.num_occurrences)
            logData.append(r.energy)
            order, variables, error = Helping_functions.make_join_order_tree(r[0],vars_list, relations)
            logData.append("Valid" if error == None else "Invalid")
            logData.append("Optimal" if total_cost == dp_optimal_cost and r.energy == lowest_energy else "Not Optimal")
            logData.append(order)
            logData.append(variables)
            self.logfile.write(";".join([str(e) for e in logData]))
            self.logfile.write("\n")
            self.logfile.flush()

    '''
    This function is to get the optimal solutions of a particular length
    from given query using the input weights.
    '''
    @staticmethod
    def fixed_length_var_optimal_sol(relations,weights,length,solver):
        relation_combinations = QUBO_formulation.relation_sublists(relations)
        rel_comb=[list(lst) for lst in combinations(relations,length)]
        total_cost_list=[]
        optimal_rel_list=[]
        optimal_variables=[]
        for rel in rel_comb:
            new_rel_vars_list=QUBO_formulation.relation_sublists(rel)
            new_weights=[]
            for var in new_rel_vars_list:
                new_weights.append(weights[relation_combinations.index(var)])
            a,b,c = Experiments_class.dwave_experiment(rel,new_weights, solver)
            optimal_variables.append(c)
            optimal_rel_list.append(c[-1])
            total_cost_list.append(b)
        return optimal_variables, optimal_rel_list, total_cost_list
    
    @staticmethod
    def joo_by_split_SS_outer_Bushy(relations, variables_ae, weights_ae, length, solver, elm_vars):
        
        '''
        This function is defined to find the JO by splitting the splitted search space further.
        we don't use the dynamic programming but the only quantum annealing and simulated annealing.
        This function can be used for the outer bushy trees.
        '''
        store_jo_details = {}
        temp_1 = []
        temp_2 = []
        cost_1 = []
        cost_2 = []
        store_final_vars = []
        store_total_cost = []
        JO_details = []
        exp_r = 0
        rel_comb = Helping_functions.run_itr_bushy_trees(relations,elm_vars,length)
        if len(rel_comb) == 0:
            return [], [], [], [], 0
        else:
            for rel in rel_comb:
                temp_lst = QUBO_formulation.relation_sublists(rel[0])
                new_rel_vars_list = [var for var in temp_lst if var in variables_ae]
                l = len(rel[0])
                temp_lst_2 = QUBO_formulation.relation_sublists(rel[1])
                new_rel_vars_list_remaining = [var for var in temp_lst_2 if var in variables_ae]
                new_list = new_rel_vars_list + new_rel_vars_list_remaining + [relations]
                new_weights = [weights_ae[variables_ae.index(var)] for var in new_list]
                if len(new_list) < len(relations) - 2:
                    continue
                result, total_cost, JO_vars = Experiments_class.dwave_experiment_opt_jo_by_vars_list(new_list, new_weights, solver)
                JO_details.append([total_cost, JO_vars, result, new_weights, new_list])
                JO_vars_copy = JO_vars.copy()
                temp_3 = []
                for var in JO_vars_copy:
                    if len(var)==length:
                        temp_3.append(var)
                if len(temp_3) == 0:
                    continue
                lst1,lst2 = Helping_functions.separate_variables(JO_vars, new_list, new_weights, length)
                if(l>2):
                    store_jo_details[frozenset(lst1[-2])] = lst1
                    store_jo_details[frozenset(lst2[-2])] = lst2
                    temp_1.append(lst1[-2])
                    cost_1.append(lst1[-1])
                    temp_2.append(lst2[-2])
                    cost_2.append(lst2[-1])
                else:
                    store_jo_details[frozenset(lst2[-2])] = lst2
                    temp_2.append(lst2[-2])
                    cost_2.append(lst2[-1])
            exp_r = len(JO_details)
            JO_details = min(JO_details, key = lambda e : e[0])
            if(len(temp_1)!=0):
                store_final_vars.append(temp_1)
                store_final_vars.append(temp_2)
                store_total_cost.append(cost_1)
                store_total_cost.append(cost_2)
            else:
                store_final_vars += temp_2
                store_total_cost += cost_2
        return  JO_details, store_jo_details, store_final_vars, store_total_cost, exp_r


    @staticmethod
    def findind_LR_deep_jo(vars_J2R, All_vars, weights, solver):
        '''
        This function is defined for the left and right deep join tree.
        '''
        #relation_combinations = QUBO_formulation.relation_sublists(relations)
        #rel_comb=[list(lst) for lst in combinations(relations, 2)]
        optimal_jo_details = []  # to store the optimal join order details
        for rel in vars_J2R:
            vars_list = []
            cost_list = []
            for i, elem in enumerate(All_vars):
                if(set(rel).issubset(set(elem))):
                    vars_list.append(elem)
                    cost_list.append(weights[i])  
            result, total_cost, optimized_jo_vars = Experiments_class.dwave_experiment_opt_jo_by_vars_list(vars_list, cost_list, solver)
            optimal_jo_details.append([total_cost, optimized_jo_vars, result, cost_list, vars_list])
        exp_run = len(optimal_jo_details) # to store the number of experiments run
        optimal_jo_details = min(optimal_jo_details, key = lambda e:e[0])
        return optimal_jo_details, exp_run
    
    @staticmethod
    def special_function_inner_split(vars_J2R, All_vars, cost, solver):
        '''
        this function is defined to find the join order for the split
        like n = m(t)+1+1+1 where m(t) is the total cost upto m and here m<n.
        Parameters:
        vars_J2R = variables of m(t)
        All_vars = all variable upto n
        cost = cost corresponding to the all_vars
        '''
        possible_jo_details = []
        for var_1 in vars_J2R:
            for var_2 in vars_J2R:
                if(set(var_1).isdisjoint(set(var_2))):
                    vars_list = []
                    cost_list = []
                    for i, elem in enumerate(All_vars):
                        if(set(var_1).issubset(set(elem)) or set(var_2).issubset(set(elem))):
                            vars_list.append(elem)
                            cost_list.append(cost[i])
                    result, total_cost, optimized_jo_vars = Experiments_class.dwave_experiment_opt_jo_by_vars_list(vars_list, cost_list, solver)
                    possible_jo_details.append([total_cost, optimized_jo_vars, result, cost_list, vars_list])
        exp_run = len(possible_jo_details)
        optimal_jo_details = (min(possible_jo_details, key = lambda e:e[0]))
        return optimal_jo_details, exp_run
    
    @staticmethod
    def reduce_contraints_for_disjoint_inner_join(lst, cost, l1, l2, solver):
        l3 = l1 + l2
        sub_lst = lst[0:l1]
        opt_details = []
        n = len(lst)
        for i in sub_lst:
            lst2 = []
            new_list = []
            new_cost_lst = []
            dis_vars = []
            dis_vars = [lst[j] for j in range(l1, l3) if set(i).isdisjoint(set(lst[j]))]
            lst2 = [lst[j] for j in range(l3, n) if set(i).issubset(set(lst[j]))]
            new_list.append(i)
            new_list += dis_vars
            new_list += lst2
            new_cost_lst = [cost[lst.index(var)] for var in new_list]
            l2 = len(dis_vars)
            result, total_cost, optimized_jo_vars = Experiments_class.dwave_experiment_inner_split_joo(new_list, new_cost_lst, 1, l2, solver)
            opt_details.append([total_cost, optimized_jo_vars, result, new_cost_lst, new_list])
        exp_run = len(opt_details)
        opt_detail = (min(opt_details, key = lambda e : e[0]))
        return opt_detail, exp_run
    
    
    def finding_opt_jo(self, relations, weights, solver):
        
        '''
        This definition has been enabled to find the optimal join order for relations 4,5,6,7 and 8.
        '''
        
        optimal_jo_details = []
        n = len(relations)
        dp_opt_jo_cost = Helping_functions.dynamic_programming(relations, weights)
        dp_optimal_cost = dp_opt_jo_cost[1]
        dp_opt_jo_cost_wo_ecp = Helping_functions.dynamic_programming_wo_ecp(relations, weights)
        dp_optimal_cost_wo_ecp = dp_opt_jo_cost_wo_ecp[1]
        changed = 0
        if dp_optimal_cost != dp_optimal_cost_wo_ecp:
            changed = 1
        print('changed:',changed)
        print('dp_opt_jo_n_cost',dp_opt_jo_cost)
        print('dp_opt_jo_n_cost_wo_ecp',dp_opt_jo_cost_wo_ecp)

        # defining variables and their cost after eliminating cartisian product
        power_set = QUBO_formulation.relation_sublists(relations)
        #print('total number of variables in power set:',len(power_set))
        #print('total number of variables in power set:',power_set)
        list2 = QUBO_formulation.vars_with_joins(relations)
        variables_ae, weights_ae = QUBO_formulation.Elimination_vars_weights(power_set, list2, weights)
        #print('total number of variables after eliminating cartisian product:',len(variables_ae))
        eliminated_vars = [x for x in power_set if x not in variables_ae]
        #print('total number of variables after eliminating cartisian product:',variables_ae)
        vars_2, cost_2 = Helping_functions.single_cost_var(variables_ae, weights_ae, [2])
        All_vars_2, All_cost_2 = Helping_functions.single_cost_var(power_set, weights, [2])
        c_join_relations = [x for x in All_vars_2 if x not in vars_2]
        #print('cross joins for relations in this query are:',c_join_relations)
        #print('Number of relations with cross joins:', len(c_join_relations))
        #print(f'variable_ae:{variables_ae} & length:{len(variables_ae)}')
        #print(f'weights_ae:{weights_ae} & length:{len(weights_ae)}')

        '''
        Solving for the 3 relations query.
        '''
        if n == 3:
        #Split -> 1, checking for left and right deep join tree
            count = 1
            optimal_jo, exp_run = QUBO_Split_Optimization_func.findind_LR_deep_jo(vars_2, variables_ae, weights_ae, solver)
            if optimal_jo[0] == dp_optimal_cost:
                #print(f'Yes,found optimal JO for the l/r deep join tree & #variables:{len(optimal_jo[3])} and #exp:{exp_run}.')
                optimal_jo_details.append(optimal_jo)
            #else:
                #print(f'No,optimal JO not found for the l/r deep join tree & #variables:{len(optimal_jo[3])} and #exp:{exp_run}.')
            
            #print(f'# total exps run:{exp_run} & # splits:{count}.')
        
        '''
        Solving for the 4 relations query.
        '''
        if n == 4:
        #Split -> 1, checking for left and right deep join tree
            count = 1
            optimal_jo, exp_run = QUBO_Split_Optimization_func.findind_LR_deep_jo(vars_2, variables_ae, weights_ae, solver)
            if optimal_jo[0] == dp_optimal_cost:
                print(f'Yes,found optimal JO for the l/r deep join tree & #variables:{len(optimal_jo[3])} and #exp:{exp_run}.')
                optimal_jo_details.append(optimal_jo)
            else:
                print(f'No,optimal JO not found for the l/r deep join tree & #variables:{len(optimal_jo[3])} and #exp:{exp_run}.')

        #Split -> 2, checking for the split 2+2
            count += 1
            vars_4, cost_4 = Helping_functions.single_cost_var(variables_ae, weights_ae, [4])
            result, total_cost, optimized_jo_vars = Experiments_class.dwave_experiment_opt_jo_by_vars_list(vars_2 + vars_4, cost_2 + cost_4, solver)
            if total_cost == dp_optimal_cost:
                print(f'Yes,found optimal JO for split 2+2 & #variables:{len(vars_2 + vars_4)} and #exp:{1}.')
                optimal_jo_details.append([total_cost, optimized_jo_vars,result, cost_2 + cost_4,  vars_2 + vars_4])
            else:
                print(f'No,optimal JO not found for split 2+2 & #variables:{len(vars_2 + vars_4)} and #exp:{1}.')
            exp_run += 1

            print(f'# total exps run:{exp_run} & # splits:{count}.')

        '''
        Solving for the 5 relations query.
        '''
        if n == 5:
        #Split -> 1, checking for left and right deep join tree
            count = 1
            optimal_jo, exp_run = QUBO_Split_Optimization_func.findind_LR_deep_jo(vars_2, variables_ae, weights_ae, solver)
            if(optimal_jo[0] == dp_optimal_cost):
                print(f'Yes,found optimal JO for the l/r deep join tree & #variables:{len(optimal_jo[3])} & #exp:{exp_run}.')
                optimal_jo_details.append(optimal_jo)
            else:
                print(f'No,optimal JO not found for the l/r deep join tree & #variables:{len(optimal_jo[3])} & #exp:{exp_run}.')
            
        #Split -> 2, checking for the (4+1) as ((2+2)+1)
            count += 1
            vars_45, cost_45 = Helping_functions.single_cost_var(variables_ae, weights_ae, [4,5])
            result, total_cost, optimized_jo_vars = Experiments_class.dwave_experiment_opt_jo_by_vars_list(vars_2 + vars_45, cost_2 + cost_45, solver)
            if(total_cost == dp_optimal_cost):
                print(f'Yes,found optimal JO for split (4+1)->((2+2)+1) & #variables:{len(vars_2 + vars_45)} & #exp:{1}.')
                optimal_jo_details.append([total_cost, optimized_jo_vars, result, cost_2 + cost_45, vars_2 + vars_45])
            else:
                print(f'No,optimal JO not found for split (4+1)->((2+2)+1) & #variables:{len(vars_2 + vars_45)} & #exp:{1}.')
            exp_run += 1

        #Split -> 3, checking for the 3+2
            opt_detail, store_jo_details, store_final_vars, store_total_cost, exprun_s3 = QUBO_Split_Optimization_func.joo_by_split_SS_outer_Bushy(relations,variables_ae, weights_ae, 3, solver, eliminated_vars)
            if len(opt_detail) == 0:
                print('The search space of this split 3+2 is empty.')
            elif opt_detail[0] == dp_optimal_cost:
                count += 1
                print(f'Yes,found optimal JO for split 3+2 & #variables:{len(opt_detail[3])} and #exp:{exprun_s3}.')
                optimal_jo_details.append(opt_detail)
            elif opt_detail[0] != dp_optimal_cost:
                count += 1
                print(f'No,optimal JO not found for split 3+2 & #variables:{len(opt_detail[3])} & #exp:{exprun_s3}.') 

            exp_run += exprun_s3 
            print(f'# total exps run:{exp_run} and # splits:{count}.')

                
        '''
        Solving for the 6 relations query.
        '''
        if n == 6:
        # Split -> 1, checking for left/right deep join tree
            count = 1
            optimal_jo, exp_run = QUBO_Split_Optimization_func.findind_LR_deep_jo(vars_2, variables_ae, weights_ae, solver)
            if optimal_jo[0] == dp_optimal_cost:
                print(f'Yes,found optimal JO for the l/r deep join tree & #variables:{len(optimal_jo[3])} and #exp:{exp_run}.')
                optimal_jo_details.append(optimal_jo)
            else:
                print(f'No,optimal JO not found for the l/r deep join tree & #variables:{len(optimal_jo[3])} & #exp:{exp_run}.')
                
        # Split -> 2, checking for 4+2 Bushy tree
            opt_detail, store_jo_details, store_final_vars_4, store_total_cost_4, exprun_s2 = QUBO_Split_Optimization_func.joo_by_split_SS_outer_Bushy(relations, variables_ae, weights_ae, 4, solver, eliminated_vars)
            if len(opt_detail) == 0:
                print('The search space of this split 4+2 is empty.')
            elif opt_detail[0] == dp_optimal_cost:
                count += 1
                print(f'Yes,found optimal JO for split 4+2 & #variables:{len(opt_detail[3])} and #exp:{exprun_s2}.')
                optimal_jo_details.append(opt_detail)
            elif opt_detail[0] != dp_optimal_cost:
                count += 1
                print(f'No,optimal JO not found for split 4+2 & #variables:{len(opt_detail[3])} & #exp:{exprun_s2}.')
            exp_run += exprun_s2

        # Split -> 3, checking for (4+1)+1
            count += 1
            vars_56 , cost_56 = Helping_functions.single_cost_var(variables_ae, weights_ae, [5,6])
            result, total_cost, optimized_jo_vars = Experiments_class.dwave_experiment_opt_jo_by_vars_list(store_final_vars_4 + vars_56, store_total_cost_4 + cost_56, solver)
            if total_cost == dp_optimal_cost:
                print(f'Yes,found optimal JO for split (4+1)+1 & #variables{len(store_final_vars_4 + vars_56)} & #exp:{1}.')
                jo_vars = store_jo_details[frozenset(optimized_jo_vars[0])]
                jo_vars.pop()
                optimized_jo_vars.pop(0)
                optimized_jo_vars = jo_vars + optimized_jo_vars
                optimal_jo_details.append([total_cost, optimized_jo_vars, result, store_total_cost_4 + cost_56, store_final_vars_4 + vars_56])
            else:
                print(f'No,optimal JO not found for split (4+1)+1 & #variables{len(store_final_vars_4 + vars_56)} & #exp:{1}.')
            exp_run += 1
                
        # Split -> 4, checking for (3+3), (3+2)+1 and (2+2+2)
            count += 1
            vars_3 , cost_3 = Helping_functions.single_cost_var(variables_ae, weights_ae, [3])
            result, total_cost, optimized_jo_vars = Experiments_class.dwave_experiment_opt_jo_by_vars_list(vars_2 + vars_3 + vars_56, cost_2 + cost_3 + cost_56, solver)
            if total_cost == dp_optimal_cost:
                print(f'Yes,found optimal JO for split (3+2)+1,(2+2+2)&(3+3) & #variables:{len(vars_2 + vars_3 + vars_56)} & #exp:{1}.')
                optimal_jo_details.append([total_cost, optimized_jo_vars, result, cost_2 + cost_3 + cost_56, vars_2 + vars_3 + vars_56])
            else:
                print(f'No,optimal JO not found for split (3+2)+1,(2+2+2)&(3+3) & #variables:{len(vars_2 + vars_3 + vars_56)} & #exp:{1}.')
            exp_run += 1
            print(f'# total exps run:{exp_run} and #splits{count}.')


        '''
        Solving for the 7 relations query.
        '''
        if n == 7:
        # Split -> 1, checking for left/right deep join tree
            count = 1
            optimal_jo, exp_run = QUBO_Split_Optimization_func.findind_LR_deep_jo(vars_2, variables_ae, weights_ae, solver)
            if optimal_jo[0] == dp_optimal_cost:
                print(f'Yes,found optimal JO for the l/r deep join tree & #variables:{len(optimal_jo[3])} and #exp:{exp_run}.')
                optimal_jo_details.append(optimal_jo)
            else:
                print(f'No,optimal JO not found for the l/r deep join tree & #variables:{len(optimal_jo[3])} & #exp:{exp_run}.')
        # Split -> 2, checking for 5+2 Bushy tree
            opt_detail, store_jo_details, store_final_vars_5, store_total_cost_5, exprun_s2 = QUBO_Split_Optimization_func.joo_by_split_SS_outer_Bushy(relations, variables_ae, weights_ae, 5, solver, eliminated_vars)
            if len(opt_detail) == 0:
                print('The search space of this split 5+2 is empty.')
            elif opt_detail[0] == dp_optimal_cost:
                count += 1
                print(f'Yes,found optimal JO for split 5+2 & #variables:{len(opt_detail[3])} and #exp:{exprun_s2}.')
                optimal_jo_details.append(opt_detail)
            elif opt_detail[0] != dp_optimal_cost:
                count += 1
                print(f'No,optimal JO not found for split 5+2 & #variables:{len(opt_detail[3])} & #exp:{exprun_s2}.')
            exp_run += exprun_s2
        # Split -> 3, checking for (5(t)+1)+1
            count += 1
            vars_67 , cost_67 = Helping_functions.single_cost_var(variables_ae, weights_ae, [6,7])
            result, total_cost, optimized_jo_vars = Experiments_class.dwave_experiment_opt_jo_by_vars_list(store_final_vars_5 + vars_67, store_total_cost_5 + cost_67, solver)
            if total_cost == dp_optimal_cost:
                print(f'Yes,found optimal JO for split (5+1)+1 & #variables{len(store_final_vars_5 + vars_67)} & #exp:{1}.')
                jo_vars = store_jo_details[frozenset(optimized_jo_vars[0])]
                jo_vars.pop()
                optimized_jo_vars.pop(0)
                optimized_jo_vars = jo_vars + optimized_jo_vars
                optimal_jo_details.append([total_cost, optimized_jo_vars, result, store_total_cost_5 + cost_67, store_final_vars_5 + vars_67])
            else:
                print(f'No,optimal JO not found for split (5+1)+1 & #variables{len(store_final_vars_5 + vars_67)} & #exp:{1}.')
            exp_run += 1
        # Split -> 4, checking for 4+3 Bushy tree
            opt_detail, store_jo_details, store_final_vars_34, store_total_cost_34, exprun_s4 = QUBO_Split_Optimization_func.joo_by_split_SS_outer_Bushy(relations, variables_ae, weights_ae, 4, solver, eliminated_vars)
            if len(opt_detail) == 0:
                print('The search space of this split 4+3 is empty.')
            elif opt_detail[0] == dp_optimal_cost:
                count += 1
                print(f'Yes,found optimal JO for split 4+3 & #variables:{len(opt_detail[3])} and #exp:{exprun_s4}.')
                optimal_jo_details.append(opt_detail)
            elif opt_detail[0] != dp_optimal_cost:
                count += 1
                print(f'No,optimal JO not found for split 4+3 & #variables:{len(opt_detail[3])} & #exp:{exprun_s4}.')
            exp_run += exprun_s4
                
        # Split -> 5, checking for 4(t)+1+1+1
            count += 1
            vars_567 , cost_567 = Helping_functions.single_cost_var(variables_ae, weights_ae, [5,6,7])
            result, total_cost, optimized_jo_vars = Experiments_class.dwave_experiment_opt_jo_by_vars_list(store_final_vars_34[1] + vars_567, store_total_cost_34[1] + cost_567, solver)
            if total_cost == dp_optimal_cost:
                print(f'Yes,found optimal JO for split (4(t)+1)+1 & #variables{len(store_final_vars_34[1] + vars_567)} & #exp:{1}.')
                jo_vars = store_jo_details[frozenset(optimized_jo_vars[0])]
                jo_vars.pop()
                optimized_jo_vars.pop(0)
                optimized_jo_vars = jo_vars + optimized_jo_vars
                optimal_jo_details.append([total_cost, optimized_jo_vars, result, store_total_cost_34[1] + cost_567, store_final_vars_34[1] + vars_567])
            else:
                print(f'No,optimal JO not found for split (4(t)+1)+1 & #variables{len(store_final_vars_34[1] + vars_567)} & #exp:{1}.')
            exp_run += 1
                
        #Split -> 6, checking for (4+2)+1
            count += 1
            l1 = len(vars_2)
            l2 = len(store_final_vars_34[1])
            vars_67 , cost_67 = Helping_functions.single_cost_var(variables_ae, weights_ae, [6,7])
            result, total_cost, optimized_jo_vars = Experiments_class.dwave_experiment_inner_split_joo(vars_2 + store_final_vars_34[1] + vars_67, cost_2 + store_total_cost_34[1] + cost_67, l1, l2, solver)
            if total_cost == dp_optimal_cost:
                print(f'Yes,found optimal JO for split (4+2)+1 & #variables{len(vars_2 + store_final_vars_34[1] + vars_67)} & #exp:{1}.')
                jo_vars = store_jo_details[frozenset(optimized_jo_vars[1])]
                jo_vars.pop()
                optimized_jo_vars.pop(1)
                optimized_jo_vars = jo_vars + optimized_jo_vars
                optimal_jo_details.append([total_cost, optimized_jo_vars, result, cost_2 + store_total_cost_34[1] + cost_67, vars_2 + store_final_vars_34[1] + vars_67])
            else:
                print(f'No,optimal JO not found for split (4+2)+1 & #variables{len(vars_2 + store_final_vars_34[1] + vars_67)} & #exp:{1}.')
            exp_run += 1
                
        #Split -> 7, checking for (3+3)+1
            count += 1
            result, total_cost, optimized_jo_vars = Experiments_class.dwave_experiment_opt_jo_by_vars_list(store_final_vars_34[0] + vars_67, store_total_cost_34[0] + cost_67, solver)
            if total_cost == dp_optimal_cost:
                print(f'Yes,found optimal JO for split (3+3)+1 & #variables{len(store_final_vars_34[0] + vars_67)} & #exp:{1}.')
                jo_vars_1 = store_jo_details[frozenset(optimized_jo_vars[0])]
                jo_vars_1.pop()
                jo_vars_2 = store_jo_details[frozenset(optimized_jo_vars[1])]
                jo_vars_2.pop()
                optimized_jo_vars.pop(0)
                optimized_jo_vars.pop(0)
                optimized_jo_vars = jo_vars_1 + jo_vars_2 + optimized_jo_vars
                optimal_jo_details.append([total_cost, optimized_jo_vars, result, store_total_cost_34[0] + cost_67, store_final_vars_34[0] + vars_67])
            else:
                print(f'No,optimal JO not found for split (3+3)+1 & #variables{len(store_final_vars_34[0] + vars_67)} & #exp:{1}.')
            exp_run += 1
            print(f'# total exps run:{exp_run} and #splits{count}.')

        '''
        Solving for the 8 relations query.
        '''
        if n == 8: 
        #Split -> 1, checking for left/right deep join tree
            count = 1
            optimal_jo, exp_run = QUBO_Split_Optimization_func.findind_LR_deep_jo(vars_2, variables_ae, weights_ae, solver)
            if optimal_jo[0] == dp_optimal_cost:
                print(f'Yes,found optimal JO for the l/r deep join tree & #variables:{len(optimal_jo[3])} and #exp:{exp_run}.')
                optimal_jo_details.append(optimal_jo)
            else:
                print(f'No,optimal JO not found for the l/r deep join tree & #variables:{len(optimal_jo[3])} & #exp:{exp_run}.')  
        #Split -> 2, checking for 6+2 Bushy tree
            opt_detail, store_jo_details, store_final_vars_6, store_total_cost_6, exprun_s2 = QUBO_Split_Optimization_func.joo_by_split_SS_outer_Bushy(relations, variables_ae, weights_ae, 6, solver, eliminated_vars)
            if len(opt_detail) == 0:
                print('The search space of this split 6+2 is empty.')
            elif opt_detail[0] == dp_optimal_cost:
                count += 1
                print(f'Yes,found optimal JO for split 6+2 & #variables:{len(opt_detail[3])} and #exp:{exprun_s2}.')
                optimal_jo_details.append(opt_detail)
            elif opt_detail[0] != dp_optimal_cost:
                count += 1
                print(f'No,optimal JO not found for split 6+2 & #variables:{len(opt_detail[3])} & #exp:{exprun_s2}.')
            exp_run += exprun_s2 
        #Split -> 3, checking for (6(t)+1)+1
            count += 1
            vars_78 , cost_78 = Helping_functions.single_cost_var(variables_ae, weights_ae, [7,8])
            result, total_cost, optimized_jo_vars = Experiments_class.dwave_experiment_opt_jo_by_vars_list(store_final_vars_6 + vars_78, store_total_cost_6 + cost_78, solver)
            if total_cost == dp_optimal_cost:
                print(f'Yes,found optimal JO for split (6(t)+1)+1 & #variables{len(store_final_vars_6 + vars_78)} & #exp:{1}.')
                jo_vars = store_jo_details[frozenset(optimized_jo_vars[0])]
                jo_vars.pop()
                optimized_jo_vars.pop(0)
                optimized_jo_vars = jo_vars + optimized_jo_vars
                optimal_jo_details.append([total_cost, optimized_jo_vars, result, store_total_cost_6 + cost_78, store_final_vars_6 + vars_78])
            else:
                print(f'No,optimal JO not found for split (6(t)+1)+1 & #variables{len(store_final_vars_6 + vars_78)} & #exp:{1}.')
            exp_run += 1
        #Split -> 4, checking for 5+3 Bushy tree
            opt_detail, store_jo_details, store_final_vars_35, store_total_cost_35, exprun_s4 = QUBO_Split_Optimization_func.joo_by_split_SS_outer_Bushy(relations, variables_ae, weights_ae, 5, solver, eliminated_vars)
            if len(opt_detail) == 0:
                print('The search space of this split 5+3 is empty.')
            elif opt_detail[0] == dp_optimal_cost:
                count += 1
                print(f'Yes,found optimal JO for split 5+3 & #variables:{len(opt_detail[3])} and #exp:{exprun_s4}.')
                optimal_jo_details.append(opt_detail)
            elif opt_detail[0] != dp_optimal_cost:
                count += 1
                print(f'No,optimal JO not found for split 5+3 & #variables:{len(opt_detail[3])} & #exp:{exprun_s4}.')
            exp_run += exprun_s4
        #Split -> 5, checking for 5(t)+1+1+1
            count += 1
            vars_6 , cost_6 = Helping_functions.single_cost_var(variables_ae, weights_ae, [6])
            result, total_cost, optimized_jo_vars = Experiments_class.dwave_experiment_opt_jo_by_vars_list(store_final_vars_35[1] + vars_6 + vars_78, store_total_cost_35[1] + cost_6 + cost_78, solver)
            if total_cost == dp_optimal_cost:
                print(f'Yes,found optimal JO for split 5(t)+1+1+1 & #variables{len(store_final_vars_35[1] + vars_6 + vars_78)} & #exp:{1}.')
                jo_vars = store_jo_details[frozenset(optimized_jo_vars[0])]
                jo_vars.pop()
                optimized_jo_vars.pop(0)
                optimized_jo_vars = jo_vars + optimized_jo_vars
                optimal_jo_details.append([total_cost, optimized_jo_vars, result, store_total_cost_35[1] + cost_6 + cost_78, store_final_vars_35[1] + vars_6 + vars_78])
            else:
                print(f'No,optimal JO not found for split 5(t)+1+1+1 & #variables{len(store_final_vars_35[1] + vars_6 + vars_78)} & #exp:{1}.')
            exp_run += 1   
        #Split -> 6, checking for (5+2)+1 and (3+4)+1
            count += 1
            l1 = len(vars_2)
            l2 = len(store_final_vars_35[1])
            # print('vars_2:',vars_2)
            # print('store_final_vars_35[1]:',store_final_vars_35[1])
            # print('vars_78:',vars_78)
            # print('l1:',l1)
            # print('l2:',l2)
            res, exprun_s6 = QUBO_Split_Optimization_func.reduce_contraints_for_disjoint_inner_join(vars_2 + store_final_vars_35[1] + vars_78, cost_2 + store_total_cost_35[1] + cost_78, l1, l2, solver)
            #result, total_cost, optimized_jo_vars = Experiments_class.dwave_experiment_inner_split_joo(vars_2 + store_final_vars_35[1] + vars_7, cost_2 + store_total_cost_35[1] + cost_7, l1, l2, solver)
            if res[0] == dp_optimal_cost:
                print(f'Yes,found optimal JO for split (5+2)+1 and (3+4)+1 & #variables{len(res[4])} & #exp:{exprun_s6}.')
                jo_vars = store_jo_details[frozenset(res[1][1])]
                jo_vars.pop()
                res[1].pop(1)
                res[1] = jo_vars + res[1]
                optimal_jo_details.append(res)
            else:
                print(f'No,optimal JO not found for split (5+2)+1 and (3+4)+1 & #variables{len(res[4])} & #exp:{exprun_s6}.')
            exp_run += exprun_s6
        #Split -> 7, checking for 4+4 Bushy tree
            opt_detail, store_jo_details, store_final_vars_44, store_total_cost_44, exprun_s7 = QUBO_Split_Optimization_func.joo_by_split_SS_outer_Bushy(relations, variables_ae, weights_ae, 4, solver, eliminated_vars)
            if len(opt_detail) == 0:
                print('The search space of this split 4+4 is empty.')
            elif opt_detail[0] == dp_optimal_cost:
                count += 1
                print(f'Yes,found optimal JO for split 4+4 & #variables:{len(opt_detail[3])} and #exp:{exprun_s7}.')
                optimal_jo_details.append(opt_detail)
            elif opt_detail[0] != dp_optimal_cost:
                count += 1
                print(f'No,optimal JO not found for split 4+4 & #variables:{len(opt_detail[3])} & #exp:{exprun_s7}.')
            exp_run += exprun_s7          
        #Split -> 8, checking for 4(t)+1+1+1+1
            count += 1
            vars_5 , cost_5 = Helping_functions.single_cost_var(variables_ae, weights_ae, [5])
            vars_4t = store_final_vars_44[0] + store_final_vars_44[1]
            total_cost_4 = store_total_cost_44[0] + store_total_cost_44[1]
            optimal_jo, exprun_s8 = QUBO_Split_Optimization_func.findind_LR_deep_jo(vars_4t, vars_4t + vars_5 + vars_6 + vars_78, total_cost_4 + cost_5 + cost_6 + cost_78, solver)
            if optimal_jo[0] == dp_optimal_cost:
                print(f'Yes,found optimal JO for split 4(t)+1+1+1+1 & #variables:{len(optimal_jo[3])} and #exp:{exprun_s8}.')
                optimal_jo_details.append(optimal_jo)
            else:
                print(f'No,optimal JO not found for split 4(t)+1+1+1+1 & #variables:{len(optimal_jo[3])} & #exp:{exprun_s8}.')
            exp_run += exprun_s8
            print(f'# total exps run:{exp_run} and #splits{count}.')
    
       # Output log generation
        info = list()
        info.append(len(c_join_relations))
        info.append(len(variables_ae))
        info.append(exp_run)  
        number_of_solutions = len(optimal_jo_details)
        if number_of_solutions == 1:
            vars_list = optimal_jo_details[0][4]
            lowest_energy_state = optimal_jo_details[0][2].lowest().record[0][0]
            self.logDwaveResult(optimal_jo_details[0][2], relations, optimal_jo_details[0][3], optimal_jo_details[0][4], dp_optimal_cost, optimal_jo_details[0][0], info, solver, changed, dp_optimal_cost_wo_ecp)
            #print('jo tree: ', Helping_functions.make_join_order_tree(lowest_energy_state, vars_list, relations))
            return Helping_functions.make_join_order_tree(lowest_energy_state, vars_list, relations)
        elif number_of_solutions > 1:
            #print('Multiple solutions found!!!')
            best_solution = []
            for i in range(number_of_solutions):
                best_solution.append([i, optimal_jo_details[i][2].aggregate().lowest().record[0][2]])
            #print('all_solution_lists:',best_solution)
            best_solution = max(best_solution , key = lambda e:e[1])
            #print('best_solution and index:',best_solution)
            i = best_solution[0]
            vars_list = optimal_jo_details[i][4]
            lowest_energy_state = optimal_jo_details[i][2].lowest().record[0][0]
            self.logDwaveResult(optimal_jo_details[i][2], relations, optimal_jo_details[i][3], optimal_jo_details[i][4], dp_optimal_cost, optimal_jo_details[i][0], info, solver, changed, dp_optimal_cost_wo_ecp)
            return Helping_functions.make_join_order_tree(lowest_energy_state, vars_list, relations)
        elif number_of_solutions == 0:
            #print('No solution found!!!')
            optimal_jo_details.append(optimal_jo)
            vars_list = optimal_jo_details[0][4]
            lowest_energy_state = optimal_jo_details[0][2].lowest().record[0][0]
            self.logDwaveResult(optimal_jo_details[0][2], relations, optimal_jo_details[0][3], optimal_jo_details[0][4], dp_optimal_cost, optimal_jo_details[0][0], info, solver, changed, dp_optimal_cost_wo_ecp)
            return Helping_functions.make_join_order_tree(lowest_energy_state, vars_list, relations)

class QUBO_Split_Optimization_func_qiskit():

    def __init__(self, filename):
        self.logfile = open("servers/qubo/{}.log".format(filename),"w")

    def __del__(self):
        self.logfile.close()

    def logQiskitResult(self, result, relations, weights, lst, dp_optimal_cost, total_cost, error):
        self.logfile.write("# {} ; {}\n".format(",".join(relations), ",".join(str(e) for e in weights)))
        lowest_fval = result.fval
        for r in result.samples:
            logData = [",".join(relations)]
            logData.append(r.probability)
            logData.append(r.fval)
            order, variables, _error_ = Helping_functions.quboToTree(r.x, lst, relations)
            logData.append("Valid" if error == None else "Invalid")
            logData.append("Optimal" if total_cost == dp_optimal_cost and r.fval == lowest_fval else "Not Optimal")
            logData.append(order)
            logData.append(variables)
            logData.append(total_cost)
            self.logfile.write(";".join([str(e) for e in logData]))
            self.logfile.write("\n")
            self.logfile.flush()

    def findind_LR_deep_jo_qiskit(relations, vars_J2R, All_vars, weights, solver, local_optimizer):
        '''
        This function is defined for the left and right deep join tree.
        '''
        #relation_combinations = QUBO_formulation.relation_sublists(relations)
        #rel_comb=[list(lst) for lst in combinations(relations, 2)]
        optimal_jo_details = []
        for rel in vars_J2R:
            vars_list = []
            cost_list = []
            for i, elem in enumerate(All_vars):
                if(set(rel).issubset(set(elem))):
                    vars_list.append(elem)
                    cost_list.append(weights[i])
            result, order, optimized_jo_vars, error = Experiments_class.qiskit_experiment_for_list_vars(relations, vars_list, cost_list, solver, local_optimizer)
            total_cost = 0
            for i in range(len(result.x)):
                if result.x[i]==1:
                    total_cost += cost_list[i]
            optimal_jo_details.append([total_cost, order, optimized_jo_vars, error, result])
            #time.sleep(60)
        optimal_jo_details = (min(optimal_jo_details, key = lambda e:e[0]))
        return optimal_jo_details

    def joo_by_split_SS_outer_Bushy_qiskit(relations, variables_ae, weights_ae, length, solver, local_optimizer):
        
        '''
        This function is defined to find the jo by splitting the splitted search space further.
        we don't use the dynamic programming but the only quantum annealing and quantum simulations.
        This function can be used for the outer bushy trees.
        '''
        store_jo_details = {}
        temp_1 = []
        temp_2 = []
        cost_1 = []
        cost_2 = []
        store_final_vars = []
        store_total_cost = []
        opt_jo_details = []
        #relation_combinations = QUBO_formulation.relation_sublists(relations)
        if len(relations) != 2*length:
            rel_comb = [list(lst) for lst in combinations(relations,length)]
        else:
            rel_comb = [list(lst) for lst in combinations(relations,length)]
            rel_comb = rel_comb[0:int(len(rel_comb)/2)]
        for rel in rel_comb:
            temp_lst = QUBO_formulation.relation_sublists(rel)
            new_rel_vars_list = list()
            new_rel_vars_list = [var for var in temp_lst if var in variables_ae]
            #print('new_rel_vars_list:-',new_rel_vars_list)
            rel_remaining = list()
            for elm in relations:
                if(elm not in rel):
                    rel_remaining.append(elm)

            l = len(rel_remaining)

            temp_lst_2 = QUBO_formulation.relation_sublists(rel_remaining)
            new_rel_vars_list_remaining = []
            for var in temp_lst_2:
                if var in variables_ae:
                    new_rel_vars_list_remaining.append(var)
            #print('new_rel_vars_list_rem:-',new_rel_vars_list_remaining)
            new_list = new_rel_vars_list + new_rel_vars_list_remaining + [relations]
            new_weights = []
            for var in new_list:
                new_weights.append(weights_ae[variables_ae.index(var)])
            result, order, optimized_jo_vars, error = Experiments_class.qiskit_experiment_for_list_vars(relations, new_list, new_weights, solver, local_optimizer)
            #time.sleep(60)
            total_cost = 0
            for i in range(len(result.x)):
                if result.x[i]==1:
                    total_cost += new_weights[i]
            opt_jo_details.append([total_cost, order, optimized_jo_vars, error, result ])
            opt_vars = optimized_jo_vars.copy()
            temp_3 = []
            for var in opt_vars:
                if len(var)==length:
                    temp_3.append(var)
            if len(temp_3) == 0:
                continue
            lst1,lst2 = Helping_functions.separate_variables(opt_vars, new_list, new_weights, length)
            if(l>2):
                store_jo_details[frozenset(lst1[-2])] = lst1
                store_jo_details[frozenset(lst2[-2])] = lst2
                temp_1.append(lst1[-2])
                cost_1.append(lst1[-1])
                temp_2.append(lst2[-2])
                cost_2.append(lst2[-1])
            else:
                store_jo_details[frozenset(lst2[-2])] = lst2
                temp_2.append(lst2[-2])
                cost_2.append(lst2[-1])
        opt_jo_details = (min(opt_jo_details, key = lambda e : e[0]))
        if(len(temp_1)!=0):
            store_final_vars.append(temp_1)
            store_final_vars.append(temp_2)
            store_total_cost.append(cost_1)
            store_total_cost.append(cost_2)
        else:
            store_final_vars += temp_2
            store_total_cost += cost_2
        
        return  opt_jo_details, store_jo_details, store_final_vars, store_total_cost

    def finding_opt_jo_qiskit(self, relations, weights, solver, local_optimizer):
        
        '''
        This definition has been enabled to find the optimal join order for relations 4,5,6,7 and 8.
        '''
        
        optimal_jo_details = []
        n = len(relations)
        l = 0
        dp_opt_jo_cost = Helping_functions.dynamic_programming(relations, weights)
        dp_optimal_cost = dp_opt_jo_cost[1]
        #print(dp_opt_jo_cost)

        # defining variables and their cost after eliminating cartisian product
        list1 = QUBO_formulation.relation_sublists(relations)
        list2 = QUBO_formulation.vars_with_joins(relations)
        variables_ae, weights_ae = QUBO_formulation.Elimination_vars_weights(list1, list2, weights)

        
        '''
        Solving for the 3 relations query.
        '''
        if n == 3:
            # lets check optimal soln for L/R deep join order.
            vars_2, cost_2 = Helping_functions.single_cost_var(variables_ae, weights_ae, [2])
            optimal_jo = QUBO_Split_Optimization_func_qiskit.findind_LR_deep_jo_qiskit(relations, vars_2, variables_ae, weights_ae, solver, local_optimizer)
            if(optimal_jo[0] == dp_optimal_cost):
                print('Yes, We found the optimal join-order for L/R join order.')
                optimal_jo_details.append(optimal_jo)

        '''
        Solving for the 4 relations query.
        '''

        if n == 4:
            # lets check optimal soln for L/R deep join order.
            vars_2, cost_2 = Helping_functions.single_cost_var(variables_ae, weights_ae, [2])
            optimal_jo = QUBO_Split_Optimization_func_qiskit.findind_LR_deep_jo_qiskit(relations, vars_2, variables_ae, weights_ae, solver, local_optimizer)
            if(optimal_jo[0] == dp_optimal_cost):
                print('Yes, We found the optimal join-order for L/R join order.')
                optimal_jo_details.append(optimal_jo)

            # lets check the optimal soln for 2+2
            vars_4, cost_4 = Helping_functions.single_cost_var(variables_ae, weights_ae, [4])
            weights = cost_2 + cost_4
            result, order, optimized_jo_vars, error = Experiments_class.qiskit_experiment_for_list_vars(relations, vars_2 + vars_4, weights, solver, local_optimizer)
            total_cost = sum(weights[i] for i in range(len(result.x)) if result.x[i] == 1)
            if total_cost == dp_optimal_cost:
                print('Yes, We found the optimal join-order for this query.')
                optimal_jo_details.append([total_cost, order, optimized_jo_vars, error, result])

        '''
        Solving for the 5 relations query.
        '''

        if n == 5:
            # lets check optimal soln for L/R deep join order.
            vars_2, cost_2 = Helping_functions.single_cost_var(variables_ae, weights_ae, [2])
            optimal_jo = QUBO_Split_Optimization_func_qiskit.findind_LR_deep_jo_qiskit(relations, vars_2, variables_ae, weights_ae, solver, local_optimizer)
            if(optimal_jo[0] == dp_optimal_cost):
                print('Yes, We found the optimal join-order for L/R join order.')
                optimal_jo_details.append(optimal_jo)
            
            #checking for the (4+1) as ((2+2)+1)
            vars_45, cost_45 = Helping_functions.single_cost_var(variables_ae, weights_ae, [4,5])
            weights = cost_2 + cost_45
            result, order, optimized_jo_vars, error = Experiments_class.qiskit_experiment_for_list_vars(relations, vars_2 + vars_45, weights, solver, local_optimizer)
            total_cost = sum(weights[i] for i in range(len(result.x)) if result.x[i] == 1)
            if total_cost == dp_optimal_cost:
                print('Yes, We found the optimal join-order for the split 4+1 as ((2+2)+1).')
                optimal_jo_details.append([total_cost, order, optimized_jo_vars, error, result])
            
            #checking for the 3+2
            opt_detail, store_jo_details, store_final_vars, store_total_cost = QUBO_Split_Optimization_func_qiskit.joo_by_split_SS_outer_Bushy_qiskit(relations, variables_ae, weights_ae, 3, solver, local_optimizer)
            if(opt_detail[0] == dp_optimal_cost):
                print('Yes, We found the optimal join-order for the split 3+2.')
                optimal_jo_details.append(opt_detail)

        number_of_solutions = len(optimal_jo_details)
        if number_of_solutions != 0:
            self.logQiskitResult(optimal_jo_details[0][4], relations, weights_ae, variables_ae, dp_optimal_cost, optimal_jo_details[0][0], optimal_jo_details[0][3])
            return optimal_jo_details[0][1], optimal_jo_details[0][2], optimal_jo_details[0][3]
        else:
            #print('No solution found!!!')
            optimal_jo_details.append(optimal_jo)
            self.logQiskitResult(optimal_jo_details[0][4], relations, weights_ae, variables_ae, dp_optimal_cost, optimal_jo_details[0][0], optimal_jo_details[0][3])
            return optimal_jo_details[0][1], optimal_jo_details[0][2], optimal_jo_details[0][3]
        
    def finding_opt_jo_dp(self, relations, weights):
        
        '''
        This definition has been enabled to find the optimal join order for relations 4,5,6,7 and 8.
        '''
        dp_opt_jo_cost = Helping_functions.dynamic_programming(relations, weights)
        dp_optimal_cost = dp_opt_jo_cost[1]
        print('dp_opt_jo',dp_opt_jo_cost[0])
        dp_opt_jo_cost_wo_ecp = Helping_functions.dynamic_programming_wo_ecp(relations, weights)
        dp_optimal_cost_wo_ecp = dp_opt_jo_cost_wo_ecp[1]
        print('dp_opt_jo_wo_ecp',dp_opt_jo_cost_wo_ecp[0])
        changed = 0
        if dp_optimal_cost != dp_optimal_cost_wo_ecp:
            changed = 1
        print('changed:',changed)
        return dp_opt_jo_cost