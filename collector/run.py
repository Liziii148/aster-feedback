"""Broad public search -> corpus -> system/function candidates. No authentication bypass."""
import json,re,time,sys
from pathlib import Path
from urllib.parse import quote
from datetime import datetime
from core import day,record,allowed_url
from screen import screen
BASE=Path(__file__).resolve().parent;OUT=BASE.parent/'output'
CARDS='''() => [...document.querySelectorAll('a.cover[href*="/search_result/"]')].filter(a=>a.getClientRects().length).map(a=>({sourceId:(a.getAttribute('href').match(/\\/search_result\\/([0-9a-f]{24})/)||[])[1],url:a.href,title:a.parentElement.querySelector('.title')?.innerText||'',rawDate:a.parentElement.querySelector('.time')?.innerText||''}))'''
BLOCK=re.compile(r'访问过于频繁|访问频繁|异常流量|安全验证|请完成验证|网络环境存在风险|账号异常|账号风险')
def run():
 from playwright.sync_api import sync_playwright
 cfg=json.loads((BASE/'config.json').read_text(encoding='utf-8'));OUT.mkdir(exist_ok=True);rows=[];cards={};report={'allPlatformCoverage':False,'startDate':cfg['start_date'],'queries':[],'readFailures':[],'dateUnknown':0,'commentsCollected':0,'stopReason':'finished_with_limits','authentication':'public_pages_only'}
 def save():
  payload={'version':3,'records':rows,'coverage':report}
  (OUT/'corpus.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
  (OUT/'system-candidates.json').write_text(json.dumps({**payload,'records':[r for r in rows if r.get('candidate')]},ensure_ascii=False,indent=2),encoding='utf-8')
  (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True);page=browser.new_page(viewport={'width':1280,'height':850},timezone_id='Asia/Shanghai')
   for keyword in cfg['keywords']:
    q={'keyword':keyword,'sort':'default_comprehensive','loadedCards':0,'rounds':0,'stopReason':'round_limit'};report['queries'].append(q);stable=0
    page.goto('https://www.xiaohongshu.com/search_result?keyword='+quote(keyword),wait_until='domcontentloaded',timeout=45000)
    try:page.locator('a.cover[href*="/search_result/"]').first.wait_for(state='visible',timeout=12000)
    except Exception:q['stopReason']='no_visible_results_or_login_required';continue
    seen=set()
    for turn in range(cfg['search_scroll_rounds']):
     body=page.locator('body').inner_text(timeout=10000)
     if BLOCK.search(body):q['stopReason']='access_limited';report['stopReason']='access_limited';save();return 2
     batch=page.evaluate(CARDS);before=len(seen)
     for c in batch:
      if not c['sourceId']:continue
      seen.add(c['sourceId']);date,quality=day(c['rawDate']);c.update(date=date,dateQuality=quality)
      if not date or date>=cfg['start_date']:
       old=cards.get(c['sourceId'],{});c['queries']=list(dict.fromkeys(old.get('queries',[])+[keyword]));cards[c['sourceId']]=c
     stable=stable+1 if len(seen)==before else 0;q.update(loadedCards=len(seen),rounds=turn+1)
     if stable>=3:q['stopReason']='no_new_visible_results';break
     page.mouse.wheel(0,1600);time.sleep(cfg['interval_seconds'])
    save()
   # Explicit seed links supplement, never replace broad keyword discovery.
   for i,u in enumerate(cfg.get('urls',[])):
    cards['seed-'+str(i)]={'url':u,'sourceId':'','title':'','rawDate':'','queries':['user_seed']}
   report['recentOrUnknownDiscovered']=len(cards)
   for index,c in enumerate(cards.values()):
    if index>=cfg['max_notes']:report['stopReason']='note_limit';break
    result=None
    try:
     if not allowed_url(c['url']):continue
     page.goto(c['url'],wait_until='domcontentloaded',timeout=45000)
     body=page.locator('body').inner_text(timeout=10000)
     if BLOCK.search(body):report['stopReason']='access_limited';break
     page.locator('#detail-desc').wait_for(state='visible',timeout=12000)
     data=page.evaluate((BASE/'extract.js').read_text(encoding='utf-8'))
     match=re.search(r'/(?:explore|search_result|discovery/item)/([A-Za-z0-9]+)',page.url);nid=match[1] if match else c['sourceId']
     if not nid:continue
     text=(data['title']+'\n'+data['description']).strip();raw=data['rawDate'] or c['rawDate'];date,quality=day(raw,post=True)
     if date and date<cfg['start_date']:continue
     result=record('帖子',nid,'',c['url'],text or c['title'] or '无标题，正文待读取',raw)
     result.update(title=data['title'] or c['title'],bodyStatus='loaded' if text else 'card_only',queries=c['queries'],systemVersion='unknown',relevance='unknown',status='pending')
    except Exception:
     report['readFailures'].append({'sourceId':c['sourceId'],'reason':'navigation_or_body_unavailable'})
     if c['sourceId']:
      result=record('帖子',c['sourceId'],'',c['url'],c['title'] or '无标题，正文待读取',c['rawDate']);result.update(title=c['title'],bodyStatus='card_only',queries=c['queries'])
    if result:
     result['candidate'],result['reason']=screen(result['text']);result['dateQuality']=result.get('dateQuality','unknown');rows.append(result)
     report['dateUnknown']=sum(not r.get('date') for r in rows)
    save();time.sleep(cfg['interval_seconds'])
   browser.close()
 finally:
  rows=list({(r['type'],r['sourceId']):r for r in rows}.values());report['retainedPosts']=len(rows);report['systemCandidates']=sum(bool(r.get('candidate')) for r in rows);report['status']='partial_corpus_no_comment_collection';save()
  print('::warning::This run collects publicly visible post text only, not complete search coverage or comments. Read report.json.')
 return 0 if rows and report['stopReason']!='access_limited' else 2
if __name__=='__main__':sys.exit(run())
