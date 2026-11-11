"""Regression checks for the exported prototype and its transmission geometry."""
import json, unittest
from pathlib import Path
import numpy as np
import trimesh
from kinematics import ROOT,P,LEGS,POSES,frames,point,rotation
from collision import Checker

class ModelChecks(unittest.TestCase):
    def test_independent_orthogonal_hip_axes(self):
        for leg in LEGS:
            neutral=frames(leg,[0,30,-60]);rolled=frames(leg,[20,30,-60])
            np.testing.assert_allclose(neutral['mount'],rolled['mount'],atol=1e-12)
            roll_axis=rolled['roll'][:3,0]
            pitch_axis=rolled['thigh'][:3,1]
            self.assertAlmostEqual(float(roll_axis@pitch_axis),0,places=10)
            foot0=point(neutral['knee'],[0,P['shin_y']*LEGS[leg][1],-P['shank_to_foot_center']])
            foot1=point(rolled['knee'],[0,P['shin_y']*LEGS[leg][1],-P['shank_to_foot_center']])
            self.assertGreater(abs(foot1[1]-foot0[1]),50)
        data=json.loads((ROOT/'output'/'model.json').read_text())
        self.assertFalse(any('shoulder_fairing' in p['name'] for p in data['parts']))

    def test_parallelogram_closes_through_target_range(self):
        for leg,(_,side) in LEGS.items():
            for roll in [-60,0,60]:
                for knee in np.linspace(*P['joint_limits_deg']['knee'],109):
                    f=frames(leg,[roll,35,float(knee)])
                    input_eye=point(f['crank'],[P['crank_radius'],side*P['rod_y'],0])
                    output_eye=point(f['knee']@rotation('y',P['crank_phase_deg']),[P['crank_radius'],side*P['rod_y'],0])
                    np.testing.assert_allclose(input_eye,point(f['rod'],[0,side*P['rod_y'],0]),atol=1e-9)
                    np.testing.assert_allclose(output_eye,point(f['rod'],[0,side*P['rod_y'],-170]),atol=1e-9)
                    self.assertAlmostEqual(np.linalg.norm(input_eye-output_eye),170,places=8)

    def test_motor_cradle_and_rear_linkage(self):
        import hashlib,math
        stamp=hashlib.sha256((ROOT/'output/model.json').read_bytes()).hexdigest()
        fit=json.loads((ROOT/'output/mounting-fit.json').read_text())
        audit=json.loads((ROOT/'output/mounting-audit.json').read_text())
        self.assertEqual(fit['model_sha256'],stamp)
        self.assertEqual(audit['model_sha256'],stamp)
        self.assertTrue(all(x['intersection_mm3']<1e-4 for x in fit['pairs']))
        motor=next(x for x in fit['pairs'] if x['parts']==['FL_thigh_inner','FL_knee_motor'])
        self.assertGreaterEqual(motor['distance_mm'],.99)
        self.assertEqual(audit['rod_hardware_sweep']['collisions'],[])
        for knee in np.linspace(*P['joint_limits_deg']['knee'],109):
            arm=P['crank_radius']*abs(math.cos(math.radians(knee+P['crank_phase_deg'])))
            self.assertGreaterEqual(arm,12.93)
        tip=rotation('y',P['crank_phase_deg'])@np.array([P['crank_radius'],0,0,1])
        self.assertGreater(tip[2],0,'Rocker attachment must lie above the knee in the shin frame')
        data=json.loads((ROOT/'output/model.json').read_text())
        inner=next(p for p in data['parts'] if p['name']=='FL_thigh_inner')
        self.assertGreater(inner['bounds_mm'][1],57,'Cradle and limb must remain one complete solid')
        outer=next(p for p in data['parts'] if p['name']=='FL_thigh_outer')
        mesh=data['meshes'][outer['mesh']]
        skin=trimesh.Trimesh(vertices=mesh['vertices'],faces=mesh['faces'],process=False)
        root=skin.section(plane_origin=[0,0,-20],plane_normal=[0,0,1])
        waist=skin.section(plane_origin=[0,0,-98],plane_normal=[0,0,1])
        self.assertGreater(root.bounds[1,1]-waist.bounds[1,1],2,'Export must retain the sculpted outer web')
        self.assertLess(root.bounds[1,1]-waist.bounds[1,1],3,'Retain material around the thigh web')
        self.assertLess(waist.bounds[1,0]-waist.bounds[0,0],43,'The thigh contour must retain its slimmer sagittal profile')

    def test_shin_curvature_and_skin(self):
        mesh=trimesh.load_mesh(ROOT/'output/stl/shin_inner.stl')
        def section(z):
            return mesh.section(plane_origin=[0,0,z],plane_normal=[0,0,1]).bounds
        samples=[section(z) for z in range(-35,-146,-10)]
        widths=np.array([b[1,0]-b[0,0] for b in samples])
        centers=np.array([b[:,0].mean() for b in samples])
        self.assertTrue(np.all(np.diff(widths)<.1),'The shin must taper without a distal flare')
        self.assertLess(float(centers.max()),4.5,'The shin uses one shallow arc')
        self.assertGreater(float(centers.max()),2.5)
        self.assertTrue(np.all(np.diff(centers,2)<.1),'The exposed shin must not introduce an S bend')
        audit=json.loads((ROOT/'output/mounting-audit.json').read_text())['shin_skin_audit']
        self.assertGreater(audit['sample_count'],150)
        self.assertGreaterEqual(audit['minimum_sampled_skin_mm'],2.5,'Recessed groove must retain printable skin')
        self.assertTrue(all(b['sagittal_edge_ligament_mm']>=5 for b in audit['bolt_sagittal_edge_ligaments']))

    def test_collision_detector_finds_opposed_leg_interference(self):
        q={l:list(v) for l,v in POSES['stand'].items()};q['FL']=[-60,60,-120];q['FR']=[-60,60,-120]
        hit=Checker().check(q)
        self.assertTrue(hit['collision'])
        self.assertTrue(any(any('FL_shin' in n for n in p) and any('FR_shin' in n for n in p) for p in hit['pairs']))

    def test_exported_presets_and_clearance(self):
        report=json.loads((ROOT/'output'/'engineering.json').read_text())
        for name,state in report['motion']['presets'].items():
            self.assertFalse(state['collision'],name)
            self.assertGreaterEqual(state['minimum_distance_mm'],P['clearance_screen_mm'],name)
        for name,state in report['motion']['transitions'].items():self.assertEqual(state['collision_samples'],0,name)
        self.assertEqual(report['motion']['coordinated_roll']['clear_intervals_deg'],[[-60,60]])

    def test_print_meshes_are_closed_and_on_bed(self):
        paths=list((ROOT/'output'/'print-stl').glob('*.stl'))
        self.assertGreater(len(paths),10)
        for path in paths:
            mesh=trimesh.load_mesh(path)
            mesh.merge_vertices(digits_vertex=4)
            self.assertTrue(mesh.is_watertight,path.name)
            self.assertGreater(mesh.volume,0,path.name)
            positive_components=[c for c in mesh.split(only_watertight=False) if c.volume>1]
            self.assertEqual(len(positive_components),1,path.name)
            self.assertAlmostEqual(mesh.bounds[0,2],0,places=3,msg=path.name)
            if path.stem=='nose_panel':self.assertLess(mesh.extents[2],1.7,'Nose fascia must lie flat on its broad face')

    def test_nose_panel_tabs_contact_the_rim(self):
        import cadquery as cq
        folder=ROOT/'output/step-parts'
        panel=cq.importers.importStep(str(folder/'nose_panel.step')).val()
        rim=cq.Compound.makeCompound([cq.importers.importStep(str(folder/f'{name}.step')).val() for name in ['body_front_0','belly_front_0']])
        paths=sorted(folder.glob('nose_standoff_*.step'))
        self.assertEqual(len(paths),4)
        for path in paths:
            tab=cq.importers.importStep(str(path)).val()
            self.assertEqual(len(tab.Solids()),1)
            self.assertLess(tab.distance(panel),.001,'Support must touch the nose panel')
            self.assertLess(tab.distance(rim),.001,'Support must touch the surrounding body rim')
            self.assertLess(tab.intersect(panel).Volume(),.001)
            self.assertLess(tab.intersect(rim).Volume(),.001)

    def test_body_skin_and_service_head_clearance(self):
        import hashlib
        audit=json.loads((ROOT/'output/body-fit.json').read_text())
        self.assertEqual(audit['model_sha256'],hashlib.sha256((ROOT/'output/model.json').read_bytes()).hexdigest())
        for region in ['roof','left_side','right_side','front_rim','rear_cap']:
            self.assertGreaterEqual(audit['shell_regions'][region]['minimum_normal_ray_thickness_mm'],1.45,region)
        self.assertGreaterEqual(audit['shell_regions']['display_pocket']['minimum_normal_ray_thickness_mm'],.95)
        self.assertGreaterEqual(audit['minimum_sampled_panel_counterbore_floor_mm'],1.0)
        self.assertEqual(audit['head_cover_intersections'],[])
        self.assertEqual(audit['tool_access_intersections'],[])

    def test_report_matches_geometry(self):
        import hashlib
        report=json.loads((ROOT/'output'/'engineering.json').read_text())
        self.assertEqual(report['model_sha256'],hashlib.sha256((ROOT/'output'/'model.json').read_bytes()).hexdigest())
        self.assertTrue(report['printability']['all_fit'])
        self.assertEqual(report['battery_fit']['intersections'],[])
        self.assertEqual(report['fixed_packaging']['intersections'],[])

    def test_individual_mount_exports_match_assembly(self):
        import hashlib
        import cadquery as cq
        raw=(ROOT/'output/model.json').read_bytes();model=json.loads(raw)
        catalog=json.loads((ROOT/'output/parts-catalog.json').read_text())
        self.assertEqual(catalog['model_sha256'],hashlib.sha256(raw).hexdigest())
        by_id={p['id']:p for p in catalog['parts']}
        mounts=('roll_cartridge','motor_carrier','hip_hub','motor_mount_ring','knee_drive_adapter')
        expected={p['mesh'] for p in model['parts'] if any(p['name'].endswith('_'+n) for n in mounts)}
        self.assertTrue(expected.issubset(by_id))
        self.assertIn('motor_carrier_-1',expected)
        self.assertIn('motor_carrier_-1_right',expected)
        for key in expected:
            record=by_id[key];path=ROOT/'output'/record['step']
            self.assertEqual(record['step_sha256'],hashlib.sha256(path.read_bytes()).hexdigest())
            part=next(p for p in model['parts'] if p['mesh']==key)
            solid=cq.importers.importStep(str(path)).val()
            self.assertTrue(solid.isValid(),key)
            self.assertEqual(len(solid.Solids()),1,key)
            # STEP round trips change surface integration slightly; allow 0.01% volume.
            self.assertAlmostEqual(solid.Volume(),part['volume_mm3'],delta=max(.01,part['volume_mm3']*1e-4),msg=key)
            bounds=solid.BoundingBox()
            # Source bounds include the tessellator's roughly 0.1 mm inflation.
            np.testing.assert_allclose([bounds.xlen,bounds.ylen,bounds.zlen],part['bounds_mm'],atol=.15,rtol=0,err_msg=key)
            np.testing.assert_allclose(solid.Center().toTuple(),part['com_mm'],atol=.001,rtol=0,err_msg=key)
            self.assertEqual(record['quantity'],sum(p['mesh']==key for p in model['parts']))

if __name__=='__main__':unittest.main()
