import importlib.util, pathlib, unittest
from unittest.mock import patch
p=pathlib.Path(__file__).resolve().parents[1]/"server.py"
spec=importlib.util.spec_from_file_location("wmk_server",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def cfg(**kw):
 d=dict(prompt="pixel art",size=256,steps=5);d.update(kw);return d
class TestWMK(unittest.TestCase):
 def setUp(self): self.h=object.__new__(m.Handler)
 def test_lora_graph(self):
  n=self.h.workflow_nodes(cfg())
  self.assertEqual(n["8"]["class_type"],"LoraLoader")
  self.assertEqual(n["5"]["inputs"]["model"],["8",0])
  self.assertEqual(n["2"]["inputs"]["clip"],["8",1])
 def test_without_lora(self):
  n=self.h.workflow_nodes(cfg(lora=""))
  self.assertNotIn("8",n)
  self.assertEqual(n["5"]["inputs"]["model"],["1",0])
 def test_invalid(self):
  for v in (0,31):
   with self.assertRaises(ValueError): self.h.image_settings(cfg(steps=v))
  with self.assertRaises(ValueError): self.h.image_settings(cfg(lora="../bad"))
 def test_seed(self): self.assertEqual(self.h.workflow_nodes(cfg(seed=42))["5"]["inputs"]["seed"],42)
 def test_submission_mock(self):
  calls=[]
  def fake(url,method="GET",body=None,**kw):
   calls.append((url,method,body))
   return {"queue_running":[],"queue_pending":[]} if url.endswith("/queue") else {"prompt_id":"abc"}
  with patch.object(m,"call",side_effect=fake): result=self.h.generate_image_job("chat",cfg())
  self.assertEqual(result["prompt_id"],"abc")
  self.assertIn("8",calls[1][2]["prompt"])
 def test_health_partial_outage(self):
  with patch.object(m,"probe",side_effect=[{"status":"offline"},{"status":"online"}]): r=m.health_report()
  self.assertTrue(r["ok"])
  self.assertEqual(r["services"]["ollama"]["status"],"offline")
 def test_probe_timeout(self):
  with patch.object(m.request,"urlopen",side_effect=TimeoutError("timeout")): r=m.probe("http://127.0.0.1:8188/system_stats")
  self.assertEqual(r["status"],"offline")
  self.assertEqual(r["error_type"],"TimeoutError")
if __name__=="__main__":unittest.main()

