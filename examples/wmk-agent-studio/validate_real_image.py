import importlib.util,json,time,urllib.request,pathlib,sys
root=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('wmk',root/'server.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
h=object.__new__(m.Handler)
nodes=h.workflow_nodes({'prompt':'pixel art red potion bottle, centered, game item, simple background','negative':'blurry, text, watermark','size':256,'steps':5,'cfg':6,'seed':42,'lora_strength':0.7})
print('Submitting',flush=True)
r=m.call('http://127.0.0.1:8188/prompt','POST',{'prompt':nodes,'client_id':'wmk-v11-validation'},timeout=20)
print(json.dumps(r),flush=True)
pid=r.get('prompt_id')
if not pid: sys.exit(2)
(root/'test-prompt-id.txt').write_text(pid)
for i in range(60):
 time.sleep(10)
 try:
  hist=m.call('http://127.0.0.1:8188/history/'+pid,timeout=5).get(pid)
  if hist:
   images=[v for o in hist.get('outputs',{}).values() for v in o.get('images',[])]
   print('FINISHED '+json.dumps({'images':images,'status':hist.get('status')}),flush=True)
   sys.exit(0 if images else 3)
  if i%3==0: print('WAIT '+str((i+1)*10)+'s',flush=True)
 except Exception as e: print('POLL_ERROR '+str(e),flush=True)
print('TIMEOUT',flush=True);sys.exit(4)
