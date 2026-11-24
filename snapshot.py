import json, urllib.request, datetime, pathlib, statistics
BASE='https://api.sleeper.app/v1/'
IDS=['1387556348635402240','1312115773220601856']; USER='608889033698906112'
def get(p):
    with urllib.request.urlopen(urllib.request.Request(BASE+p,headers={'User-Agent':'FantasyManager/3.0'}),timeout=45) as r: return json.load(r)
def build():
    directory=get('players/nfl'); nfl=get('state/nfl'); errors=[]
    def optional(p):
        try: return get(p)
        except Exception as e: errors.append({'endpoint':p,'error':str(e)}); return None
    trends={x['player_id']:x['count'] for x in (optional('players/nfl/trending/add?lookback_hours=24&limit=200') or [])}
    def player(i):
        p=directory.get(i) or {}; return dict(id=i,name=p.get('full_name') or i,position=p.get('position'),team=p.get('team'),injury=p.get('injury_status'),status=p.get('status'),trending=trends.get(i,0),depth_chart_order=p.get('depth_chart_order'),depth_chart_position=p.get('depth_chart_position'))
    out=dict(schema_version=3,generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),user_id=USER,nfl_state=nfl,leagues=[],errors=errors,limitations=['Historical points are Sleeper league matchup player points, not raw NFL statistics. Missing weeks are not zero. Unrostered player history may be incomplete. NFL schedules, projections and usage are not supplied by this exporter.'])
    for i in IDS:
        l=get('league/'+i); rs=get('league/'+i+'/rosters'); mine=next(r for r in rs if r.get('owner_id')==USER or USER in (r.get('co_owners') or [])); owned={p for r in rs for k in ('players','reserve','taxi') for p in (r.get(k) or [])}; free=[player(p) for p,v in directory.items() if p not in owned and v and v.get('position') in ('QB','RB','WR','TE','DEF') and v.get('team') and (v.get('active') or v.get('status')=='Active')]; free.sort(key=lambda p:(-p['trending'],p['name']))
        last=l['settings'].get('last_scored_leg',nfl['week']-1); history={}; matchups={}; opponents={}
        for w in range(1,min(18,max(last,nfl['week'])+3)+1):
            rows=optional(f'league/{i}/matchups/{w}')
            if not isinstance(rows,list): continue
            own=next((r for r in rows if r.get('roster_id')==mine['roster_id']),None)
            if own and own.get('matchup_id') is not None: opponents[str(w)]=[r['roster_id'] for r in rows if r.get('matchup_id')==own['matchup_id'] and r['roster_id']!=mine['roster_id']]
            if w>last: continue
            matchups[str(w)]=rows
            for r in rows:
                for p,v in (r.get('players_points') or {}).items():
                    if isinstance(v,(int,float)): history.setdefault(p,{})[str(w)]=v
        analytics={}
        for p,h in history.items():
            vals=[v for _,v in sorted(h.items(),key=lambda x:int(x[0]))]; analytics[p]=dict(weekly_points=h,recorded_weeks=len(vals),average=round(statistics.mean(vals),2),last3=round(statistics.mean(vals[-3:]),2),last5=round(statistics.mean(vals[-5:]),2),stdev=round(statistics.pstdev(vals),2))
        out['leagues'].append(dict(id=i,name=l['name'],settings=l['settings'],scoring=l['scoring_settings'],slots=l['roster_positions'],standings=[dict(roster_id=r['roster_id'],settings=r['settings']) for r in rs],my_roster=mine,all_rosters=rs,players=[player(p) for p in sorted(owned)],unrostered=free,completed_matchups=matchups,fantasy_opponents=opponents,player_analytics=analytics))
    return out
if __name__=='__main__': pathlib.Path('snapshot.json').write_text(json.dumps(build(),separators=(',',':')))
