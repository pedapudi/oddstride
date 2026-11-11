# Proposal B visual iterations

The target is the unchanged precision-instrument studio image in `../studio-reference.png`.
Every numbered image renders the CAD meshes from the fingerprint in its adjacent provenance file.

| Pass | Observed mismatch | Geometry correction in the following pass |
| --- | --- | --- |
| 01 | The mirrored battery panel appeared on the roof; flat cone feet stood on edges; the nose face stood proud. | Corrected the panel plane, used spherical lower soles and replaced the plate with a recessed service face. |
| 02 | The cap engraving looked almost horizontal; shin channels ended abruptly; the sensor face remained narrow. | Changed the local engraving angle, rounded channel ends and developed an enclosing nose rim. |
| 03 | The nose surround entered the hip sweep; shoulders grazed the roof; feet lacked a distinct boot. | Moved the wide sensor face forward, raised only the shoulder crowns and added roll-carried annular cowls and larger spherical boot soles. |
| 04 | The larger cowl approached rail ends and bearing-mount ears too closely. | Shortened each rail by 2 mm, reduced the cowl outside diameter to 104.4 mm and preserved the 50.3 mm inside radius around the rotating cradle. |
| 05 | Rotating the complete boot to level its sole moved the upper neck ahead of the shin. | Kept the spherical sole orientation and lofted an asymmetric upper boot to a neck on the shin centerline. |
| 06 | The shin bowed behind the knee-to-foot chord; the reference bows forward. Its structural ankle extended too far into the boot. | Reversed the midshaft offset from −9 mm to +13 mm, narrowed the waist to 20 mm, returned the collar to the fixed foot axis and shortened the structural shin to 136 mm below the knee. The internal cavity and rounded channel follow the new sweep. |
| 07 | The shin sweep now follows the reference direction and tapers into a distinct ankle neck. | Retained the knee and foot centers. Recovered the lower curve earlier to clear the thigh in full fold, reduced upper transverse depth by 1 mm and made the groove shallower to retain its wall above the internal cavity. Rechecked motion, structural sections and torque estimates. |
| 08 | The pronounced S profile and ankle recovery made the limb unnecessarily complex. | Replaced it with one analytic 3 mm bow and continuous taper; slimmed the thigh web and simplified the circular knee. A 16 mm lower cavity removes 4.96 g per paired shin relative to the first 10 mm cavity trial. Updated torque, inertia, section and clearance comparisons record the tradeoffs. |

| 09 | The front was a detached stepped frame with clipped corners and a high undulating crown. | Unified the nose and torso envelope, lowered the crown by 3 mm, rounded front corners to nominal 18 mm, widened the sensor opening to 168 mm, recessed layered optics and rounded battery-panel edges. A roof return tongue and four fascia posts provide actual attachment paths. All approved limb meshes remain unchanged. |

Passes 01–03 use the neutral [0°, 30°, −60°] pose. Passes 04–09 use the shared
studio [0°, 45°, −75°] pose. The final shared review compares both proposals and
the baseline in the latter pose, so a pose change is not counted as a geometry gain.

The local crowns and shoulder articulation remain visibly different from the
illustration. Flexible seals, cables, exact battery adapters and loaded behavior
remain unqualified. The CAD preserves the real motor and joint envelopes.

The [side-profile overlay](../13-shin-profile.svg) projects both structural halves from the previous and revised CAD. Its filled paths are the union of projected mesh triangles, simplified within 0.03 mm. Dashed lines join the actual loft stations; the knee and foot centers define the unchanged reference chord.

The current refinement follows pass 09. Its [front detail](../15-body-detail.png)
shows a compound-curved fascia and matching bezel. The center roof separates from
the side panels for printing. Thigh edges are softer, and the shin uses a single
3.5 mm bow. The [preceding geometry](refinement-baseline/12-studio-view.png) and its
source snapshot are retained for comparison. All individual STEP exports now
undergo a solid-topology and volume round-trip check.

The [whole-limb comparison](../14-limb-profile.svg) overlays the preceding and
current geometry in open and folded poses. Hip, knee and foot centers and motor
interfaces remain unchanged. The sampled thigh section modulus decreases by
about 0.3% and the shin section modulus by about 8.8%. These geometric comparisons
do not qualify printed strength; the engineering report records the load screens.

The subsequent assembly pass increases the face crown to 8 mm and replaces the
vertical fourth-power profile with a quadratic curve. The preceding face is
preserved in [the assembly baseline](assembly-baseline/15-body-detail.png).
Roof bosses clear the side panels during lifting, locating tabs replace four
lower cover screws, and the battery guides are integral with the cassette.
The [assembly review](http://127.0.0.1:8768/review/assembly.html) shows the tray and
cassette removal sequence. Its shared attachment requires supporting the cassette
during tray service. The assembly report records the tested paths and tool sizes.
