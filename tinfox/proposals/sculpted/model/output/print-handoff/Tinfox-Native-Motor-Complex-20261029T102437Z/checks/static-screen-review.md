# Corrected motor-complex static review

The corrected detached motor complex has no unresolved nominal material
interference in its exported assembly pose. This conclusion applies to the
121-solid native assembly STEP with SHA-256
`ca629df49d3b28a17cff81ebc2a0bef398e9e46868fc2d76f970445e2c9e850b`.
It is a supported, unpowered fit prototype, with no operating-strength or
loaded-motion qualification.

The exported solids bind uniquely to the native inventory through placed
bounds, volume and semantic component labels. The inventory contains thirteen
custom parts, eight cut-stock bodies and one hundred purchased references.
The purchased references include three motors and twenty-four connector bodies.

The independent screen considers all 7,260 possible pairs. Bounding boxes
eliminate 6,787 disjoint pairs. Exact Boolean checks cover the remaining 473
pairs without excluding categories or groups. Fifty-seven pairs contain
positive reference volume:

- Forty-five motor screws enter motor reference solids whose threaded holes
  are not modeled. Each measured shaft volume and axial interval matches its
  specific documented mounting interface and nominal penetration.
- Twelve protective boot envelopes deliberately enclose part of their own
  port's plug or cable reference. Their individual labels, overlap volumes
  and bounds are retained.

No custom/custom or fastener/fastener material interference remains unresolved.
The original neutral tie/head contact and three-lobe hub/motor contact are
eliminated in this assembly. The separate revised-part reports retain their
original measurements and the corrective geometry checks.

One external kernel operation needs an explicit qualification. The coincident
inner/outer thigh split returns an invalid Common in the primary local check
and two non-destructive retries. Those failures remain recorded. A targeted
saved-native check excludes coincident faces, finds zero material interference
and successfully subtracts the halves in both directions without changing
volume, face count or edge count. The saved-reopen audit binds that native
geometry to the exported checkpoint. This resolution applies only to that
identified pair.

The [classified report](native-bench-static-classification.json) retains the
exact source hashes, identity evidence, each accepted intersection, original
kernel failure and native resolution. The [raw screen](native-bench-static-screen.json)
retains all 473 exact-check results. Native physical-property values and
independent STEP integration are distinct methods; they are not treated as
numerically interchangeable.

Manufacturing tolerances, flexible cables, print orientation, physical motor
threads, clamp preload, bearing fits, polymer creep and loaded motion remain
separate qualification tasks. This static review does not establish complete
CNC tool access or authorize powered operation.
