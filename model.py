import gurobipy as gp
import numpy as np
import pandas as pd
from gurobipy import GRB
import rasterio



def mip(budget):
    #Placeholder for material cost of planting 1 tree
    t = 10

    #Placeholder for site cost of planting 1 tree

    siteCost = 20

    #Placeholder for max # of trees at 1 location
    maxT = 100


    HI1 = 0.5
    HI2 = 2.5


    #reading data
    src = rasterio.open("ForUSTree_2018_HighVeg_TreeCoverage.tif")
    #b = src.read(1)
    b = np.random.beta(a=2, b=5, size=(100, 150)) * 0.6

    src = rasterio.open("texas_clipped.tif")
    #imp = src.read(1)
    imp = np.random.beta(a=2, b=2, size=(100, 150)) 



    # -----------------------------
    # Parameters
    # -----------------------------
    siteCost = 20
    maxT = 100

    n, p = b.shape
    

    # -----------------------------
    # Tree types
    # -----------------------------
    tree_types = ["3gal", "5gal", "10gal"]
    K = len(tree_types)

    # cost per tree type
    t = np.array([8, 12, 20], dtype=float)

    # canopy fraction gained per tree type
    # example: 3gal adds 0.6%, 5gal adds 1.0%, 10gal adds 1.8%
    gamma = np.array([0.006, 0.010, 0.018], dtype=float)

    # -----------------------------
    # Data placeholders
    # Replace these with real arrays
    # -----------------------------
    a_base = np.ones((n, p), dtype=int)
    # b = np.random.uniform(0.0, 0.60, size=(n, p))
    # imp = np.random.uniform(0.0, 1.0, size=(n, p))

    # Imperviousness threshold
    imp_threshold = 0.85
    a = a_base * (imp <= imp_threshold).astype(int)

    # -----------------------------
    # Imperviousness-adjusted cooling coefficients
    # -----------------------------
    HI1_grid = np.zeros((n, p))
    HI2_grid = np.zeros((n, p))

    low_imp = imp < 0.25
    mid_imp = (imp >= 0.25) & (imp < 0.50)
    high_imp = imp >= 0.50

    HI1_grid[low_imp]  = 0.75 / 100
    HI2_grid[low_imp]  = 2.00 / 100

    HI1_grid[mid_imp]  = 0.30 / 100
    HI2_grid[mid_imp]  = 2.50 / 100

    HI1_grid[high_imp] = 0.10 / 100
    HI2_grid[high_imp] = 1.80 / 100

    beta = 1.0 + 0.75 * imp

    # -----------------------------
    # Band setup from baseline canopy b
    # -----------------------------
    u = np.maximum(0.40 - b, 0.0)
    Mtot = np.maximum(0.80 - b, 0.0)

    # -----------------------------
    # Model
    # -----------------------------
    model = gp.Model("MILP_multi_tree_types")

    # -----------------------------
    # Variables
    # -----------------------------
    # x[i,j,k] = number of trees of type k planted at site (i,j)
    x = model.addMVar(shape=(n, p, K), vtype=GRB.INTEGER, lb=0, name="x")

    # y[i,j] = whether site (i,j) is activated
    y = model.addMVar(shape=(n, p), vtype=GRB.BINARY, name="y")

    # total added canopy at each site
    addCanopy = model.addMVar(shape=(n, p), vtype=GRB.CONTINUOUS, lb=0.0, name="addCanopy")

    # band split
    z1 = model.addMVar(shape=(n, p), vtype=GRB.CONTINUOUS, lb=0.0, name="z_band1")
    z2 = model.addMVar(shape=(n, p), vtype=GRB.CONTINUOUS, lb=0.0, name="z_band2")
    w = model.addMVar(shape=(n, p), vtype=GRB.BINARY, name="cross40")

    # -----------------------------
    # Constraints
    # -----------------------------

    # Budget: tree purchase costs + fixed site activation costs
    model.addConstr(
        gp.quicksum(t[k] * x[:, :, k].sum() for k in range(K)) + siteCost * y.sum() <= budget,
        name="budget"
    )

    # Activation: total number of trees at a site only if site is activated
    model.addConstr(
        x.sum(axis=2) <= maxT * y,
        name="maxTreesPerSite"
    )

    # Feasibility mask
    model.addConstr(y <= a, name="allowedSites")

    # Trees -> added canopy
    model.addConstr(
        addCanopy == gp.quicksum(gamma[k] * x[:, :, k] for k in range(K)),
        name="canopy_from_trees"
    )

    # Cap total canopy at 80%
    model.addConstr(addCanopy <= Mtot, name="cap_at_80")

    # Split added canopy into two canopy bands
    model.addConstr(z1 + z2 == addCanopy, name="split_canopy")

    # Band 1 fills up to 40%
    model.addConstr(z1 <= u, name="band1_cap")

    # Logic for entering band 2 only after filling band 1
    model.addConstr(addCanopy <= u + Mtot * w, name="cross_logic_a")
    model.addConstr(z2 <= Mtot * w, name="cross_logic_z2")
    model.addConstr(z1 >= u * w, name="cross_logic_fill1")
    model.addConstr(z1 <= addCanopy, name="z1_le_add")

    # -----------------------------
    # Objective
    # -----------------------------
    degrees_cooled = 100.0 * ((beta * HI1_grid * z1).sum() + (beta * HI2_grid * z2).sum())
    model.setObjective(degrees_cooled, GRB.MAXIMIZE)

    # -----------------------------
    # Optimize
    # -----------------------------
    model.optimize()

    # -----------------------------
    # Example outputs
    # -----------------------------
    if model.Status == GRB.OPTIMAL:
        x_sol = x.X
        y_sol = y.X
        z1_sol = z1.X
        z2_sol = z2.X

        print(f"Optimal objective (weighted cooling): {model.ObjVal:.4f}")
        print(f"Total trees planted: {x_sol.sum():.0f}")
        print(f"Activated sites: {(y_sol > 0.5).sum()}")

        for k, name in enumerate(tree_types):
            print(f"Total {name} trees planted: {x_sol[:, :, k].sum():.0f}")

        selected = y_sol > 0.5
        if selected.sum() > 0:
            print(f"Average imperviousness of selected sites: {imp[selected].mean():.4f}")
            print(f"Average baseline canopy of selected sites: {b[selected].mean():.4f}")
    else:
        print(f"Model ended with status code {model.Status}")


mip(1000)