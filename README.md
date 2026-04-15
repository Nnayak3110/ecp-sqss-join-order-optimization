This repository contains the implementation and experimental artifacts for the research paper:

**"Improved Join Order Optimization for Database Queries using Hybrid Quantum-Classical Approaches for QUBO Problems"** 

---

## Overview

Join Order Optimization (JOO) is a fundamental problem in database systems and is known to be NP-hard. This work formulates the JOO problem as a **Quadratic Unconstrained Binary Optimization (QUBO)** problem and proposes a **hybrid quantum-classical approach** to solve it efficiently.

The key contributions of this work include:

- **Eliminating Cartesian Products (ECP)** to reduce unnecessary intermediate joins and reduce the QUBO search space.
- **Splitting the QUBO Search Space (SQSS)** to make large optimization problems tractable on current quantum hardware.
- Integration with multiple optimization approaches:
  - Quantum Annealing (QA)
  - Simulated Annealing (SA)
  - Variational Quantum Eigensolver (VQE)
  - Quantum Approximate Optimization Algorithm (QAOA)
- Evaluation on real-world SQL queries (ErgastF1 dataset).
- Analysis of **selectivity impact** on QUBO weight distribution and optimization performance.

The approach improves algorithms performance for large problems and reduces hardware requirements while maintaining optimal join order solutions.
---
