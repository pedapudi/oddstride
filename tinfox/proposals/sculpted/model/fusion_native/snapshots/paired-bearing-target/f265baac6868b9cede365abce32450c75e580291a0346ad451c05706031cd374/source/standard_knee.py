"""M5 knee retention study retaining the 12 mm load-carrying axle diameter."""
import build as b

PARAMETERS=dict(knee_retainer_thread_mm=5,knee_retainer_pitch_mm=.8,
    knee_retainer_length_mm=55,knee_axle_od_mm=12,knee_axle_id_mm=5.5,
    knee_axle_length_mm=44.6,knee_retainer_washer_od_mm=15,
    knee_retainer_washer_id_mm=5.3,knee_retainer_washer_thickness_mm=1.2,
    knee_retention_load_qualified=False)

def parts():
    p=PARAMETERS
    return dict(
        knee_axle=b.ring(p['knee_axle_od_mm']/2,p['knee_axle_id_mm']/2,p['knee_axle_length_mm'],49.4,-170),
        axle_bolt=b.cyl(2.5,55,(0,48.2,-170)).fuse(b.cyl(4.75,2.75,(0,45.45,-170))),
        axle_nut=b.hex_nut(8,4,0,95.2,-170,2.5),
        axle_washer_inner=b.ring(7.5,2.65,1.2,48.2,-170),
        axle_washer_outer=b.ring(7.5,2.65,1.2,94,-170))

def thigh_inner():
    # Open the existing outer-face recess to receive the standard large washer.
    # Use the current washer-seat shell, rather than the older source lookup.
    import cadquery as cq
    from kinematics import ROOT
    s=cq.importers.importStep(str(ROOT/'output/clamp-seat-work/step/thigh_inner.step')).val()
    return s.cut(b.cyl(7.7,8,(0,41.4,-170))).clean()

def thigh_outer():
    import cadquery as cq
    from kinematics import ROOT
    s=cq.importers.importStep(str(ROOT/'output/clamp-seat-work/step/thigh_outer.step')).val()
    return s.cut(b.cyl(7.7,16,(0,94,-170))).clean()
