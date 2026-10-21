"""Pure data normalization. No website requests or hidden-state access."""
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse
from uuid import uuid4

ALIASES={
 '有麦K歌':['有麦','k歌','唱歌'],'QQ音乐':['qq音乐'], '播客类应用':['播客'],
 '音源显示体验':['音源'],'百变小萤生图功能':['百变小萤','生图'],'发光小队':['发光小队'],
 '车模样式':['车模'],'快捷控制':['快捷控制'],'系统账户记忆':['账户记忆','账号记忆'],
 'lumo语音功能':['lumo','语音'],'lumo GPT':['gpt'],'惊喜问候':['惊喜问候'],
 '露营模式':['露营'],'尾门开启空间提醒':['尾门'],'能量回收显示':['能量回收显示'],
 '续航风险提醒':['续航风险'],'守卫模式':['守卫'],'车辆热点分享':['热点'],'换电体验':['换电']}

def allowed_url(url):
 try:
  p=urlparse(url);h=p.hostname or ''
  return p.scheme=='https' and any(h==d or h.endswith('.'+d) for d in ['xiaohongshu.com','xhslink.cn','xhslink.com'])
 except ValueError:return False

def day(raw, now=None, post=False):
 """Edited post timestamps are not publication dates. Keep unknown rather than guess."""
 now=now or datetime.now()
 if not raw or (post and '编辑' in raw):return '', 'unknown_or_edited'
 full=re.search(r'(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})',raw)
 try:
  if full:return datetime(*map(int,full.groups())).date().isoformat(),'exact'
  m=re.search(r'(\d+)天前',raw)
  if m:return (now-timedelta(days=int(m[1]))).date().isoformat(),'relative_estimate'
  if '昨天' in raw:return (now-timedelta(days=1)).date().isoformat(),'relative_estimate'
  if re.search(r'今天|刚刚|\d+分钟前|\d+小时前',raw):return now.date().isoformat(),'relative_estimate'
  m=re.search(r'(?<!\d)(\d{1,2})[-/月](\d{1,2})(?!\d)',raw)
  if m:
   d=datetime(now.year,int(m[1]),int(m[2]));d=d if d.date()<=now.date() else d.replace(year=now.year-1)
   return d.date().isoformat(),'year_inferred'
 except ValueError:pass
 return '', 'unknown'

def candidates(text, context=''):
 low=text.lower(); fs=[f for f,keys in ALIASES.items() if any(k in low for k in keys)]
 # Context can suggest the feature, but never supplies the attitude.
 if not fs: fs=[f for f,keys in ALIASES.items() if any(k in context.lower() for k in keys)]
 ss=[]
 if re.search(r'喜欢|很好用|很棒|不错|满意|太方便',text):ss.append('赞赏')
 if re.search(r'不支持|难用|不好用|卡顿|故障|失灵|失败|不满|太慢|用不了|bug|报错',text,re.I):ss.append('抱怨')
 if re.search(r'希望|建议|能不能增加|能否增加|想要|期待|许愿',text):ss.append('建议')
 if not fs and re.search(r'升级|更新|2\.1|故障',text):fs=['升级后其他问题（归因待核实）']
 if re.search(r'希望|想要|许愿|期待',text) and not fs:fs=['许愿：其他']
 return fs,ss

def record(kind, source_id, parent_id, url, text, raw_date, context='', now=None):
 date,quality=day(raw_date,now,post=kind=='帖子');fs,ss=candidates(text,context)
 return dict(id=str(uuid4()),type=kind,sourceId=source_id,parentId=parent_id,url=url,text=text,
  date=date,rawDate=raw_date,dateQuality=quality,features=fs,sentiments=ss,approved=False,
  context=context,collectionMethod='visible_browser_dom',versionConfirmed=False)

def key(r):return (r['type'],r.get('parentId','') if r['type']=='评论' else '',r['sourceId'])

def merge(old,new):
 """Refresh an observation; edits reset review. Keep unrelated historical records."""
 rows={key(r):r for r in old}
 for r in new:
  k=key(r);prev=rows.get(k)
  if prev and prev.get('text')==r['text']:
   r={**prev,**{x:r[x] for x in ['rawDate','dateQuality','context']},'lastSeenAt':datetime.now().astimezone().isoformat()}
  rows[k]=r
 return list(rows.values())
