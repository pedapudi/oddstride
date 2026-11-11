"""Regression checks for the exported prototype and its transmission geometry."""
import json, unittest
from pathlib import Path
import numpy as np
import trimesh
from kinematics import ROOT,P,LEGS,POSES,frames,point,rotation,matrix,contacts
from collision import Checker

class ModelChecks(unittest.TestCase):
    def test_integrated_joint_assembly(self):
        import hashlib
        report=json.loads((ROOT/'output/integration-audit.json').read_text())
        self.assertEqual(report['model_sha256'],hashlib.sha256((ROOT/'output/model.json').read_bytes()).hexdigest())
        self.assertTrue(all(p['passed'] for p in report['paths']))
        self.assertTrue(all(p['retaining_lip_overlap_mm3']>1 for p in report['bearing_retention']))
        self.assertEqual(report['counts']['custom_leg_components_removed_net'],8)

    def test_motor_service_paths(self):
        import hashlib
        report=json.loads((ROOT/'output/limb-assembly-audit.json').read_text())
        self.assertEqual(report['model_sha256'],hashlib.sha256((ROOT/'output/model.json').read_bytes()).hexdigest())
        self.assertTrue(all(p['passed'] for p in report['paths']))
        self.assertLess(report['closed_overlap_mm3'],1e-4)
        self.assertEqual(len(report['paths']),3)

    def test_body_assembly_access(self):
        import hashlib
        stamp=hashlib.sha256((ROOT/'output/model.json').read_bytes()).hexdigest()
        report=json.loads((ROOT/'output/assembly-audit.json').read_text())
        self.assertEqual(report['model_sha256'],stamp)
        self.assertTrue(report['passed'])
        self.assertGreaterEqual(len(report['paths']),3)
        self.assertGreaterEqual(len(report['tool_access']),24)
        self.assertEqual(len(report['nut_insertion']),4)
        self.assertEqual(report['hardware_counts']['after']['cover_screws'],4)

    def test_body_skin_and_declared_limb_refinement(self):
        import hashlib
        stamp=hashlib.sha256((ROOT/'output/model.json').read_bytes()).hexdigest()
        report=json.loads((ROOT/'output/body-revision-comparison.json').read_text())
        self.assertEqual(report['model_sha256'],stamp)
        self.assertFalse(report['limb_meshes_unchanged'])
        self.assertTrue(any(n.endswith('_shin_inner') for n in report['changed_limb_meshes']))
        self.assertGreaterEqual(report['skin_checks']['nominal_envelope_min_mm'],1.5)
        self.assertGreaterEqual(report['skin_checks']['finished_fascia_min_mm'],1.5)
        self.assertGreaterEqual(report['skin_checks']['return_tongue_min_sampled_section_mm2'],25)
        self.assertTrue(all(v['intersection_mm3']<1e-4 for v in report['fit_checks']))
        self.assertEqual(report['joint_interval_changes'],[])

    def test_manufacturing_inventory_and_convex_face(self):
        import hashlib
        stamp=hashlib.sha256((ROOT/'output/model.json').read_bytes()).hexdigest()
        result=json.loads((ROOT/'output/refinement-checks.json').read_text())
        plan=json.loads((ROOT/'output/manufacturing-plan.json').read_text())
        steps=json.loads((ROOT/'output/step-roundtrip.json').read_text())
        self.assertTrue(all(record['model_sha256']==stamp for record in [result,plan,steps]))
        self.assertGreater(result['face_center_to_y90_bow_mm'],2.0)
        self.assertGreater(result['face_vertical_bow_mm'],3.0)
        self.assertTrue(result['previous_sampled_motion_preserved'])
        self.assertTrue(all(p['valid'] and p['expected_solids']==p['reopened_solids'] for p in steps['parts']))
        self.assertEqual(len(steps['parts']),len(plan['parts']))
        self.assertTrue(all(p['screen']['fits'] for p in plan['parts'] if 'screen' in p))

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
        self.assertGreaterEqual(audit['minimum_sampled_groove_wall_mm'],2.3)
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
        self.assertGreater(root.bounds[1,1]-waist.bounds[1,1],1,'Export must contain the sculpted outer surface')
        self.assertLess(root.bounds[1,1]-waist.bounds[1,1],3,'Retain material around the thigh web')

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

    def test_rounded_boot_contact_matches_kinematics(self):
        data=json.loads((ROOT/'output/model.json').read_text())
        for leg in LEGS:
            part=next(p for p in data['parts'] if p['name']==leg+'_foot')
            vertices=np.array(data['meshes'][part['mesh']]['vertices'])
            for pose in ['stand','studio','raised','crouch','reach']:
                transform=matrix(part,POSES[pose])
                world=vertices@transform[:3,:3].T+transform[:3,3]
                foot,_,_=contacts(leg,POSES[pose][leg])
                self.assertAlmostEqual(world[:,2].min(),foot[2],delta=.5,msg=leg+' '+pose)
        report=json.loads((ROOT/'output/engineering.json').read_text())
        part=next(p for p in data['parts'] if p['name']=='FL_foot')
        vertices=np.array(data['meshes'][part['mesh']]['vertices'])
        for case in report['torque_cases']:
            poses={leg:case['q_deg'] for leg in LEGS};transform=matrix(part,poses)
            world=vertices@transform[:3,:3].T+transform[:3,3]
            foot,_,_=contacts('FL',case['q_deg'])
            self.assertAlmostEqual(world[:,2].min(),foot[2],delta=.5,msg=case['case'])

    def test_shin_has_single_shallow_bow_and_continuous_taper(self):
        data=json.loads((ROOT/'output/model.json').read_text())
        # The fore/aft split divides the profile; evaluate both structural halves.
        meshes=[]
        for name in ['FL_shin_inner','FL_shin_outer']:
            part=next(p for p in data['parts'] if p['name']==name)
            geometry=data['meshes'][part['mesh']]
            meshes.append(trimesh.Trimesh(vertices=geometry['vertices'],faces=geometry['faces'],process=False))
        mesh=trimesh.util.concatenate(meshes)
        widths=[];centers=[];stations=[35,55,75,95,115,132]
        for distance in stations:
            section=mesh.section(plane_origin=[0,0,-distance],plane_normal=[0,0,1])
            centers.append(section.bounds[:,0].mean())
            widths.append(section.bounds[1,0]-section.bounds[0,0])
        self.assertTrue(all(a>b for a,b in zip(widths,widths[1:])),widths)
        self.assertGreater(max(centers),2.7)
        self.assertLess(max(centers),3.8)
        coefficients=np.polyfit(stations,centers,2)
        self.assertLess(coefficients[0],0)
        self.assertLess(max(abs(np.polyval(coefficients,stations)-centers)),.15)
        slopes=np.diff(centers)/np.diff(stations)
        self.assertTrue(all(np.diff(slopes)<0),'Shin must have one consistent curvature sign')

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
