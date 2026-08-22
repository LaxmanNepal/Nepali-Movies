import json, os, re, urllib.parse, urllib.request
from datetime import datetime, timezone
KEY=os.getenv('YOUTUBE_API_KEY'); OUT='data/movies.json'
if not KEY:
    print('YOUTUBE_API_KEY is not configured; keeping existing catalog.'); raise SystemExit(0)
QUERIES=['Nepali full movie official','Nepali full film official','नेपाली पूर्ण फिल्म','नेपाली चलचित्र full movie','Nepali movie complete film','Nepali classic full movie','Nepali new movie full']
BAD=re.compile(r'\b(trailer|teaser|song|songs|music|lyric|lyrics|clip|clips|scene|scenes|interview|reaction|review|shorts?|making|behind|promo|preview|episode|part\s*[0-9]+)\b',re.I)
GOOD=re.compile(r'\b(full movie|full film|complete movie|complete film|official movie|movie)\b',re.I)
NEP=re.compile(r'(nepali|nepal|नेपाली|नेपाल)',re.I)
def api(endpoint,params):
    p=dict(params,key=KEY); u='https://www.googleapis.com/youtube/v3/'+endpoint+'?'+urllib.parse.urlencode(p)
    with urllib.request.urlopen(u,timeout=30) as r:return json.load(r)
def duration_seconds(s):
    m=re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$',s or '')
    return (int(m.group(1) or 0)*3600+int(m.group(2) or 0)*60+int(m.group(3) or 0)) if m else 0
def clean_title(t):
    t=re.sub(r'\s*[|–-]\s*(full movie|official|nepali movie).*?$','',t,flags=re.I)
    t=re.sub(r'\s+',' ',t).strip(' -|')
    return t or 'Untitled Nepali Movie'
def score(st,days,duration):
    views=max(int(st.get('viewCount',0)),0); likes=max(int(st.get('likeCount',0)),0); age=max(days,1)
    engagement=(likes/max(views,1))*100
    length_bonus=8 if duration>=3600 else (4 if duration>=1800 else 0)
    return round(min(100,18*(views/100000)**0.35+18*engagement**0.25+42/(age**0.28)+length_bonus),2)
items={}
for q in QUERIES:
    try:s=api('search',{'part':'snippet','q':q,'type':'video','maxResults':50,'order':'relevance','safeSearch':'none'})
    except Exception as e: print('search failed',q,e); continue
    ids=[x['id']['videoId'] for x in s.get('items',[]) if x.get('id',{}).get('videoId')]
    if not ids:continue
    try:v=api('videos',{'part':'snippet,contentDetails,statistics,status','id':','.join(ids)})
    except Exception as e: print('video lookup failed',e);continue
    for x in v.get('items',[]):
        sn=x.get('snippet',{}); title=sn.get('title',''); low=title.lower(); dur=duration_seconds(x.get('contentDetails',{}).get('duration',''))
        if not NEP.search(title) or BAD.search(low) or not GOOD.search(low) or dur<900: continue
        status=x.get('status',{}); 
        if status.get('privacyStatus')!='public' or status.get('embeddable') is False: continue
        pub=sn.get('publishedAt',''); dt=datetime.fromisoformat(pub.replace('Z','+00:00')) if pub else datetime.now(timezone.utc); days=(datetime.now(timezone.utc)-dt).days
        st=x.get('statistics',{}); vid=x['id']; channel_id=sn.get('channelId',''); channel_name=sn.get('channelTitle','YouTube Creator')
        items[vid]={'id':vid,'title':clean_title(title),'youtubeVideoId':vid,'youtubeUrl':'https://www.youtube.com/watch?v='+vid,'thumbnail':f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg','creator':{'name':channel_name,'channelId':channel_id,'url':f'https://www.youtube.com/channel/{channel_id}' if channel_id else ''},'description':sn.get('description','')[:1000],'publishedDate':pub,'year':dt.year,'durationSeconds':dur,'genre':['Nepali Cinema'],'views':int(st.get('viewCount',0)),'likes':int(st.get('likeCount',0)),'verification':{'status':'unknown','method':'youtube-metadata','claim':'uploader-not-rights-holder'},'algorithm':{'trendingScore':score(st,days,dur)}}
old=[]
try:
    with open(OUT,encoding='utf-8') as f: old=json.load(f).get('movies',[])
except Exception: pass
merged={m['id']:m for m in old}
merged.update(items)
# Remove records that are now clearly invalid if re-discovered; keep older records until health checks are added.
movies=list(merged.values()); movies.sort(key=lambda x:x.get('algorithm',{}).get('trendingScore',0),reverse=True)
os.makedirs('data',exist_ok=True)
with open(OUT,'w',encoding='utf-8') as f: json.dump({'movies':movies,'meta':{'updatedAt':datetime.now(timezone.utc).isoformat(),'count':len(movies),'source':'YouTube Data API','verificationPolicy':'uploader is not assumed to be rights-holder'}},f,ensure_ascii=False,indent=2)
print('Catalog records:',len(movies),'new:',len(items))