import gurobipy as gp
import numpy as np
import pandas as pd
from gurobipy import GRB
import rasterio



#imp = src.read(1)
imp = np.random.beta(a=2, b=2, size=(100, 150)) 


#b = src.read(1)
b = np.random.beta(a=2, b=5, size=(100, 150)) * 0.6

def forestry_mip(
    budget,
    b,
    imp,
    tree_type_names,
    tree_cost_dict,
    tree_canopy_gain_dict,
    tree_inventory_limit_dict,   # NEW
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

    tree_inventory_limit_dict : dict[str, int | float]
        Maps tree type name -> max number of trees available to purchase.

    selected_regions : dict[str, list[tuple[int, int]]] | None
        Maps region name/id -> list of grid cells.

    region_requirements : dict[str, dict] | None
        Optional constraints on selected regions.

    site_cost : float
        Fixed cost to activate a planting site.

    max_trees_per_site : int
        Maximum total trees that can be planted at one site.

    imp_threshold : float
        Sites with imp > imp_threshold are not plantable.

    verbose : bool
        Whether to print Gurobi output.
    """

    # -----------------------------
    # Validation
    # -----------------------------
    if b.shape != imp.shape:
        raise ValueError("b and imp must have the same shape.")

    n, p = b.shape

    selected_regions = selected_regions or {}
    region_requirements = region_requirements or {}

    for name in tree_type_names:
        if name not in tree_cost_dict:
            raise KeyError(f"Missing cost for tree type '{name}'.")
        if name not in tree_canopy_gain_dict:
            raise KeyError(f"Missing canopy gain for tree type '{name}'.")
        if name not in tree_inventory_limit_dict:
            raise KeyError(f"Missing inventory limit for tree type '{name}'.")

    K = len(tree_type_names)
    tree_type_to_idx = {name: k for k, name in enumerate(tree_type_names)}
    t = np.array([tree_cost_dict[name] for name in tree_type_names], dtype=float)
    gamma = np.array([tree_canopy_gain_dict[name] for name in tree_type_names], dtype=float)
    inventory_limits = np.array(
        [tree_inventory_limit_dict[name] for name in tree_type_names],
        dtype=float
    )

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

    x = model.addMVar(shape=(n, p, K), vtype=GRB.INTEGER, lb=0, name="x")
    y = model.addMVar(shape=(n, p), vtype=GRB.BINARY, name="y")
    addCanopy = model.addMVar(shape=(n, p), vtype=GRB.CONTINUOUS, lb=0.0, name="addCanopy")
    z1 = model.addMVar(shape=(n, p), vtype=GRB.CONTINUOUS, lb=0.0, name="z1")
    z2 = model.addMVar(shape=(n, p), vtype=GRB.CONTINUOUS, lb=0.0, name="z2")
    w = model.addMVar(shape=(n, p), vtype=GRB.BINARY, name="cross40")

    # -----------------------------
    # Core constraints
    # -----------------------------
    model.addConstr(
        gp.quicksum(t[k] * x[:, :, k].sum() for k in range(K)) + site_cost * y.sum() <= budget,
        name="budget"
    )

    model.addConstr(
        x.sum(axis=2) <= max_trees_per_site * y,
        name="maxTreesPerSite"
    )

    model.addConstr(
        y <= a,
        name="allowedSites"
    )

    model.addConstr(
        addCanopy == gp.quicksum(gamma[k] * x[:, :, k] for k in range(K)),
        name="canopy_from_trees"
    )

    model.addConstr(
        addCanopy <= Mtot,
        name="cap_at_80"
    )

    model.addConstr(z1 + z2 == addCanopy, name="split_canopy")
    model.addConstr(z1 <= u, name="band1_cap")
    model.addConstr(addCanopy <= u + Mtot * w, name="cross_logic_a")
    model.addConstr(z2 <= Mtot * w, name="cross_logic_z2")
    model.addConstr(z1 >= u * w, name="cross_logic_fill1")
    model.addConstr(z1 <= addCanopy, name="z1_le_add")

    # NEW: inventory limits by tree type
    for k in range(K):
        model.addConstr(
            x[:, :, k].sum() <= inventory_limits[k],
            name=f"inventory_limit_{tree_type_names[k]}"
        )

    # -----------------------------
    # Selected region constraints
    # -----------------------------
    for region_id, req in region_requirements.items():
        if region_id not in selected_regions:
            raise KeyError(f"Region requirement provided for unknown region '{region_id}'.")

        cells = selected_regions[region_id]
        if len(cells) == 0:
            raise ValueError(f"Region '{region_id}' has no cells.")

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

    model.optimize()

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

