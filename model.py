import gurobipy as gp
import numpy as np
import pandas as pd
from gurobipy import GRB
import rasterio


src = rasterio.open("texas_clipped.tif")
#imp = src.read(1)
imp = np.random.beta(a=2, b=2, size=(100, 150)) 

src = rasterio.open("ForUSTree_2018_HighVeg_TreeCoverage.tif")
#b = src.read(1)
b = np.random.beta(a=2, b=5, size=(100, 150)) * 0.6

def mip(budget, treeCoverage, imp):
    #Placeholder for material cost of planting 1 tree
    t = 10

    #Placeholder for site cost of planting 1 tree

    siteCost = 20

    #Placeholder for max # of trees at 1 location
    maxT = 100


    HI1 = 0.5
    HI2 = 2.5


    #reading data
    

    



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





def forestry_mip(
    budget,
    b,
    imp,
    tree_type_names,
    tree_cost_dict,
    tree_canopy_gain_dict,
    selected_regions=None,
    region_requirements=None,
    site_cost=20.0,
    max_trees_per_site=100,
    imp_threshold=0.85,
    verbose=False
):
    """
    Solve the forestry planting problem.

    The model may plant anywhere in Houston that is feasible.
    If selected region requirements are provided, it must plant at least
    the requested number of trees inside those regions.

    Parameters
    ----------
    budget : float
        Total planting budget.

    b : np.ndarray of shape (n, p)
        Baseline canopy fraction at each site, usually in [0,1].

    imp : np.ndarray of shape (n, p)
        Imperviousness at each site, usually in [0,1].

    tree_type_names : list[str]
        Tree types selected by the UI, e.g. ["3gal", "5gal", "10gal"].

    tree_cost_dict : dict[str, float]
        Maps tree type name -> cost per tree.

    tree_canopy_gain_dict : dict[str, float]
        Maps tree type name -> canopy fraction gained per tree.

    selected_regions : dict[str, list[tuple[int, int]]] | None
        Maps region name/id -> list of grid cells.
        Example:
            {
                "regionA": [(0,0), (0,1), (1,1)],
                "regionB": [(2,3), (2,4)]
            }

    region_requirements : dict[str, dict] | None
        Optional constraints on selected regions.
        Example:
            {
                "regionA": {"total_trees_min": 20},
                "regionB": {"total_trees_min": 10}
            }

        Supported keys per region:
            - "total_trees_min"
            - "total_trees_max"
            - "total_trees_exact"
            - "tree_type_counts"   # exact counts by type in that region

        If None or empty, no region planting requirements are enforced.

    site_cost : float
        Fixed cost to activate a planting site.

    max_trees_per_site : int
        Maximum total trees that can be planted at one site.

    imp_threshold : float
        Sites with imp > imp_threshold are not plantable.

    verbose : bool
        Whether to print Gurobi output.

    Returns
    -------
    result : dict
        Dictionary with optimization status and solution summaries.
    """

    # -----------------------------
    # Validation
    # -----------------------------
    if b.shape != imp.shape:
        raise ValueError("b and imp must have the same shape.")

    n, p = b.shape

    selected_regions = selected_regions or {}
    region_requirements = region_requirements or {}

    # Check tree type dictionaries
    for name in tree_type_names:
        if name not in tree_cost_dict:
            raise KeyError(f"Missing cost for tree type '{name}'.")
        if name not in tree_canopy_gain_dict:
            raise KeyError(f"Missing canopy gain for tree type '{name}'.")

    # Tree parameters in UI-specified order
    K = len(tree_type_names)
    tree_type_to_idx = {name: k for k, name in enumerate(tree_type_names)}
    t = np.array([tree_cost_dict[name] for name in tree_type_names], dtype=float)
    gamma = np.array([tree_canopy_gain_dict[name] for name in tree_type_names], dtype=float)

    # -----------------------------
    # Feasible planting mask
    # -----------------------------
    a_base = np.ones((n, p), dtype=int)
    a = a_base * (imp <= imp_threshold).astype(int)

    # -----------------------------
    # Imperviousness-adjusted cooling coefficients
    # -----------------------------
    HI1_grid = np.zeros((n, p))
    HI2_grid = np.zeros((n, p))

    low_imp = imp < 0.25
    mid_imp = (imp >= 0.25) & (imp < 0.50)
    high_imp = imp >= 0.50

    HI1_grid[low_imp] = 0.75 / 100.0
    HI2_grid[low_imp] = 2.00 / 100.0

    HI1_grid[mid_imp] = 0.30 / 100.0
    HI2_grid[mid_imp] = 2.50 / 100.0

    HI1_grid[high_imp] = 0.10 / 100.0
    HI2_grid[high_imp] = 1.80 / 100.0

    beta = 1.0 + 0.75 * imp

    # -----------------------------
    # Canopy band setup
    # -----------------------------
    u = np.maximum(0.40 - b, 0.0)
    Mtot = np.maximum(0.80 - b, 0.0)

    # -----------------------------
    # Build model
    # -----------------------------
    model = gp.Model("ForestryFrontendMIP")
    model.Params.OutputFlag = 1 if verbose else 0

    # x[i,j,k] = number of trees of type k planted at site (i,j)
    x = model.addMVar(shape=(n, p, K), vtype=GRB.INTEGER, lb=0, name="x")

    # y[i,j] = whether site (i,j) is activated
    y = model.addMVar(shape=(n, p), vtype=GRB.BINARY, name="y")

    # added canopy
    addCanopy = model.addMVar(shape=(n, p), vtype=GRB.CONTINUOUS, lb=0.0, name="addCanopy")

    # split canopy bands
    z1 = model.addMVar(shape=(n, p), vtype=GRB.CONTINUOUS, lb=0.0, name="z1")
    z2 = model.addMVar(shape=(n, p), vtype=GRB.CONTINUOUS, lb=0.0, name="z2")
    w = model.addMVar(shape=(n, p), vtype=GRB.BINARY, name="cross40")

    # -----------------------------
    # Core constraints
    # -----------------------------
    # Budget = tree purchase + site activation
    model.addConstr(
        gp.quicksum(t[k] * x[:, :, k].sum() for k in range(K)) + site_cost * y.sum() <= budget,
        name="budget"
    )

    # Site activation logic
    model.addConstr(
        x.sum(axis=2) <= max_trees_per_site * y,
        name="maxTreesPerSite"
    )

    # Feasible sites only
    model.addConstr(
        y <= a,
        name="allowedSites"
    )

    # Tree planting induces canopy increase
    model.addConstr(
        addCanopy == gp.quicksum(gamma[k] * x[:, :, k] for k in range(K)),
        name="canopy_from_trees"
    )

    # Cap total canopy increase so baseline + addCanopy <= 0.80
    model.addConstr(
        addCanopy <= Mtot,
        name="cap_at_80"
    )

    # Split canopy increase across two benefit bands
    model.addConstr(z1 + z2 == addCanopy, name="split_canopy")
    model.addConstr(z1 <= u, name="band1_cap")
    model.addConstr(addCanopy <= u + Mtot * w, name="cross_logic_a")
    model.addConstr(z2 <= Mtot * w, name="cross_logic_z2")
    model.addConstr(z1 >= u * w, name="cross_logic_fill1")
    model.addConstr(z1 <= addCanopy, name="z1_le_add")

    # -----------------------------
    # Selected region constraints
    # These are LOWER BOUNDS / optional extra requirements.
    # The model may still plant anywhere else in Houston.
    # -----------------------------
    for region_id, req in region_requirements.items():
        if region_id not in selected_regions:
            raise KeyError(f"Region requirement provided for unknown region '{region_id}'.")

        cells = selected_regions[region_id]
        if len(cells) == 0:
            raise ValueError(f"Region '{region_id}' has no cells.")

        # Validate cells
        for (i, j) in cells:
            if not (0 <= i < n and 0 <= j < p):
                raise IndexError(f"Cell {(i, j)} in region '{region_id}' is out of bounds.")

        total_region_trees = gp.quicksum(
            x[i, j, k] for (i, j) in cells for k in range(K)
        )

        if "total_trees_exact" in req and req["total_trees_exact"] is not None:
            model.addConstr(
                total_region_trees == req["total_trees_exact"],
                name=f"{region_id}_total_exact"
            )

        else:
            if "total_trees_min" in req and req["total_trees_min"] is not None:
                model.addConstr(
                    total_region_trees >= req["total_trees_min"],
                    name=f"{region_id}_total_min"
                )

            if "total_trees_max" in req and req["total_trees_max"] is not None:
                model.addConstr(
                    total_region_trees <= req["total_trees_max"],
                    name=f"{region_id}_total_max"
                )

        # Optional exact per-tree-type counts in this region
        tree_type_counts = req.get("tree_type_counts", {})
        for tree_name, count in tree_type_counts.items():
            if tree_name not in tree_type_to_idx:
                raise KeyError(
                    f"Region '{region_id}' references unknown selected tree type '{tree_name}'."
                )
            k = tree_type_to_idx[tree_name]
            model.addConstr(
                gp.quicksum(x[i, j, k] for (i, j) in cells) == count,
                name=f"{region_id}_{tree_name}_count"
            )

    # -----------------------------
    # Objective
    # -----------------------------
    degrees_cooled = 100.0 * (
        (beta * HI1_grid * z1).sum() +
        (beta * HI2_grid * z2).sum()
    )
    model.setObjective(degrees_cooled, GRB.MAXIMIZE)

    # -----------------------------
    # Solve
    # -----------------------------
    model.optimize()

    # -----------------------------
    # Package results
    # -----------------------------
    result = {
        "status_code": int(model.Status),
        "status": None,
        "objective_value": None,
        "total_trees": None,
        "total_cost": None,
        "trees_by_type": None,
        "activated_sites": None,
        "x_sol": None,
        "y_sol": None,
        "region_tree_totals": {},
    }

    status_map = {
        GRB.OPTIMAL: "OPTIMAL",
        GRB.INFEASIBLE: "INFEASIBLE",
        GRB.UNBOUNDED: "UNBOUNDED",
        GRB.INF_OR_UNBD: "INF_OR_UNBD",
        GRB.TIME_LIMIT: "TIME_LIMIT",
    }
    result["status"] = status_map.get(model.Status, f"STATUS_{model.Status}")

    if model.Status == GRB.OPTIMAL:
        x_sol = np.rint(x.X).astype(int)
        y_sol = y.X

        total_tree_cost = sum(t[k] * x_sol[:, :, k].sum() for k in range(K))
        total_site_cost = site_cost * int((y_sol > 0.5).sum())
        total_cost = float(total_tree_cost + total_site_cost)

        trees_by_type = {
            tree_type_names[k]: int(x_sol[:, :, k].sum())
            for k in range(K)
        }

        region_tree_totals = {}
        for region_id, cells in selected_regions.items():
            region_tree_totals[region_id] = int(
                sum(x_sol[i, j, :].sum() for (i, j) in cells)
            )

        result.update({
            "objective_value": float(model.ObjVal),
            "total_trees": int(x_sol.sum()),
            "total_cost": total_cost,
            "trees_by_type": trees_by_type,
            "activated_sites": int((y_sol > 0.5).sum()),
            "x_sol": x_sol,
            "y_sol": y_sol,
            "region_tree_totals": region_tree_totals,
        })

    return result


def run_sample_test():
    # -----------------------------
    # Small toy Houston grid
    # -----------------------------
    b = np.array([
        [0.10, 0.20, 0.15],
        [0.05, 0.30, 0.10],
        [0.25, 0.10, 0.35]
    ], dtype=float)

    imp = np.array([
        [0.20, 0.30, 0.90],   # (0,2) is infeasible because > imp_threshold
        [0.10, 0.40, 0.50],
        [0.60, 0.15, 0.20]
    ], dtype=float)

    # Tree data stored elsewhere
    tree_cost_dict = {
        "3gal": 8,
        "5gal": 12,
        "10gal": 20
    }

    tree_canopy_gain_dict = {
        "3gal": 0.006,
        "5gal": 0.010,
        "10gal": 0.018
    }

    tree_type_names = ["3gal", "5gal"]

    # Selected regions from UI
    selected_regions = {
        "regionA": [(0, 0), (0, 1), (1, 0)],
        "regionB": [(2, 1), (2, 2)]
    }

    # Require at least 4 trees in regionA
    region_requirements = {
        "regionA": {"total_trees_min": 4}
    }

    result = forestry_mip(
        budget=120,
        b=b,
        imp=imp,
        tree_type_names=tree_type_names,
        tree_cost_dict=tree_cost_dict,
        tree_canopy_gain_dict=tree_canopy_gain_dict,
        selected_regions=selected_regions,
        region_requirements=region_requirements,
        site_cost=5,
        max_trees_per_site=10,
        imp_threshold=0.85,
        verbose=False
    )

    print("=== TEST 1: With region minimum ===")
    print("Status:", result["status"])
    print("Objective:", result["objective_value"])
    print("Total trees:", result["total_trees"])
    print("Total cost:", result["total_cost"])
    print("Trees by type:", result["trees_by_type"])
    print("Region totals:", result["region_tree_totals"])

    assert result["status"] == "OPTIMAL"
    assert result["region_tree_totals"]["regionA"] >= 4, "Region minimum not satisfied."
    assert result["total_cost"] <= 120 + 1e-6, "Budget violated."

    # Optional stronger check: because regionA minimum is 4, total trees must be at least 4
    assert result["total_trees"] >= 4

    print("Test 1 passed.")

    # -----------------------------
    # Test 2: No region requirements
    # -----------------------------
    result2 = forestry_mip(
        budget=120,
        b=b,
        imp=imp,
        tree_type_names=tree_type_names,
        tree_cost_dict=tree_cost_dict,
        tree_canopy_gain_dict=tree_canopy_gain_dict,
        selected_regions=selected_regions,
        region_requirements=None,   # No requirements
        site_cost=5,
        max_trees_per_site=10,
        imp_threshold=0.85,
        verbose=False
    )

    print("\n=== TEST 2: No region requirements ===")
    print("Status:", result2["status"])
    print("Objective:", result2["objective_value"])
    print("Total trees:", result2["total_trees"])
    print("Total cost:", result2["total_cost"])
    print("Trees by type:", result2["trees_by_type"])
    print("Region totals:", result2["region_tree_totals"])

    assert result2["status"] == "OPTIMAL"
    assert result2["total_cost"] <= 120 + 1e-6, "Budget violated in no-requirements case."

    print("Test 2 passed.")

    return result, result2
run_sample_test()