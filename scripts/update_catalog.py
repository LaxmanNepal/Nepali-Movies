import json,os,re,urllib.parse,urllib.request
from datetime import datetime,timezone
KEY=os.getenv('YOUTUBE_API_KEY')
OUT='data/movies.json'
if not KEY:
    print('YOUTUBE_API_KEY is not configured; keeping existing catalog.')
    raise SystemExit(0)
QUERIES=['Nepali full movie','Nepali film full movie','नेपाली फिल्म full movie','Nepali movie official']
def api(endpoint,params):
    p=dict(params,key=KEY);u='https://www.googleapis.com/youtube/v3/'+endpoint+'?'+urllib.parse.urlencode(p)
    with urllib.request.urlopen(u,timeout=30) as r:return json.load(r)
def clean_title(t):
    t=re.sub(r'\b(full movie|full film|official movie|official full movie|nepali movie)\b','',t,flags=re.I)
    return re.sub(r'\s+',' ',t).strip(' -|')
def score(v,days):
    views=max(int(v.get('viewCount',0)),0);likes=max(int(v.get('likeCount',0)),0);age=max(days,1)
    return round(min(100,12*(views/100000)**0.35+18*(likes/max(views,1)*100)**0.25+35/(age**0.25)),2)
items={}
for q in QUERIES:
    try:
        s=api('search',{'part':'snippet','q':q,'type':'video','maxResults':50,'order':'relevance'})
    except Exception as e:
        print('search failed',q,e);continue
    ids=[x['id']['videoId'] for x in s.get('items',[]) if x.get('id',{}).get('videoId')]
    if not ids:continue
    v=api('videos',{'part':'snippet,contentDetails,statistics,status','id':','.join(ids)})
    for x in v.get('items',[]):
        title=x['snippet']['title'];low=title.lower()
        if not any(k in low for k in ['nepali','नेपाली','nepal']):continue
        if x.get('status',{}).get('embeddable') is False or x.get('status',{}).get('privacyStatus')!='public':continue
        vid=x['id'];pub=x['snippet'].get('publishedAt','');dt=datetime.fromisoformat(pub.replace('Z','+00:00')) if pub else datetime.now(timezone.utc);days=(datetime.now(timezone.utc)-dt).days
        st=x.get('statistics',{});items[vid]={'id':vid,'title':clean_title(title) or title,'youtubeVideoId':vid,'youtubeUrl':'https://www.youtube.com/watch?v='+vid,'thumbnail':f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg','creator':{'name':x['snippet'].get('channelTitle','YouTube Creator'),'channelId':x['snippet'].get('channelId',''),'url':'https://www.youtube.com/channel/'+x['snippet'].get('channelId','')},'description':x['snippet'].get('description','')[:500],'publishedDate':pub,'year':dt.year,'genre':['Nepali Cinema'],'views':int(st.get('viewCount',0)),'likes':int(st.get('likeCount',0)),'verified':False,'algorithm':{'trendingScore':score(st,days)}}
old={}
try:
    with open(OUT,encoding='utf-8') as f: old=json.load(f).get('movies',[])
except:pass
merged={m['id']:m for m in old}
merged.update(items)
movies=list(merged.values());movies.sort(key=lambda x:x.get('algorithm',{}).get('trendingScore',0),reverse=True)
os.makedirs('data',exist_ok=True)
with open(OUT,'w',encoding='utf-8') as f:json.dump({'movies':movies,'meta':{'updatedAt':datetime.now(timezone.utc).isoformat(),'count':len(movies),'source':'YouTube Data API'}},f,ensure_ascii=False,indent=2)
print('Catalog records:',len(movies))
