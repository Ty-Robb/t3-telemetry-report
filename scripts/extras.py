"""Extra aggregates for the report. Assumes `timestamp` is UTC (PostHog convention)."""
import json, sys, collections, datetime as dt
from zoneinfo import ZoneInfo
path, out = sys.argv[1], sys.argv[2]
PT=ZoneInfo('America/Los_Angeles')
C=collections.Counter
rows=[json.loads(l) for l in open(path)]
for r in rows: r['p']=json.loads(r['properties']); r['t']=dt.datetime.strptime(r['timestamp'][:19],'%Y-%m-%d %H:%M:%S').replace(tzinfo=dt.timezone.utc)
res={}
wk=lambda t:(t-dt.timedelta(days=t.weekday())).date().isoformat()
weekly=collections.defaultdict(C); wtok=collections.defaultdict(C)
for r in rows:
    w=wk(r['t']); weekly[w]['events']+=1; weekly[w][r['event']]+=1
    if r['event']=='provider.turn.completed':
        p=r['p']; wtok[w][p.get('provider')]+=p.get('inputTokens',0) or 0
        wtok[w]['uncached']+=(p.get('inputTokens',0) or 0)-(p.get('cachedInputTokens',0) or 0)
        wtok[w]['output']+=p.get('outputTokens',0) or 0
res['weekly']={k:dict(v) for k,v in sorted(weekly.items())}
res['weekly_tokens']={k:dict(v) for k,v in sorted(wtok.items())}
# user-initiated turns by PT hour x weekday
hm=C(); hm_utc=C(); hours_pt=C()
for r in rows:
    if r['event']=='client.turn.requested':
        t=r['t'].astimezone(PT); hm[(t.strftime('%a'),t.hour)]+=1; hours_pt[t.hour]+=1
res['user_turns_by_pt_hour']=dict(sorted(hours_pt.items()))
res['user_turns_heat']={f'{a}-{b}':c for (a,b),c in hm.items()}
# all events by PT hour
res['all_by_pt_hour']=dict(sorted(C(r['t'].astimezone(PT).hour for r in rows).items()))
# turns/tokens by provider
pv=collections.defaultdict(C)
for r in rows:
    if r['event']=='provider.turn.completed':
        p=r['p']; k=p.get('provider'); pv[k]['turns']+=1
        for f in ['inputTokens','cachedInputTokens','outputTokens','reasoningTokens']: pv[k][f]+=p.get(f,0) or 0
res['provider_tokens']={k:dict(v) for k,v in pv.items()}
# models on turns
res['turn_models']=dict(C(r['p'].get('model') for r in rows if r['event']=='provider.turn.completed').most_common(12))
# client turns by surface/device
res['user_turn_surface']=dict(C(r['p'].get('surface') for r in rows if r['event']=='client.turn.requested'))
res['user_turn_creationSource']=dict(C(r['p'].get('creationSource') for r in rows if r['event']=='client.turn.requested'))
# longest gap in events (proxy for offline time)
ts=sorted(r['t'] for r in rows); gaps=sorted(((b-a).total_seconds()/3600,a.isoformat()) for a,b in zip(ts,ts[1:]))[-5:]
res['longest_gaps_h']=gaps
# daily user turns
res['daily_user_turns']=dict(sorted(C(r['t'].astimezone(PT).date().isoformat() for r in rows if r['event']=='client.turn.requested').items()))
res['days_with_user_turns']=len(res['daily_user_turns'])
# per-install event share
res['events_by_serverOs']=dict(C(r['p'].get('serverOs') for r in rows))
json.dump(res,open(f'{out}/extras.json','w'),indent=1,default=str)
for k in ['weekly_tokens','user_turns_by_pt_hour','all_by_pt_hour','provider_tokens','turn_models','user_turn_surface','longest_gaps_h','days_with_user_turns']: print(k, json.dumps(res[k],default=str))
print('weekly events', {k:v['events'] for k,v in res['weekly'].items()})
