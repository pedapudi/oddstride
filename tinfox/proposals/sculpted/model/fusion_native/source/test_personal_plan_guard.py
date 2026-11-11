"""Check publication capacity and protection of unrelated or unsaved work."""
import unittest
from types import SimpleNamespace as NS
from personal_plan_guard import personal_plan_inventory,require_personal_capacity,PersonalPlanCapacityError

class CapacityChecks(unittest.TestCase):
 def setUp(self):
  project=NS(id='tinfox-project')
  self.master_file=NS(id='master',name='Native master',parentProject=project,isReadOnly=False,isComplete=True)
  self.part=NS(id='part',name='Saved foot',parentProject=project,isReadOnly=False,isComplete=True)
  self.other=NS(id='other',name='Unrelated user work',parentProject=NS(id='other-project'),isReadOnly=False,isComplete=True)
  self.master=NS(isSaved=True,dataFile=self.master_file,isModified=False,name='Native master')
  self.limits=NS(editableFiles=[self.master_file,self.part,self.other],editableFileCount=8,maxEditableFileCount=10)
  self.app=NS(data=NS(personalUseLimits=self.limits),documents=[self.master,NS(isSaved=False,name='Unsaved user work')])
  self.known={'master':{'part':'master','project_id':'tinfox-project','completed_saved_candidate':False},'part':{'part':'foot','project_id':'tinfox-project','completed_saved_candidate':True}}
 def test_space_for_publication_and_recovery(self):
  r=require_personal_capacity(self.app,self.master,self.known)
  self.assertEqual(r['available_slots'],2)
  self.assertEqual([p['file_id'] for p in r['manual_read_only_candidates']],['part'])
  self.assertEqual(r['unmanaged_editable_file_count'],1)
  self.assertEqual(r['unsaved_open_documents'],1)
 def test_near_limit_stops_before_write(self):
  for count in [9,10]:
   self.limits.editableFileCount=count
   with self.assertRaises(PersonalPlanCapacityError):require_personal_capacity(self.app,self.master,self.known)
 def test_current_or_modified_part_is_protected(self):
  r=personal_plan_inventory(self.app,self.known,['part']);self.assertEqual(r['manual_read_only_candidates'],[])
  self.app.documents.append(NS(isSaved=True,dataFile=self.part,isModified=True,name='Saved foot'))
  r=personal_plan_inventory(self.app,self.known);self.assertEqual(r['manual_read_only_candidates'],[])
 def test_wrong_project_or_incomplete_upload_is_excluded(self):
  self.part.parentProject=NS(id='other-project')
  self.assertEqual(personal_plan_inventory(self.app,self.known)['manual_read_only_candidates'],[])
  self.part.parentProject=NS(id='tinfox-project');self.part.isComplete=False
  self.assertEqual(personal_plan_inventory(self.app,self.known)['manual_read_only_candidates'],[])
 def test_readonly_master_cannot_be_modified(self):
  self.master_file.isReadOnly=True
  with self.assertRaises(PersonalPlanCapacityError):require_personal_capacity(self.app,self.master,self.known)
 def test_commercial_license_has_no_personal_count(self):
  self.app.data.personalUseLimits=None
  self.assertFalse(require_personal_capacity(self.app,self.master,self.known)['personal_plan'])

if __name__=='__main__':unittest.main()
