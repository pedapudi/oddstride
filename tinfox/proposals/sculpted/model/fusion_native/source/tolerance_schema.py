"""Fit semantics and interval checks for native Fusion tolerance parameters.

Allowances change the target geometry. Manufacturing tolerances describe its
permitted variation. Process compensation requires measured calibration; zero
does not mean the printer or mill is exact. No values here qualify a fit.
"""
import json
from pathlib import Path

INTERFACES = [
    {'interface':'Knee bearing outer race', 'nominal_parameters':['lc_bearing_od'],
     'allowance_basis':'diametral', 'finished_expression':'lc_bearing_od + bearing_seat_diametral_allowance + hole_process_compensation',
     'legacy_binding':'lc_bearing_fit_allowance = (bearing_seat_diametral_allowance + hole_process_compensation)/2',
     'checks':['both complete seats follow together','outer-race shoulders and extraction paths remain intact','minimum radial wall survives largest seat']},
    {'interface':'Knee axle and inner races', 'nominal_parameters':['lc_bearing_id','axle_outer_diameter'],
     'allowance_basis':'diametral', 'checks':['actual bearing ID versus axle OD interval','fixed axle datum','assembly sliding and removal']},
    {'interface':'Thigh axle clearance', 'nominal_parameters':['axle_outer_diameter'],
     'allowance_basis':'diametral', 'checks':['clearance bores follow axle nominal plus independent hole allowance','bearing ID remains independent']},
    {'interface':'Bearing inner-race spacer', 'allowance_basis':'axial',
     'finished_expression':'outer_bearing_near_face - inner_bearing_far_face + spacer_length_adjustment',
     'checks':['maximum and minimum inner-race clamp stack','outer-race retention independently checked','no assumed print shrinkage compensation in metal spacer']},
    {'interface':'Six millimeter shoulder pin and rod bushings', 'allowance_basis':'diametral',
     'checks':['pin shoulder nominal separated from M5 thread nominal','bushing ID and OD tolerances treated independently','pin journal hole clearance preserved']},
    {'interface':'Pushrod fork axial stack', 'allowance_basis':'axial',
     'finished_expression':'rod_thickness + near_bushing_flange + far_bushing_flange + fork_total_side_clearance',
     'checks':['tightest fork versus widest rod/flange stack','both crank and integral shin eye','pin shoulder length and thread engagement']},
    {'interface':'M3 and M4 mounting holes', 'allowance_basis':'diametral',
     'checks':['nominal screw diameter plus hole clearance','bolt-circle dimensions fixed','head diameter and head-depth allowances independent']},
    {'interface':'Captured hex nuts', 'allowance_basis':'total across-flats',
     'checks':['nut nominal AF plus total AF allowance','pocket depth independent','accessible insertion and wrench path','remaining boss ligament']},
    {'interface':'Motor pilot and flange', 'allowance_basis':'diametral and axial separately',
     'checks':['verified vendor nominal required','pilot clearance independent of motor body envelope','flange seating and mounting-hole position stack','no uniform scaling']},
    {'interface':'Motor housing', 'allowance_basis':'radial or diametral explicitly named',
     'checks':['housing radius = motor case nominal diameter/2 + radial case clearance','socket insertion and cooling space','mounting flange carries clamp loads']},
    {'interface':'Structural shell seam', 'allowance_basis':'total normal gap',
     'checks':['each mating face relieved by half total gap','do not translate whole half or bearing datums','compression sleeve clamp stack remains correct']},
    {'interface':'Locating features', 'allowance_basis':'total pocket-minus-tongue clearance',
     'checks':['both mating profiles reference one tongue nominal','lead-in independently controlled','tool access and hand assembly','no new tolerance-critical tiny pins']},
    {'interface':'Motor connectors', 'allowance_basis':'per-side and axial separately',
     'checks':['physical plug envelope independent of insertion clearance','housing opening follows connector envelope plus allowance','assembly travel and cable bend corridor']},
    {'interface':'Moving rigid parts', 'allowance_basis':'minimum surface gap',
     'checks':['worst directional position and angular error','shaft or joint play and manufacturing variation','deflection budget reported separately','full stated sampled motion range']},
    {'interface':'Equal-crank linkage closure', 'allowance_basis':'center distance and hole position',
     'checks':['shared nominal crank radius and link length','independent realized dimensional errors','tight and loose pivot fits','no dead-center or newly binding pose']},
]

PROCESS_RULES = {
    'reference': 'Preserve the audited source geometry for translation checks.',
    'printed': 'Separate hole, external-size and seam compensation parameters. Start unqualified until material, orientation and printer coupons are measured.',
    'cnc': 'Separate desired fit allowances and drawing tolerances. Use supplier-confirmed fits; tool compensation is not a universal CAD offset.',
    'shared': 'Nominal hardware, bolt circles and kinematic datums do not scale with robot size. Model expressions and interval evidence must use the same units and allowance convention.',
}


def difference_interval(container_nominal, container_minus, container_plus,
                        insert_nominal, insert_minus, insert_plus):
    """Clearance interval; negative values represent interference.

    The minus/plus inputs are nonnegative manufacturing deviations in the same
    length units as the two nominal dimensions. Do not use statistical RSS for
    this deterministic worst-case check.
    """
    values=[container_minus,container_plus,insert_minus,insert_plus]
    if any(v<0 for v in values):raise ValueError('Deviation magnitudes must be nonnegative')
    return {'minimum':container_nominal-container_minus-insert_nominal-insert_plus,
            'maximum':container_nominal+container_plus-insert_nominal+insert_minus}


def axial_stack_interval(dimensions):
    """Sum (nominal, minus, plus) stack dimensions without shared-error reuse."""
    if any(lo<0 or hi<0 for _,lo,hi in dimensions):raise ValueError('Deviation magnitudes must be nonnegative')
    return {'nominal':sum(n for n,_,_ in dimensions),
            'minimum':sum(n-lo for n,lo,_ in dimensions),
            'maximum':sum(n+hi for n,_,hi in dimensions)}


if __name__=='__main__':
    # Arithmetic checks use illustrative dimensions, not selected robot fits.
    assert abs(difference_interval(10,.1,.2,9,.05,.15)['minimum']-.75)<1e-12
    assert abs(difference_interval(10,.1,.2,9,.05,.15)['maximum']-1.25)<1e-12
    assert axial_stack_interval([(8,.01,.02),(16,.02,.03),(8,.01,.02)])=={'nominal':32,'minimum':31.96,'maximum':32.07}
    target=Path(__file__).resolve().parents[1]/'manifests/tolerance-plan.json'
    target.write_text(json.dumps({'interfaces':INTERFACES,'process_rules':PROCESS_RULES,
        'native_bindings_complete':False,'physical_fit_qualified':False,
        'status':'Implementation specification; native binding/edit evidence is required separately.'},indent=2))
    print('Tolerance semantics and interval arithmetic checked; specification saved.')
