import unittest
from unittest.mock import patch
from test_v11 import m
class CancelTests(unittest.TestCase):
 def setUp(self): self.h=object.__new__(m.Handler);self.h.reply=lambda d,status=200:(status,d);self.h.fail=lambda d,status=400:(status,{'error':str(d)})
 def test_pending_cancel(self):
  with patch.object(m,'call',side_effect=[{'queue_pending':[[0,'00000000-0000-0000-0000-000000000001',{}]],'queue_running':[]},{}]) as api:
   code,data=self.h.cancel_image({'prompt_id':'00000000-0000-0000-0000-000000000001'})
  self.assertEqual(code,200)
  self.assertEqual(api.call_args_list[1].args[2],{'delete':['00000000-0000-0000-0000-000000000001']})
 def test_running_never_interrupt(self):
  with patch.object(m,'call',return_value={'queue_pending':[],'queue_running':[[0,'00000000-0000-0000-0000-000000000001',{}]]}) as api:
   code,data=self.h.cancel_image({'prompt_id':'00000000-0000-0000-0000-000000000001'})
  self.assertEqual(code,409)
  self.assertEqual(api.call_count,1)
 def test_other_job_not_cancelled(self):
  with patch.object(m,'call',return_value={'queue_pending':[],'queue_running':[]}) as api:
   code,data=self.h.cancel_image({'prompt_id':'00000000-0000-0000-0000-000000000001'})
  self.assertEqual(code,404)
  self.assertEqual(api.call_count,1)
 def test_invalid_id(self):
  with patch.object(m,'call') as api:
   code,data=self.h.cancel_image({'prompt_id':'../../invalid'})
  self.assertEqual(code,400)
  api.assert_not_called()
if __name__=='__main__':unittest.main()
