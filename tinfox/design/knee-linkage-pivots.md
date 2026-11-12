# Knee linkage pivots and test pushrod

Saved in Fusion as `Tinfox - Leg module` v41, referenced by `Tinfox` v66 (2026-11-12).
All four legs use the same shared components; right-hand parts are mirrored copies.

## What changed

| Item | Before (Leg v40) | Now (Leg v41) |
|---|---|---|
| Pivot pin, crank and shin | M5 shoulder screw, 6 mm shoulder, M5 nut | ISO 4762 M4x25 through a 6 OD x 4 ID 6063 tube sleeve cut to 18.6 mm, M4 nylock held in a hex pocket |
| Fork gap | 8.4 mm | 8.75 mm (6.35 mm plate, two 1 mm bushing flanges, 0.4 mm clearance) |
| Fork seat floors | 20 mm apart | 18.6 mm apart, so the M4x25 passes the nylock by about 1.4 mm |
| Pushrod for first builds | printed 6 x 6 mm flat link | M6 threaded rod cut to 157 mm with two identical printed eyes |
| Pushrod for CNC builds | 6 mm flat link | 6.35 mm (0.250 in) flat plate with flanged bushings, same forks |
| Link taper clearance | 12 mm | 26 mm, which also clears the printed eye neck |

The screw clamps the sleeve, not the printed fork. Each fork cheek carries the sleeve
on 4.9 mm of 6.1 mm bore.

The printed eye is 8.35 mm thick with a 15 mm eye, a 6.1 mm bore that runs on the
sleeve, and a 9.5 mm wide neck 18 mm long. The rod enters a 5 mm hole 12 mm deep:
tap it M6 x 1, or drive the rod in with epoxy. Set the eye spacing to 170.0 mm
before the adhesive cures.

Parameters: `fit_pivot_sleeve_length`, `fit_pivot_sleeve_nominal_od`,
`fit_pivot_screw_nominal_diameter`, `fit_pivot_head_nominal_diameter`,
`lc_rod_thickness`, `lc_rod_taper_length`, and the `tp_` family for the test pushrod.

## Why not rod ends

SI6T/K female rod ends were checked first. Their body reaches 30 mm from the pivot,
36 mm with a jam nut. Swept through knee travel it cut into the shin at the knee
bearings and crossed the crank hub screws, and it needed a 13.5 mm fork gap. The
linkage was designed around a 6 mm flat link, so the test pushrod keeps that envelope.

## Loads considered

Earlier audit figures: about 345 N in the pushrod standing and 1.03 kN at peak motor
torque. Hand estimates, pinned ends, 150 mm free length:

| Member | Buckling load |
|---|---|
| Printed 6 x 6 mm PETG-CF link | 74-185 N |
| M6 304 threaded rod | about 2.4 kN |
| 6.35 x 6 mm 6061 plate stem | about 3 kN |

At 1.03 kN the printed eye sees about 20 MPa bearing on the sleeve and 14 MPa on the
net section, and each fork cheek about 18 MPa. These are estimates, not test results.

## Checks

- Feature health: no warnings or errors in the Leg v41 timeline.
- Motion: the placed pushrod bodies were swept against the crank, shin and thigh
  bodies of the front-left leg from 14 degrees beyond full extension to full flexion
  (`lc_knee_max` -48 degrees to `lc_knee_min` -156 degrees) in 2 to 8 degree steps.
  No overlap inside the range; the rod first touches the shin 2 degrees beyond full flexion.
- Visual: side and close-up views of the crank fork and shin fork with the thigh cover hidden.

Not yet verified: printed thread strength, wear of the printed eye on the aluminium
sleeve, right-hand legs by sweep (they share geometry by mirror), and physical knee stops.
