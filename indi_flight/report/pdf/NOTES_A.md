# Notes A: template, build script, introduction and background

## Template choices
- `scrreprt`, 11 pt, A4, one-sided. LuaLaTeX with fontspec; Libertinus Serif/Sans/Mono and Libertinus Math exist in this TeX Live, so they are used (fallback to Latin Modern is coded in the preamble).
- `unicode-math` is loaded; `amssymb` is NOT loaded (it clashes with unicode-math: `\eth` already defined). Bold math vectors: `\vect{...}` = `\symbf{...}`.
- Headings, captions labels, links in `indiblue`; palette defined as in the task (HTML model).
- Headers: chapter mark left, page number right, rule in `indiblue`. `\automark[section]{chapter}`.
- cleveref with `capitalise,nameinlink`; equations referenced as "Equation (n)".
- Numbering: equations, figures and tables restart in each chapter (`\numberwithin`, `\counterwithin`).

## Macros (preamble.tex)
- `\param{MC_INDI_EN}`, `\topic{...}`, `\module{...}`: monospace, a break is allowed after each underscore (expl3 replacement of the catcode-8 underscore).
- `\indidiagram{name}{caption}{label}`: figure that inputs `diagrams/name.tex`, else framed placeholder.
- `\indifigure{name}{caption}{label}`: figure with `figures/name.pdf` at `\linewidth`, else placeholder. Name without extension.
- Boxes: `keyresult` (title "Key result" or an argument), `indinote`. Verdict macros `\passed`, `\notpassed`.
- Notation macros: `\vect`, `\ts` (T_s), `\fc` (f_c), `\aref`, `\Omax`. Column types `L{w}`, `Y`.
- Diagrams are shrunk to `\linewidth` only if wider (adjustbox `max width`); they are never enlarged.
- `diagrams/diagram_style.tex` is loaded if present (after the tikz libraries).

## Build
- `build.sh [--no-figs]`: runs `bench/report_figs/make_all.sh` when it exists, then `latexmk -lualatex -interaction=nonstopmode -halt-on-error -outdir=build main.tex`, then copies `build/main.pdf` to `indi_report.pdf`. `build/chapters/` is created first because `\include` writes aux files there.

## Content decisions
- Acceptance criteria are called C1-C8 (Cn = Gn); the verdict table in the introduction has one line of meaning each. Verdicts as given in the task.
- Chapters 03-09 and appendices A, B are stubs with labels `ch:inner_loop`, `ch:outer_loop`, `ch:analysis`, `ch:validation`, `ch:limits`, `ch:bringup`, `ch:conclusion`, `ch:parameters`, `ch:traceability`. Other labels used by my chapters: `sec:airframe`, `sec:criteria`, `tab:criteria`, `eq:plant`, `eq:increment`, `eq:indi_law`, `eq:nu`, `eq:actuator`, `eq:u_state`, `fig:architecture`.
- The architecture diagram is `\indidiagram{architecture}` in chapter 2.

## Numbers and their sources
- Abstract: PM 49.1 deg (outer, worst), rate spot PM 46.9 deg, limit 45 deg: report 03_validation.md section 3.2 table; 300 runs, 79 of 297 oscillation, 2 Hz pitch, weak-motor corner: 03_validation.md 3.3 and 04_limits.md 4.1.
- Airframe table: design/ref_airframe_model.md (mass 0.610 kg, inertia, 0.0795 m, k_T, k_Q/k_T, 2700 rad/s, 33 ms, J_r 5e-6 assumed, 14 poles, hover 999 rad/s and u 0.137) and bench/params/quad5in_indi_defaults.params (G1 1757, 1640, 205); controller rates 800, 400, 266.7 Hz from report 01 section 1.

## Unverified
- Units in the airframe table (kg m^2 for inertia, k_T without unit) are inferred; the source table gives numbers only. k_T unit left out on purpose.
- "About 999 rad/s" hover speed is "w_h ~999" in the source.
- Claim that the maximum rotor speed 2700 rad/s is `MC_INDI_W_MAX` (default of the quad5in parameter set).
- Introduction claim that the method "has been flown" on aircraft, micro air vehicles and aggressive quadrotor flight is from the cited literature titles, not re-read.
- Statement in the background that the controllers refuse to arm without rotor telemetry or rotor geometry: from the G7 and G8 verdict notes (arming check).
- Sample rates listed as "used in tests": 800, 400 and 266.7 Hz (report 01, section 1: "bench rates").
