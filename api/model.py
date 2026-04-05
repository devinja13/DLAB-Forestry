import gurobipy as gp
import numpy as np
import pandas as pd
from gurobipy import GRB
import rasterio



#imp = src.read(1)
imp = np.random.beta(a=2, b=2, size=(100, 150)) 


#b = src.read(1)
b = np.random.beta(a=2, b=5, size=(100, 150)) * 0.6


# TREE PARAMETERS — FULL SUPPLIER DATA


CELL_AREA = 2500  # 50m x 50m grid cell


# MATERIAL COSTS


material_cost = {

    # ---------------- 3 GAL ----------------
    "American Beautyberry 3gal": 11,
    "Anacua 3gal": 12,
    "Birch River 3gal": 12,
    "Buttonbush 3gal": 11,
    "Cedar Eastern Red 3gal": 14,
    "Cypress Pond 3gal": 14,
    "Dogwood Roughleaf 3gal": 14,
    "Holly Deciduous Possumhaw 3gal": 12,
    "Hornbeam American 3gal": 12,
    "Mayhaw 3gal": 14,
    "Oak Cherrybark 3gal": 11,
    "Oak Chinquapin 3gal": 11,
    "Oak Swamp Chestnut 3gal": 11,
    "Pine Long needle 3gal": 12,
    "Plum Chickasaw 3gal": 14,
    "Sugarberry 3gal": 11,
    "Tupelo Blackgum 3gal": 14,
    "Viburnum Arrowwood 3gal": 14,
    "Vitex Chase tree 3gal": 14,

    # ---------------- 15 GAL ----------------
    "Ash Green 15gal": 65,
    "Bashem Light Pink 15gal": 65,
    "Birch River 15gal": 65,
    "Catawba purple 15gal": 65,
    "Cherry Black 15gal": 65,
    "Cypress Bald 15gal": 65,
    "Dogwood Roughleaf 15gal": 65,
    "Elm American 15gal": 65,
    "Elm Cedar 15gal": 65,
    "Elm Lacebark 15gal": 65,
    "Holly Deciduous Possumhaw 15gal": 65,
    "Holly Eagleston 15gal": 65,
    "Holly Yaupon 15gal": 65,
    "Magnolia Southern 15gal": 65,
    "Magnolia Sweetbay 15gal": 65,
    "Maple Drummond Red 15gal": 65,
    "Mulberry Red 15gal": 65,
    "Muskogee Lavender Pink 15gal": 65,
    "Natchez White 15gal": 65,
    "Oak Bur 15gal": 65,
    "Oak Cherrybark 15gal": 65,
    "Oak Chinquapin 15gal": 65,
    "Oak Live 15gal": 65,
    "Oak Monterrey White Mexican 15gal": 65,
    "Oak Nuttall 15gal": 65,
    "Oak Overcup 15gal": 65,
    "Oak Shumard 15gal": 65,
    "Oak Southern Red 15gal": 65,
    "Oak Swamp Chestnut 15gal": 65,
    "Oak Water 15gal": 65,
    "Oak White 15gal": 65,
    "Oak Willow 15gal": 65,
    "Pecan Native 15gal": 65,
    "Persimmon Common 15gal": 65,
    "Pine Loblolly 15gal": 65,
    "Pine Long needle 15gal": 65,
    "Plum Mexican 15gal": 65,
    "Redbud Eastern 15gal": 65,
    "Sugarberry 15gal": 65,
    "Sweetgum 15gal": 65,
    "Sycamore American 15gal": 65,
    "Tonto dark pink red-pink 15gal": 65,
    "Tuscarora watermelon pink 15gal": 65,
    "Vitex Chase tree 15gal": 65,

    # ---------------- 30 GAL ----------------
    "Cypress Bald 30gal": 150,
    "Elm American 30gal": 150,
    "Holly Yaupon 30gal": 150,
    "Magnolia Southern 30gal": 160,
    "Maple Drummond Red 30gal": 150,
    "Oak Bur 30gal": 150,
    "Oak Live 30gal": 150,
    "Oak Swamp Chestnut 30gal": 150,
    "Oak White 30gal": 150,
    "Pine Loblolly 30gal": 150,
    "Sycamore American 30gal": 150,
    "Vitex Chase tree 30gal": 150,
}


# PLANTING COST (MODERATE COMMERCIAL)


planting_cost = {}

for name in material_cost:
    if "3gal" in name:
        planting_cost[name] = 53
    elif "15gal" in name:
        planting_cost[name] = 363
    elif "30gal" in name:
        planting_cost[name] = 463
    else:
        planting_cost[name] = 363


# INVENTORY (FULL SUPPLIER MATCH)


inventory = {
    # 15 GAL
    "Ash Green 15gal": 195,
    "Bashem Light Pink 15gal": 50,
    "Birch River 15gal": 138,
    "Catawba purple 15gal": 50,
    "Cherry Black 15gal": 35,
    "Cypress Bald 15gal": 179,
    "Dogwood Roughleaf 15gal": 70,
    "Elm American 15gal": 0,
    "Elm Cedar 15gal": 351,
    "Elm Lacebark 15gal": 60,
    "Holly Deciduous Possumhaw 15gal": 100,
    "Holly Eagleston 15gal": 240,
    "Holly Yaupon 15gal": 906,
    "Magnolia Southern 15gal": 9,
    "Magnolia Sweetbay 15gal": 78,
    "Maple Drummond Red 15gal": 295,
    "Mulberry Red 15gal": 42,
    "Muskogee Lavender Pink 15gal": 50,
    "Natchez White 15gal": 371,
    "Oak Bur 15gal": 287,
    "Oak Cherrybark 15gal": 75,
    "Oak Chinquapin 15gal": 50,
    "Oak Live 15gal": 999,
    "Oak Monterrey White Mexican 15gal": 95,
    "Oak Nuttall 15gal": 163,
    "Oak Overcup 15gal": 126,
    "Oak Shumard 15gal": 1174,
    "Oak Southern Red 15gal": 20,
    "Oak Swamp Chestnut 15gal": 176,
    "Oak Water 15gal": 280,
    "Oak White 15gal": 14,
    "Oak Willow 15gal": 29,
    "Pecan Native 15gal": 212,
    "Persimmon Common 15gal": 98,
    "Pine Loblolly 15gal": 8,
    "Pine Long needle 15gal": 117,
    "Plum Mexican 15gal": 30,
    "Redbud Eastern 15gal": 35,
    "Sugarberry 15gal": 8,
    "Sweetgum 15gal": 12,
    "Sycamore American 15gal": 14,
    "Tonto dark pink red-pink 15gal": 50,
    "Tuscarora watermelon pink 15gal": 50,
    "Vitex Chase tree 15gal": 152,

    # 30 GAL
    "Cypress Bald 30gal": 19,
    "Elm American 30gal": 24,
    "Holly Yaupon 30gal": 87,
    "Magnolia Southern 30gal": 17,
    "Maple Drummond Red 30gal": 50,
    "Oak Bur 30gal": 30,
    "Oak Live 30gal": 785,
    "Oak Swamp Chestnut 30gal": 10,
    "Oak White 30gal": 11,
    "Pine Loblolly 30gal": 58,
    "Sycamore American 30gal": 61,
    "Vitex Chase tree 30gal": 30,
}

# Default large inventory for 3gal species
for k in material_cost:
    if k not in inventory:
        inventory[k] = 10**6

# CANOPY AREA (m² by size class)

canopy_area_m2 = {}

for name in material_cost:
    if "3gal" in name:
        canopy_area_m2[name] = 20
    elif "15gal" in name:
        canopy_area_m2[name] = 50
    elif "30gal" in name:
        canopy_area_m2[name] = 113
    else:
        canopy_area_m2[name] = 50

# FINAL DICTIONARIES USED BY MODEL

tree_type_names = list(material_cost.keys())

tree_cost_dict = {
    k: material_cost[k] + planting_cost[k]
    for k in tree_type_names
}

tree_canopy_gain_dict = {
    k: canopy_area_m2[k] / CELL_AREA
    for k in tree_type_names
}

tree_inventory_limit_dict = inventory

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

