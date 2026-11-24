import json, urllib.request, datetime, pathlib
BASE='https://api.sleeper.app/v1/'
IDS=['1387556348635402240','1312115773220601856']
USER='608889033698906112'
def get(p):
    with urllib.request.urlopen(urllib.request.Request(BASE+p,headers={'User-Agent':'FantasyManager/2.0'}),timeout=90) as r: return json.load(r)
def build():
    players=get('players/nfl'); trending={x['player_id']:x['count'] for x in get('players/nfl/trending/add?lookback_hours=24&limit=200')}
    def player(i):
        p=players.get(i,{}) or {}; return dict(id=i,name=p.get('full_name') or i,position=p.get('position'),team=p.get('team'),injury=p.get('injury_status'),status=p.get('status'),trending=trending.get(i,0))
    out={'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'user_id':USER,'nfl_state':get('state/nfl'),'leagues':[]}
    for i in IDS:
        l=get('league/'+i); rs=get('league/'+i+'/rosters'); owned={p for r in rs for k in ('players','reserve','taxi') for p in (r.get(k) or [])}; mine=next(r for r in rs if r.get('owner_id')==USER or USER in (r.get('co_owners') or [])); free=[player(p) for p,v in players.items() if p not in owned and v and v.get('position') in ('QB','RB','WR','TE','K','DEF') and (v.get('active') or v.get('team'))]; free.sort(key=lambda p:(-p['trending'],p['name'])); out['leagues'].append(dict(id=i,name=l['name'],settings=l['settings'],scoring=l['scoring_settings'],slots=l['roster_positions'],standings=[dict(roster_id=r['roster_id'],settings=r['settings']) for r in rs],my_roster=mine,players=[player(p) for p in sorted(owned)],unrostered=free))
    return out
if __name__=='__main__':
    data=build(); pathlib.Path('snapshot.json').write_text(json.dumps(data,separators=(',',':')))
