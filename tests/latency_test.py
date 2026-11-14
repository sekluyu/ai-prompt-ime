"""Compare old/new Lua per-key latency and outputs in isolated librime processes."""
import argparse
import copy
import csv
import hashlib
import json
import math
import os
import re
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]

def worker(source):
    from engine_test import Engine
    os.environ['BOORU_TEST_SOURCE']=str(source)
    os.environ['BOORU_TEST_USER']=str(source.parent/'runtime')
    os.environ['BOORU_TEST_LOG']=str(source.parent)
    durations={}
    original=Engine.call
    def timed(self,name,*args):
        start=time.perf_counter()
        value=original(self,name,*args)
        durations[name]=durations.get(name,0)+time.perf_counter()-start
        return value
    Engine.call=timed
    engine=Engine()
    events=[]
    try:
        for query in ['huli','shuangmawei','zuoshoufuyaoyoushoumotou',
                      'zhilianggenggao','jiao','bi','piyan','shu','x']:
            engine.reset()
            actions=list(query)+['=','-','\b','\b','\b',' ']
            for ch in actions:
                start=time.perf_counter()
                engine.key(ch)
                candidates,last=engine.candidates()
                commit=engine.commit()
                elapsed=(time.perf_counter()-start)*1000
                events.append(dict(query=query,key=ch,ms=elapsed,
                                   candidates=candidates,last=last,commit=commit))
    finally:
        engine.close()
    values=sorted(event['ms'] for event in events)
    return dict(events=events,keys=len(values),median_ms=statistics.median(values),
                p95_ms=values[math.ceil(.95*len(values))-1],max_ms=max(values),
                select_schema_seconds=durations.get('select_schema',0))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-ref',default='v0.2.6')
    parser.add_argument('--output-dir',type=Path)
    parser.add_argument('--worker',type=Path,help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.worker),ensure_ascii=True))
        return
    if args.output_dir is None:
        parser.error('--output-dir is required')
    baseline=subprocess.check_output(['git','show',args.baseline_ref+':rime/lua/booru_filter.lua'],cwd=ROOT)
    runs=[]
    reference=None
    raw_reference=None
    raw_outputs_identical=True
    expected_prefix_adjustments=0
    with (ROOT/'rime/booru.tsv').open(encoding='utf-8') as stream:
        prefixes={re.sub(r'([\\()])',r'\\\1',row['tag'].removeprefix('__prompt__:'))
                  for row in csv.DictReader(stream,delimiter='\t') if '〔待续写〕' in row['zh']}
    expected_suffixes={text+', ':text+' ' for text in prefixes}
    with tempfile.TemporaryDirectory(prefix='ime-latency-') as tmp:
        for round_no in range(3):
            for label in ['baseline','candidate']:
                base=Path(tmp)/f'{round_no}-{label}'
                source=base/'source'
                shutil.copytree(ROOT/'rime',source)
                if label=='baseline':
                    (source/'lua/booru_filter.lua').write_bytes(baseline)
                result=subprocess.run([sys.executable,__file__,'--worker',str(source)],
                                      capture_output=True,encoding='utf-8',timeout=120)
                if result.returncode:
                    raise RuntimeError('Isolated latency worker failed:\n'+result.stdout+'\n'+result.stderr)
                run=json.loads(result.stdout)
                run.update(label=label,round=round_no+1)
                raw_signatures=[{k:v for k,v in event.items() if k!='ms'} for event in run['events']]
                signatures=copy.deepcopy(raw_signatures)
                if raw_reference is None:raw_reference=raw_signatures
                raw_outputs_identical=raw_outputs_identical and raw_signatures==raw_reference
                if label=='baseline':
                    for event in signatures:
                        for candidate in event['candidates']:
                            if '〔待续写〕' in candidate['comment'] and candidate['text'] in expected_suffixes:
                                candidate['text']=expected_suffixes[candidate['text']]
                                expected_prefix_adjustments+=1
                        if event['commit'] in expected_suffixes:
                            event['commit']=expected_suffixes[event['commit']]
                            expected_prefix_adjustments+=1
                if reference is None:
                    reference=signatures
                if signatures!=reference:
                    raise AssertionError('Unexpected text, annotation, order or commit difference: '+label)
                runs.append(run)
                print(json.dumps({k:v for k,v in run.items() if k!='events'}),flush=True)
    passed=all(run['median_ms']<5 and run['p95_ms']<10 for run in runs if run['label']=='candidate')
    report=dict(status='PASS' if passed else 'FAIL',baseline_ref=args.baseline_ref,
                baseline_lua_sha256=hashlib.sha256(baseline).hexdigest(),
                candidate_lua_sha256=hashlib.sha256((ROOT/'rime/lua/booru_filter.lua').read_bytes()).hexdigest(),
                dictionary_sha256=hashlib.sha256((ROOT/'rime/booru.tsv').read_bytes()).hexdigest(),
                annotations_sha256=hashlib.sha256((ROOT/'rime/booru.annotations.tsv').read_bytes()).hexdigest(),
                outputs_compatible_with_expected_continuations=True,
                unaffected_outputs_identical=True,raw_outputs_identical=raw_outputs_identical,
                expected_baseline_prefix_adjustments=expected_prefix_adjustments,runs=runs,
                scope='Separate librime processes; synthetic keys, backspace, paging and selection; no live Weasel input or desktop acceptance')
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/'latency.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    if not passed:
        raise AssertionError('Candidate exceeded median <5ms / p95 <10ms target')

if __name__=='__main__':
    main()
