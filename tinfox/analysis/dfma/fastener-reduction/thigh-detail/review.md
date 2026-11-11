# Native thigh mouth and connector-window detail review

The two detail corrections are implemented in the saved native model and independently verified on its final STEP exports. At Z−42 mm, the primary ends at X=0 and the secondary has one continuous section; the former isolated tapered shelf is integrated into that section. Three radial sections confirm the connector-window end at Y46.5 mm and a 3.9 mm band before the tube foot. Both exports contain one valid solid. Exact hashes and checks are in `final-detail-delta.json`.

The findings below document the preceding candidate and explain the two changes. Printing orientation, physical cable bend, preload and operating strength remain unqualified.

## Findings on the preceding candidate

Two small parameter changes will remove fragile detail edges without changing the motor interfaces, fasteners or two-part construction. Keep the primary/secondary split at X=0 down to Z−50 mm, then transition to the existing lower split at Z−70 mm. Shorten the connector window from 38.5 to 36 mm while keeping its Y10.5 start, so its end moves from Y49 to Y46.5 mm.

Coordinates are in the knee motor frame: Y follows the motor axis, +X is the open side of the cradle, and −Z points toward the knee.

This review used the actual exported primary and secondary native solids listed in `review.json`. It covers only the lower motor opening and the connector-window end near the 300° long-screw column. The native owner's existing insertion, closure, motion and driver checks were not repeated.

## Motor-opening edge

The diagonal split currently starts at Z−40 mm and crosses the circular inboard motor barrel. At Z−42 mm, the secondary contains a separate planar section of 16.27 mm² between X6.67 and 17.24 mm, Y9 and 11.14 mm. This is a finite tapered shelf, with maximum axial thickness 2.14 mm. It disappears before the Z−44 mm section. It is therefore more than a sharp silhouette edge.

Moving the split start to Z−50 mm keeps the division at X=0 through the R45.4 inboard barrel. The change reallocates material between the same two parts and avoids this short tapered shelf. The transition to the lower limb remains straight and accessible from the open structural split. Check the updated local sections before acceptance; this report does not describe unexported geometry as corrected.

## Connector-window end

Three radial sections through the 300° column, at tangential offsets −4, 0 and +4 mm, confirm the 1.4 mm band between the current window end Y49 and tube foot Y50.4. This band is not the column's only connection: the column joins the exterior barrel continuously along its 34 mm length. The center section shows approximately 4.25 mm of radial overlap between the R40.25 inner barrel boundary and the column's R44.5 outer extent.

Shortening the window to Y46.5 increases its axial distance from the tube foot to 3.9 mm. It leaves 0.7 mm beyond the modeled cable run ending Y45.8. That modeled margin does not establish clearance for the physical connector, cable bend or strain relief; confirm these on the fit assembly. The edit improves the thin edge without adding a rib, cover or separate mounting piece.

## Manufacturing implications

The taper at the motor opening creates a poor handling edge and an awkward thin feature for a cutter or printed support removal. The revised split should remove it rather than add a fillet to an unnecessarily narrow root. The shorter connector opening retains its existing straight radial tool approach and rounded ends; the changed edge needs no hidden pocket. These local observations do not establish cutter access for every other feature or printed operating strength.

The primary cannot simply be printed on its Y=0 motor flange without support: the lower inner limb is offset near Y47. Review a supported side orientation or a shallow tilt on the final exported primary. The secondary's broad exterior is a candidate bed face. A slicing review is still needed before calling either orientation support-free.

## Evidence

- `sections.json`: exact source hashes and planar section areas/bounds.
- `sections-z.png`: motor-opening sections; orange is primary, blue is secondary.
- `sections-y.png`: axial sections through the motor region.
- `300-root.png`: three local radial sections through the long-screw column.
- `300-root.json`: sampled boundaries of those exact planar sections.

Sections coincident with feature boundaries can include duplicate faces or omit a coincident face in the external Boolean result. In particular, the Z−60 section is not used to infer that secondary material is absent. The quantitative shelf finding uses the noncoincident Z−42 section.
