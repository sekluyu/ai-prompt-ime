"""One local image smoke test, only when the existing ComfyUI queue is idle."""
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:8188'
def get(path):
    with urllib.request.urlopen(BASE+path,timeout=10) as f: return json.load(f)

def main():
    queue=get('/queue')
    if queue['queue_running'] or queue['queue_pending']:
        raise RuntimeError('ComfyUI busy; smoke test not submitted')
    info=get('/object_info/CheckpointLoaderSimple')
    available=info['CheckpointLoaderSimple']['input']['required']['ckpt_name'][0]
    model='NovaFurryILV18A.safetensors'
    if model not in available: raise RuntimeError('Expected local checkpoint not available')
    # Input is the exact core sequence produced by the real Rime integration test.
    engine=json.loads((ROOT/'validation/gpt/engine-test.json').read_text(encoding='utf-8'))
    positive=engine['core_sequence'].rstrip(', ')
    workflow={
      '1':{'class_type':'CheckpointLoaderSimple','inputs':{'ckpt_name':model}},
      '2':{'class_type':'CLIPTextEncode','inputs':{'text':positive,'clip':['1',1]}},
      '3':{'class_type':'CLIPTextEncode','inputs':{'text':'','clip':['1',1]}},
      '4':{'class_type':'EmptyLatentImage','inputs':{'width':768,'height':1024,'batch_size':1}},
      '5':{'class_type':'KSampler','inputs':{'model':['1',0],'positive':['2',0],'negative':['3',0],'latent_image':['4',0],'seed':20261112,'steps':20,'cfg':5.5,'sampler_name':'euler','scheduler':'normal','denoise':1.0}},
      '6':{'class_type':'VAEDecode','inputs':{'samples':['5',0],'vae':['1',2]}},
      '7':{'class_type':'SaveImage','inputs':{'images':['6',0],'filename_prefix':'ai-prompt-ime/smoke'}},
    }
    request=urllib.request.Request(BASE+'/prompt',data=json.dumps({'prompt':workflow,'client_id':'ai-prompt-ime-smoke'}).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=15) as f: submitted=json.load(f)
    prompt_id=submitted['prompt_id']
    report={'status':'submitted','prompt_id':prompt_id,'workflow':workflow,'model':model,'positive':positive,'limitation':'Single-image local pipeline smoke test; no model-wide tag quality conclusion'}
    target=ROOT/'validation/gpt/comfy-smoke.json'
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Submitted local smoke test '+prompt_id,flush=True)
    for _ in range(300):
        history=get('/history/'+prompt_id)
        if prompt_id in history:
            item=history[prompt_id]; report['history']=item
            if item.get('status',{}).get('status_str')=='error':
                report['status']='FAILED'; target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8'); raise RuntimeError('ComfyUI execution failed; see report')
            images=item.get('outputs',{}).get('7',{}).get('images',[])
            if images:
                query=urllib.parse.urlencode(images[0])
                with urllib.request.urlopen(BASE+'/view?'+query,timeout=15) as f: data=f.read()
                (ROOT/'validation/gpt/comfy-smoke.png').write_bytes(data)
                report['status']='PASS'; report['image']='validation/gpt/comfy-smoke.png'
                target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
                print('PASS: local image generated'); return
        time.sleep(2)
    raise TimeoutError('Generation still pending; inspect submitted prompt_id without resubmitting')

if __name__=='__main__': main()
