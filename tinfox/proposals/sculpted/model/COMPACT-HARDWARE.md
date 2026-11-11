# Conventional hardware in the revised limb

The CAD candidate uses conventional shoulder screws with their heads facing
inward and captured nuts facing outward. The fork geometry accommodates the
longer threads. It no longer depends on the special low-profile 18 mm shoulder
screw. Inventory quantities remain unverified; this is a modeled specification,
not a purchase list with confirmed delivery.

| Location | Modeled specification | Quantity |
| --- | --- | ---: |
| Pushrod pivots | 6 mm diameter × 20 mm shoulder; M5 × 0.8 thread, 9.75 mm long; head 10 mm diameter × 4.5 mm high | 8 |
| Pivot nuts | M5 hex nut, 8 mm across flats, 4 mm high, captured in integral outer fork | 8 |
| Knee axle | M8 × 55 ISO 7380-1 class 10.9 button head; full-height flange nut and metal axle sleeve | 4 |
| Shin clamps | M4 × 25 ISO 7380 button head with captured M4 nut and 18 mm compression sleeve | 8 |
| Rear thigh clamp | Same M4 screw, nut and sleeve dimensions as the shin clamps | 4 |
| Camera hood root | M3 × 16 button head and captured M3 nut | 2 |
| Camera saddle | M3 × 10 button head through the front rail joints | 4 |

The pivot envelope follows [Bolt Depot 14232](https://boltdepot.com/Product-Details?product=14232).
The shoulder spans both fork ears and the rod bushings. The head seats in the
inner ear; the nut seats in the outer ear. Both ears provide about 5.8 mm of
nominal shoulder support. The longer thread stays inside the revised thigh
clearance pocket. Four input-crank nuts are added to the assembly.

The axle matches [BelMetric SB8X55CLZ](https://belmetric.com/content/A-PDF_Drawings/SB8X55CLZ.pdf).
Its threaded shank passes through the existing metal axle sleeve. The screw tip
projects 1.9 mm beyond the nominal nut envelope. Shin screws retain their reversed
orientation: the low button heads face the body and the nuts sit outside.

## Assemble the pivots before closing the thigh

1. Press the replaceable bushings into the pushrod eyes.
2. Place the rod between the fork ears. Insert the shoulder screws from the inner
   side and place the M5 nuts in the outer pockets.
3. Assemble the input crank and pushrod before attaching the crank to the motor.
   The motor mounting plate restricts inward-facing driver access after assembly.
4. Fit the knee axle and shin, then close the thigh halves. Bearing extraction
   still requires separation of the shin halves and removal of the thigh cheeks.

Flat head seats and compression sleeves limit compression of the printed parts.
Actual tightening torque, locking method, printed creep and fatigue require
qualification. The geometry checks use smooth dimensional envelopes; they do
not simulate thread engagement or bolt preload.

## Broad supply must be established before purchasing

Supplier dimensions and public listings were checked on 2026-10-25.
Bolt Depot offers the pivot individually and in bags and bulk packages.
[MF Supply lists Holo-Krome 09005](https://www.mfsupply.com/HOLO_KROME_09005_p/hol09005.htm)
in the same nominal shoulder/thread family, but requests contact for availability.
Its full dimensions must be compared before treating it as interchangeable.
Package sizes and catalog entries do not establish on-hand inventory.

M8 × 55 class 10.9 button heads are also listed by
[Fastener Mart](https://www.fastenermart.com/iso-7380-button-head-socket-cap-screws.html?CatListingOffset=325&Offset=325&Per_Page=25&Sort_By=disp_order),
including zinc-plated SHR664-645. Ordinary M3/M4 fasteners can come from US
suppliers or Amazon.com when the exact standard, material, dimensions and grade
match. Stock and delivery must be checked for the robot plus replacement parts.

If conventional shoulder screws cannot meet the supply requirement, the fallback
is an ordinary bolt through a smooth steel sleeve. That adds one part per pivot
and requires a verified journal tolerance and clamp-length stack. This fallback
has not been modeled. Do not use screw threads as the rotating bearing surface.

The previous substitution study retains the former screw orientation and shows
why a direct swap collided. The current assembly audit evaluates the reversed
screws and revised forks. Neither study establishes structural strength.
