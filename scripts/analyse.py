"""Deeper analysis of Theo's T3 Code telemetry dump. Usage: python3 analyse.py <jsonl> <outdir>"""
import json, sys, collections, re, os, datetime as dt
path, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
rows=[]
for line in open(path):
    r=json.loads(line); r['p']=json.loads(r['properties']); rows.append(r)
C=collections.Counter
def ts(s): return dt.datetime.strptime(s[:19],'%Y-%m-%d %H:%M:%S')
res={}
# daily counts & by event
daily=C(); daily_ev=collections.defaultdict(C); hour=C(); wd=C()
for r in rows:
    t=ts(r['timestamp']); daily[t.date().isoformat()]+=1; daily_ev[t.date().isoformat()][r['event']]+=1
    hour[t.hour]+=1; wd[t.strftime('%a')]+=1
res['daily']=dict(sorted(daily.items())); res['hour_utc']=dict(sorted(hour.items())); res['weekday']=dict(wd)
res['active_days']=len(daily); res['span_days']=(ts(rows[-1]['timestamp'])-ts(rows[0]['timestamp'])).days
# weekly by event
weekly=collections.defaultdict(C)
for r in rows:
    t=ts(r['timestamp']); wk=(t-dt.timedelta(days=t.weekday())).date().isoformat(); weekly[wk][r['event']]+=1
res['weekly_events']={k:dict(v) for k,v in sorted(weekly.items())}
# tokens from provider.turn.completed
tok=collections.defaultdict(lambda: C()); 
for r in rows:
    if r['event']=='provider.turn.completed':
        p=r['p']; key=p.get('model') or p.get('provider') or '?'
        for f in ['inputTokens','outputTokens','cachedInputTokens','cacheCreationTokens','reasoningTokens']:
            v=p.get(f); 
            if isinstance(v,(int,float)): tok[key][f]+=v
        tok[key]['turns']+=1
res['tokens_by_model']={k:dict(v) for k,v in sorted(tok.items(), key=lambda x:-x[1]['turns'])}
tot=C()
for v in tok.values(): tot.update(v)
res['tokens_total']=dict(tot)
# per-provider turns, models, tools, features, errors
def cnt(ev,field):
    c=C(r['p'].get(field) for r in rows if (ev is None or r['event']==ev) and field in r['p']); return dict(c.most_common())
res['turns_by_provider']=cnt('provider.turn.completed','provider')
res['models_all']=cnt(None,'model')
res['tools']=cnt('mcp.tool.invoked','tool')
res['features']=cnt('feature.used','feature')
res['errorCodes']=cnt(None,'errorCode')
res['effort']=cnt(None,'effort')
res['runtimeMode']=cnt(None,'runtimeMode')
res['clientDeviceModel']=cnt(None,'clientDeviceModel')
res['clientOs']=cnt('client.connected','clientOs')
res['connectionMethod']=cnt('client.connected','connectionMethod')
res['ownerSource']=cnt('install.owner_observed','ownerSource')
res['serviceTier']=cnt(None,'serviceTier')
res['delegation_pairs']=dict(C(f"{r['p'].get('callerProvider')}->{r['p'].get('targetProvider')}" for r in rows if r['event']=='mcp.delegated_task.finished').most_common())
# identifier inventory
ids={}
for f in ['installId','ownerId']:
    ids[f]=len({r['p'][f] for r in rows if f in r['p']})
ids['distinct_id']=len({r['distinct_id'] for r in rows}); ids['uuid']=len({r['uuid'] for r in rows})
res['identifier_counts']=ids
# map distinct_id -> platform/os/install
m=collections.defaultdict(lambda: collections.defaultdict(C))
for r in rows:
    d=r['distinct_id'][:12]; p=r['p']
    m[d]['serverOs'][p.get('serverOs')]+=1; m[d]['arch'][p.get('arch')]+=1
    m[d]['installId'][(p.get('installId') or '-')[:12]]+=1; m[d]['n']['events']+=1
    m[d]['first'][r['timestamp'][:10]]+=1
res['distinct_id_profile']={d:{'events':v['n']['events'],'serverOs':dict(v['serverOs']),'arch':dict(v['arch']),'installIds':list(v['installId']),'first_day':min(v['first']),'last_day':max(v['first'])} for d,v in m.items()}
# PII scan: every string value; look for paths, emails, IPs, urls, long free text
pat={'email':re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+'),'ipv4':re.compile(r'\b\d{1,3}(?:\.\d{1,3}){3}\b'),'path':re.compile(r'(/Users/|/home/|C:\\\\|~/)'),'url':re.compile(r'https?://'),'spaces4':re.compile(r'(\S+\s+){4,}')}
hits=collections.defaultdict(C); strvals=collections.defaultdict(set)
for r in rows:
    for k,v in list(r['p'].items())+[('user_agent',r['user_agent'])]:
        if isinstance(v,str):
            strvals[k].add(v)
            for n,rx in pat.items():
                if rx.search(v) and not re.fullmatch(r'[\d.]+(-nightly[\d.]*)?',v): hits[n][k]+=1
res['pii_scan_hits']={k:dict(v) for k,v in hits.items()}
res['string_fields_cardinality']={k:len(v) for k,v in sorted(strvals.items(), key=lambda x:-len(x[1]))}
res['high_card_string_samples']={k:sorted(v)[:8] for k,v in strvals.items() if len(v)>30 and k not in('installId','ownerId')}
# latency
d=[r['p']['durationMs'] for r in rows if r['event']=='provider.turn.completed' and isinstance(r['p'].get('durationMs'),(int,float))]
d.sort(); res['turn_duration_ms']={'n':len(d),'median':d[len(d)//2],'p90':d[int(len(d)*.9)],'max':d[-1]} if d else {}
# ingestion lag
lag=[(ts(r['received_at'])-ts(r['timestamp'])).total_seconds() for r in rows]; lag.sort()
res['ingest_lag_s']={'median':lag[len(lag)//2],'p99':lag[int(len(lag)*.99)],'max':lag[-1],'min':lag[0]}
res['inserted_at_range']=[min(r['inserted_at'] for r in rows),max(r['inserted_at'] for r in rows)]
res['to_posthog_false_events']=dict(C(r['event'] for r in rows if not r['to_posthog']))
json.dump(res, open(f'{out}/analysis.json','w'), indent=1, default=str)
print(json.dumps({k:res[k] for k in ['active_days','span_days','tokens_total','turns_by_provider','identifier_counts','pii_scan_hits','turn_duration_ms','ingest_lag_s','inserted_at_range','to_posthog_false_events','hour_utc','weekday','string_fields_cardinality','high_card_string_samples']}, indent=1, default=str))
