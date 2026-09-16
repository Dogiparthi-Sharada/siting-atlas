"""Figures 1-3: system architecture, star schema, agent loop with gates.

Every connector anchors to a Rect edge via link(), so moving a box moves its
arrows with it. Every label is auto-fitted to its box by common.box().
"""

from __future__ import annotations

from common import (AQUA, AXIS, BLUE, CRITICAL, GOOD, GRID, INK, INK_2, MUTED,
                    ORANGE, PLANE, SEQ, SURFACE, WARNING, arrow, band,
                    blank_canvas, box, caption, elbow, link, newtag, save)


def fig01_architecture(out):
    """End-to-end flow: public sources -> warehouse -> models -> agent -> app."""
    fig, ax = blank_canvas(11.0, 6.8)

    # --- layer 1: sources ---------------------------------------------------
    band(ax, 1, 79, 98, 18,
         "1  PUBLIC DATA SOURCES  (no licensed panels, no API keys)")
    srcs = [("Census ACS\n5-year", 3), ("TIGER/Line\nshapefiles", 14.9),
            ("Zillow\nZORI / ZHVI", 26.8), ("Census CBP\nretail density", 38.7),
            ("BLS OES\nwages", 50.6), ("EIA energy\nprices", 62.5),
            ("Facility panel\n+ open dates", 74.4), ("EPA\nEJScreen", 86.3)]
    new = ("CBP", "EJScreen", "open dates")
    boxes = {}
    for label, x in srcs:
        is_new = any(k in label for k in new)
        boxes[label] = box(ax, x, 80.5, 10.6, 9.4, label,
                           edge=ORANGE if is_new else BLUE,
                           face="#fdf0ea" if is_new else SURFACE, fs=6.9)
    newtag(ax, 30, 75.4, "ADMINISTRATIVE - NO RATE LIMIT, NO KEY")
    newtag(ax, 74.4, 75.4, "THE TARGET VARIABLE")

    # --- layer 2: pipeline --------------------------------------------------
    band(ax, 1, 56, 98, 17, "2  ELT PIPELINE  ->  DuckDB WAREHOUSE")
    stages = [("Python\nextractors", 4, 14), ("Cloud\nstorage lake", 21, 14),
              ("dbt Core\ntransforms", 38, 14), ("DuckDB\nstar schema", 55, 14),
              ("Great Expectations\ndata contracts", 74, 22)]
    stage_rects = {}
    prev = None
    for label, x, w in stages:
        is_new = "Expectations" in label
        r = box(ax, x, 57.5, w, 9.4, label,
                edge=ORANGE if is_new else BLUE,
                face="#fdf0ea" if is_new else SURFACE, fs=7.4)
        stage_rects[label] = r
        if prev is not None:
            link(ax, prev, r)
        prev = r

    # sources feed the lake; the warehouse feeds the models
    link(ax, boxes["Census CBP\nretail density"],
         stage_rects["Cloud\nstorage lake"], sides=("b", "t"), rad=0.06)

    # --- layer 3: models ----------------------------------------------------
    band(ax, 1, 27, 47.5, 27, "3  ANALYTICAL MODELS")
    siting = box(ax, 3.5, 42.4, 42, 6.8,
                 "SITING / TIMING MODEL   discrete-time hazard\n"
                 "observable outcome: did the operator enable, and when",
                 edge=ORANGE, face="#fdf0ea", fs=7.0)
    newtag(ax, 3.5, 38.4, "OBSERVABLE OUTCOME - SCOREABLE")
    box(ax, 3.5, 33.0, 20, 4.6, "ZINB demand\n(secondary)", fs=7.0)
    box(ax, 25.5, 33.0, 20, 4.6, "LightGBM +\nSHAP benchmark", fs=7.0)
    scm = box(ax, 3.5, 27.8, 20, 4.6, "Spatial SCM\n+ decay radius",
              edge=ORANGE, face="#fdf0ea", fs=7.0)
    cost = box(ax, 25.5, 27.8, 20, 4.6, "Daganzo cost\n+ OD lookup (10 MB)",
               edge=ORANGE, face="#fdf0ea", fs=7.0)

    # --- layer 4: decisions -------------------------------------------------
    band(ax, 51.5, 27, 47.5, 27, "4  DECISION LAYER")
    port = box(ax, 54, 42.4, 42, 6.8,
               "PORTFOLIO OPTIMISER   bundles, not a ranking\n"
               "interaction: cannibalisation (-) + density (+)",
               edge=ORANGE, face="#fdf0ea", fs=7.0)
    newtag(ax, 54, 38.4, "BUNDLES, NOT A RANKING")
    box(ax, 54, 33.0, 20, 4.6, "Monte Carlo NPV\n10,000 draws", fs=7.0)
    box(ax, 76, 33.0, 20, 4.6, "Conformal\nintervals", edge=ORANGE,
        face="#fdf0ea", fs=7.0)
    rank = box(ax, 54, 27.8, 20, 4.6, "Top-K rank\nstability", edge=ORANGE,
               face="#fdf0ea", fs=7.0)
    box(ax, 76, 27.8, 20, 4.6, "8-bucket capital\ndecomposition", fs=7.0)

    link(ax, stage_rects["DuckDB\nstar schema"], siting,
         sides=("b", "t"), fracs=(0.4, 0.6))
    link(ax, siting, port, sides=("r", "l"), rad=-0.12)

    # --- the offline step ---------------------------------------------------
    offline = box(ax, 3.5, 21.0, 60, 4.2,
                  "OFFLINE, ONCE:   OSRM per metro  ->  OD matrix  ->  DELETE "
                  "artifacts   (peak disk 8 GB, not 60 GB)",
                  edge=MUTED, face=PLANE, ls="--", lw=1.1, fs=6.8, color=INK_2)
    link(ax, offline, cost, sides=("t", "b"), fracs=(0.35, 0.5),
         color=MUTED, ls="--")

    # --- layer 5: agent and surfaces ----------------------------------------
    band(ax, 1, 1.5, 98, 17.5, "5  AGENT + DELIVERY SURFACES")
    agent = box(ax, 3.5, 2.8, 26, 10.6,
                "ReAct AGENT (MCP tools)\nSQL_Generator\nSpatial_Visualizer\n"
                "Warehouse_Mutator", fs=7.2)
    gates = box(ax, 32, 2.8, 20, 10.6, "SIX GATES\nsee Figure 3\ngates 5 + 6 "
                "are\nidentification gates", edge=ORANGE, face="#fdf0ea",
                fs=7.2)
    opview = box(ax, 54.5, 2.8, 20, 10.6, "OPERATOR VIEW\nranked bundles\n"
                 "NPV bands\nSHAP drilldown", fs=7.2)
    pubview = box(ax, 77, 2.8, 20, 10.6, "PUBLIC PLANNING VIEW\n"
                  "propensity score\ntiming window\nEJ burden overlay",
                  edge=ORANGE, face="#fdf0ea", fs=7.2)
    for a, b in ((agent, gates), (gates, opview), (opview, pubview)):
        link(ax, a, b)
    link(ax, rank, opview, sides=("b", "t"), fracs=(0.5, 0.4))

    ax.set_title("Siting Atlas end-to-end architecture",
                 loc="left", x=0.01, y=1.015)
    caption(ax, "Orange marks the components that carry the contribution. "
                "Every source is public; no licensed panel or API key is "
                "required to reproduce the system.", y=-1.5)
    return save(fig, out, "fig01_architecture")


def fig02_star_schema(out):
    """Kimball star schema centred on the fact table."""
    fig, ax = blank_canvas(9.6, 6.2)

    fact = box(ax, 33, 34, 34, 32,
               "fact_siting_economics\n\n"
               "zcta_id  (FK)\ndate_id  (FK)\nnode_id  (FK)\n"
               "operator_id  (FK)\nscenario_id  (FK)\n\n"
               "enabled_flag\nexpected_volume\ncannibalisation\n"
               "cost_per_package\nnpv_p10 / p50 / p90",
               edge=BLUE, face="#eaf2fc", lw=2.0, fs=7.6, weight="bold")

    dims = [
        ("dim_geography\n\nzcta_id\ngeometry\nmetro\nurban_rural\nEJ_index",
         2, 62, 24, 24, AQUA, SURFACE),
        ("dim_date\n\ndate_id\nquarter\nyear", 2, 26, 24, 15, AQUA, SURFACE),
        ("dim_logistics_node\n\nnode_id\nlat / lon\nfacility_type\nopen_date\n"
         "square_feet", 74, 62, 24, 24, ORANGE, "#fdf0ea"),
        ("dim_operator\n\noperator_id\nname\nnetwork_tier",
         74, 38, 24, 16, ORANGE, "#fdf0ea"),
        ("dim_scenario\n\nscenario_id\nW_version\nmutation_id\nseed",
         74, 12, 24, 19, ORANGE, "#fdf0ea"),
    ]
    for label, x, y, w, h, edge, face in dims:
        r = box(ax, x, y, w, h, label, edge=edge, face=face, fs=7.0,
                align="left")
        link(ax, r, fact, color=AXIS, style="-")

    box(ax, 2, 2, 62, 8,
        "WHY dim_scenario MATTERS:  every agent mutation of W creates a "
        "scenario row, so any\npublished number can be replayed exactly "
        "-  which W, which mutation, which seed.",
        edge=ORANGE, face="#fdf0ea", fs=7.2, align="left")

    ax.set_title("DuckDB star schema", loc="left", x=0.01, y=1.01)
    return save(fig, out, "fig02_star_schema")


def fig03_agent_gates(out):
    """ReAct loop and the six-gate mutation path."""
    fig, ax = blank_canvas(10.6, 6.4)

    band(ax, 1, 66, 44, 31, "ReAct LOOP")
    steps = []
    for i, (lab, y) in enumerate([("THOUGHT", 86), ("ACTION", 78),
                                  ("OBSERVATION", 70)]):
        steps.append(box(ax, 6, y, 34, 6.4, lab, fs=8, weight="bold",
                         face=SEQ[i], edge=BLUE, color=INK))
    link(ax, steps[0], steps[1])
    link(ax, steps[1], steps[2])
    arrow(ax, steps[2].right, steps[0].right, rad=-0.55, color=MUTED)
    ax.text(46.8, 81, "loop", fontsize=7, color=MUTED, va="center")

    band(ax, 49, 66, 50, 31, "MCP TOOL SURFACE")
    tools = []
    for lab, y, edge, face, wt in (
            ("SQL_Generator          read-only", 86, BLUE, SURFACE, "normal"),
            ("Spatial_Visualizer     read-only", 78, BLUE, SURFACE, "normal"),
            ("Warehouse_Mutator          WRITE", 70, CRITICAL, "#fbeaea",
             "bold")):
        tools.append(box(ax, 52, y, 44, 6.4, lab, fs=7.6, align="left",
                         edge=edge, face=face, weight=wt))
    link(ax, steps[1], tools[1])

    ax.text(50, 62, "A PROPOSED WRITE MUST CLEAR SIX GATES", ha="center",
            fontsize=9, fontweight="bold", color=INK)

    gates = []
    for i, (n, lab) in enumerate([("1", "Schema\nconformance"),
                                  ("2", "Geocoding\nreachability"),
                                  ("3", "Confidence\nthreshold"),
                                  ("4", "Audit-log\nimmutability")]):
        gates.append(box(ax, 3 + i * 17.4, 46, 15.4, 11, f"GATE {n}\n{lab}",
                         fs=7.2, edge=BLUE))
    for i, (n, lab) in enumerate([("5", "Donor-pool\nintegrity"),
                                  ("6", "Estimate\nstability")]):
        gates.append(box(ax, 72 + i * 14.6, 46, 13, 11, f"GATE {n}\n{lab}",
                         fs=7.2, edge=ORANGE, face="#fdf0ea", weight="bold"))
    for a, b in zip(gates, gates[1:]):
        link(ax, a, b)

    ax.text(35.5, 42.6, "DATA INTEGRITY  -  prior art exists", ha="center",
            fontsize=7.4, color=INK_2, style="italic")
    ax.text(85.5, 42.6, "IDENTIFICATION INTEGRITY  -  new", ha="center",
            fontsize=7.4, color=ORANGE, fontweight="bold")
    newtag(ax, 76, 58.4, "THE CONTRIBUTION")

    why = box(ax, 3, 18, 45, 21,
              "WHY GATES 1-4 ARE NOT ENOUGH\n\n"
              "A write can be schema-valid, correctly geocoded,\n"
              "high-confidence and fully logged  -  and still\n"
              "change W  ->  the donor pool  ->  theta  ->  NPV\n"
              "by millions.\n\n"
              "The data is fine. The inference is broken.",
              edge=CRITICAL, face="#fbeaea", fs=7.2, align="left")
    what = box(ax, 52, 18, 45, 21,
               "WHAT GATES 5 AND 6 DO\n\n"
               "5   does this move a control unit into treatment?\n"
               "      if yes -> recompute the donor pool and flag\n\n"
               "6   re-run theta with and without the mutation\n"
               "      if |d theta| > pre-registered threshold\n"
               "      -> escalate to a human, always",
               edge=ORANGE, face="#fdf0ea", fs=7.2, align="left")
    hitl = box(ax, 26, 3, 48, 11,
               "HITL_REQUIRED  =  ON for any public demo\n"
               "Every passing mutation still surfaces a diff card\n"
               "requiring an explicit human apply.",
               edge=GOOD, face="#eaf7ea", fs=7.6)
    link(ax, why, hitl, sides=("b", "t"), fracs=(0.5, 0.25))
    link(ax, what, hitl, sides=("b", "t"), fracs=(0.5, 0.75))

    ax.set_title("Agent loop and the six-gate mutation path",
                 loc="left", x=0.01, y=1.01)
    return save(fig, out, "fig03_agent_gates")


BUILDERS = [fig01_architecture, fig02_star_schema, fig03_agent_gates]
