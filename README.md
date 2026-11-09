# ECP-SQSS: Hybrid Quantum–Classical Join Order Optimization

Research implementation and experimental artifacts for [*Improved Join Order Optimization for Database Queries using Hybrid Quantum-Classical Approaches for QUBO Problems*](https://arxiv.org/abs/2606.16247).

Different join orders can produce very different intermediate results for the same SQL query. ECP-SQSS searches for a low-cost logical join tree by modeling join order optimization as a **quadratic unconstrained binary optimization (QUBO)** problem.

## How ECP-SQSS works

1. **Eliminating Cartesian Products (ECP)** removes candidate relation subsets whose induced join graph is disconnected. Joining all relations within such a subset would require a Cartesian product.
2. **Splitting the QUBO Search Space (SQSS)** searches the remaining space using smaller sub-QUBOs, reducing the size of individual optimization problems.

The study uses PostgreSQL 14.4 cardinality estimates for intermediate joins as QUBO weights. Dynamic programming supplies an exact reference for the evaluated search space and cost model. The experiments evaluate simulated annealing (SA), quantum annealing (QA), the Quantum Approximate Optimization Algorithm (QAOA), and the Variational Quantum Eigensolver (VQE).

## Repository contents

| Path | Contents |
| --- | --- |
| [`ECP_SQSS_QUBO.py`](ECP_SQSS_QUBO.py) | QUBO construction, ECP and SQSS routines, dynamic programming, and solver wrappers |
| [`SQL_queries_selectivity_exps/sql_queries.sql`](SQL_queries_selectivity_exps/sql_queries.sql) | SQL queries used in the controlled selectivity experiments |
| [`results/csv/`](results/csv/) | Data behind the reported figures, including QUBO size, subproblem counts, and solver outcomes |
| [`results/logs/`](results/logs/) | Saved simulated- and quantum-annealing logs for the selectivity experiments |
| [`results/png/`](results/png/) | Plots of the experimental results |

## Getting started

- **Inspect the results:** Start with the saved figures, then consult the corresponding CSV files and logs. No solver or quantum hardware access is needed to inspect these artifacts.
- **Explore the implementation:** The Python module is intended to be used from Python code, rather than as a command-line tool. It takes relation lists and precomputed weights for relation subsets, ordered by `QUBO_formulation.relation_sublists`. Join connectivity comes from the ErgastF1 relation mapping in the module.
- **Run new experiments:** Set up a compatible environment for the module’s D-Wave Ocean and Qiskit imports. The paper reports `dwave-neal==0.6.0` for SA and `qiskit==0.45.1` with `qiskit-optimization==0.5.0` for the gate-based experiments. This artifact snapshot does not include a pinned environment or a packaged PostgreSQL integration. Hardware QA also requires D-Wave access; configure your own credentials outside the source code before using any cloud-backed solver.

### Small local example

Once the module's dependencies are installed, try the dynamic-programming reference with synthetic costs. This calculation does not use a database connection or a quantum backend.

```python
from ECP_SQSS_QUBO import Helping_functions

relations = ["circuits", "races", "constructorresults"]

# Costs for (circuits, races), (circuits, constructorresults),
# (races, constructorresults), and the full relation set, in that order.
weights = [5, 99, 12, 4]

tree, cost = Helping_functions.dynamic_programming(relations, weights)
print(tree, cost)  # Joins circuits with races first; total modeled cost: 9.
```

## Evaluation and scope

The main study evaluates 145 queries with five to eight relations derived from the ErgastF1 schema. A separate ten-query experiment varies predicate selectivity and examines how it affects QUBO weights and solver outcomes. Comparisons with SQSS alone measure changes in formulation size, the number of sub-QUBO solves, and retrieval of optimal join orders under the modeled objective.

The evaluation covers connected inner joins. QUBO variable counts describe formulation size, not physical qubit usage. The paper does not report an end-to-end speed comparison against PostgreSQL’s native optimizer.

## Citation

If you use this code or these artifacts in your research, please cite the [arXiv preprint](https://arxiv.org/abs/2606.16247):

```bibtex
@misc{nayak2026ecpsqss,
  title         = {Improved Join Order Optimization for Database Queries using Hybrid Quantum-Classical Approaches for {QUBO} Problems},
  author        = {Nayak, Nitin and Winker, Tobias and Çalıkyılmaz, Umut and Groppe, Jinghua and Groppe, Sven},
  year          = {2026},
  eprint        = {2606.16247},
  archivePrefix = {arXiv},
  primaryClass  = {cs.DB},
  doi           = {10.48550/arXiv.2606.16247}
}
```
