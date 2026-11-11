
All-metal custom limb parts
Estimated whole-robot base mass: 14.239 kg.
Custom limb parts across all four legs: 4.279 kg.
Material-specific relief saves 0.513 kg versus unreduced shapes in the same material.
With 1 kg cargo: 15.239 kg.

TINFOX LIMB CONSTRUCTION STUDIES

Scope
The printed route is the first unloaded fit and hand-articulation prototype.
Printed forks, bearing seats and motor carriers have no qualified load rating.
All routes use purchased motors, metal shafts, bearings, bushes and fasteners.
The printed route includes a widened plastic pushrod for unloaded fit checks.
Hybrid and CNC routes use a steel pushrod. The rest of the robot is shared.

Structural parts and service
Each thigh has two structural halves. Its inner half houses the knee motor;
the outer half includes the service ring and motor face. Each shin has two
fore/aft structural halves with integral bearing seats and pushrod rocker.
Opening the split releases the bearings radially. There is no internal bearing
housing, separate knee head, or blind pocket to press a bearing through.
Two M4 x 20 screws close each shin against hard mating lands. Captive sleeves
and nuts simplify service. Install the M5 pivot nut through its side-loading
pocket before closing the shell. Check bore roundness and free rotation.
The knee axle uses a 12 OD x 8.4 ID x 45.1 mm precision sleeve, recessed M8 x 60
button-head screw and outboard flange nut. Preload and bearing fits need testing.
Remove the pushrod pivot, axle retention and sleeve before opening the shin.

Printed carrier
The printed carrier has two parts: a roll trunnion and a perpendicular hip flange
with integral shroud. A broad key and two M4 x 16 button-head screws join them.
The 5 mm flange prints with its motor face parallel to the bed. The trunnion
prints with its roll axis vertical. Metal carriers remain one piece.
The shroud belongs to the roll carrier; the thigh rotates independently in pitch.

Printing
Use the oriented print-STLs, resting at Z=0. The planning envelope is
305 x 300 x 315 mm. All structural limb lengths lie in the bed plane.
Thigh cavities face upward with their pitch axes vertical. Shin halves lie on
opposite curved exteriors, with their fore/aft split faces upward and bearing
axes horizontal. Local support or a shaped cradle may be needed below curves.
Inspect layer previews for support removal, bearing seats and thin webs.
Start with dry PETG, ample perimeters and dense local material at holes and roots.
Solid infill does not establish strength, thermal resistance or creep life.
Print fit coupons and one front-left assembly before the complete set.

Machining
Metal variants have relief in the thigh cradle, service collar, motor face,
hubs and carrier. Critical roots, bearing seats and closure lands retain material.
These are weight-reduced candidates, not stress-optimized production parts.
Machine open shells from the split face and finish curves in a second setup.
Carrier elbows need indexed setups. Finish critical split bores with the mating
halves fixed against their stops; obtain a shop review of tolerances and fixtures.
SendCutSend lists a standard +/-0.005 inch CNC tolerance and no custom tolerancing.
Precision bearing and shaft fits need drawing-controlled finishing elsewhere.
Source: https://sendcutsend.com/guidelines/cnc-machining/

US hardware sourcing
Amazon.com is the default for ordinary matching fasteners. Use McMaster-Carr,
Fastenal or US manufacturer stores for precision interfaces. Lowe's is a local
fallback. The hardware shortlist distinguishes measured dimensions from candidates;
stock, delivery, material certification and fit are not guaranteed.
6001-2RS bearings: https://littlemachineshop.com/products/bearing-6001-2rs
Flanged bushes: https://www.igus.com/iglide-ibh/flange-bearings/product-details/iglide-g-m?artnr=GFM-0608-04
M4 x 20 screw candidate: https://www.amazon.com/dp/B0DYSQZHC9
Shoulder screws: https://www.mcmaster.com/products/shoulder-screws/fastener-head-type~socket/material~steel-2/
The CAD shoulder screw has a 6 x 20 mm shoulder and M5 x 6 mm thread. Catalog
94361A525 has a 5 mm thread; 92981A103 has a 10 mm thread. Neither is approved
without an engagement and motor-clearance check. The rod and sleeves need finishing.

Motor interfaces and remaining work
RS-02 stators use nine M3 positions on a 73 mm circle; outputs use six M4 positions
on a 24 mm circle. Select screw lengths from actual clamp stacks and delivered
motor thread depths. Low-head output screws require separate clearance checks.
Source: https://robstride.com/products/robStride02
Roll-bearing retainers, motor ties, foot attachment, cable routing, fastener
engagement and axle preload remain unfinished. Printed carrier, forks and bearing
lands need temperature, creep, fatigue and impact qualification before loaded use.

Verification
Custom STEP files reopen as single valid solids. Printed meshes are watertight
and fit the planning envelope. Eight reference poses are checked for each variant.
This does not prove clearance during every motion or qualify physical strength.
Mass estimates use solid CAD volume. Torque screens use prescribed force cases,
not gait simulation. Additional cargo is 1 kg; the robot remains above 10 kg.
