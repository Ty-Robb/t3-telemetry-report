import json, sys, collections
path = sys.argv[1]
top = collections.Counter(); events = collections.Counter(); propkeys = collections.Counter()
propvals = collections.defaultdict(collections.Counter)
distinct = collections.Counter(); ts=[]; ua=collections.Counter(); tp=collections.Counter()
n=0
for line in open(path):
    r = json.loads(line); n+=1
    top.update(r.keys()); events[r['event']]+=1; distinct[r['distinct_id']]+=1
    ts.append(r['timestamp']); ua[r.get('user_agent')]+=1; tp[r.get('to_posthog')]+=1
    p = json.loads(r['properties']) if isinstance(r['properties'], str) else r['properties']
    for k,v in p.items():
        propkeys[k]+=1
        s = json.dumps(v) if not isinstance(v,str) else v
        if len(propvals[k])<5000: propvals[k][s[:120]]+=1
print('rows',n); print('top keys',top); print('min/max ts',min(ts),max(ts))
print('distinct_ids',len(distinct)); print(distinct.most_common(20))
print('user_agent',ua.most_common(10)); print('to_posthog',tp)
print('\nEVENTS', len(events))
for e,c in events.most_common(): print(f'  {c:7d} {e}')
print('\nPROPS', len(propkeys))
for k,c in propkeys.most_common():
    vals = propvals[k]
    print(f'  {c:7d} {k}  uniq={len(vals)}  e.g. {vals.most_common(6)}')
