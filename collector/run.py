"""GitHub-hosted public-page probe. Does not log in or bypass restrictions."""
import json,re,time,sys
from pathlib import Path
from datetime import datetime
from core import allowed_url,record
BASE=Path(__file__).resolve().parent
OUT=BASE.parent/'output'
def run():
 from playwright.sync_api import sync_playwright
 cfg=json.loads((BASE/'config.json').read_text(encoding='utf-8'));rows=[];notes=[];seen=set();restricted=False
 OUT.mkdir(exist_ok=True)
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True)
   page=browser.new_page(viewport={'width':1280,'height':850},timezone_id='Asia/Shanghai')
   extract=(BASE/'extract.js').read_text(encoding='utf-8')
   for index,url in enumerate(cfg['urls'][:int(cfg['max_notes'])]):
    result={'index':index+1,'complete':False,'status':'failed','observedComments':0}
    try:
     if not allowed_url(url):raise ValueError('invalid_url')
     page.goto(url,wait_until='domcontentloaded',timeout=45000)
     body=page.locator('body').inner_text(timeout=10000)
     if re.search(r'访问过于频繁|访问频繁|异常流量|安全验证|请完成验证|网络环境存在风险|账号异常|账号风险',body):
      result['status']='verification_or_access_limited';restricted=True;notes.append(result);break
     try:page.locator('#detail-desc').wait_for(state='visible',timeout=12000)
     except Exception:
      result['status']='login_required' if '登录' in body else 'body_unavailable';notes.append(result);continue
     match=re.search(r'/(?:explore|discovery/item)/([A-Za-z0-9]+)',page.url)
     if not match:result['status']='note_id_unavailable';notes.append(result);continue
     nid=match[1]
     if nid in seen:continue
     seen.add(nid);data=page.evaluate(extract);post_text=data['title']+'\n'+data['description']
     post=record('帖子',nid,'',url,post_text,data['rawDate']);post['versionConfirmed']=False
     if not post['date'] or post['date']>=cfg['start_date']:rows.append(post)
     found={};stable=0;reason='scroll_limit';limited=False
     for i in range(int(cfg['max_scrolls_per_note'])+1):
      body=page.locator('body').inner_text(timeout=10000)
      if re.search(r'访问过于频繁|访问频繁|异常流量|安全验证|请完成验证|网络环境存在风险',body):
       restricted=True;reason='access_limited';break
      data=page.evaluate(extract);before=len(found)
      for c in data['comments']:found[c['sourceId']]=c
      stable=stable+1 if before==len(found) else 0
      if data['loginLimited']:limited=True;reason='login_limited';break
      if stable>=2:reason='no_new_visible_comments';break
      if i==int(cfg['max_scrolls_per_note']):break
      page.evaluate('''() => {let n=document.querySelector('[id^="comment-"]')||document.querySelector('#detail-desc');while(n){if(n.scrollHeight>n.clientHeight+40&&/auto|scroll/.test(getComputedStyle(n).overflowY)){n.scrollBy(0,650);return;}n=n.parentElement;}window.scrollBy(0,650);}''')
      time.sleep(max(2,float(cfg['interval_seconds'])))
     for c in found.values():
      r=record('评论',c['sourceId'],nid,url,c['text'],c['rawDate'],post_text)
      if not r['date'] or r['date']>=cfg['start_date']:rows.append(r)
     result.update(noteId=nid,status='partial',observedComments=len(found),loginLimited=limited,stopReason=reason)
    except Exception:
     # Avoid dumping page URLs, tokens, raw text or stack traces into Actions logs.
     result['status']='navigation_or_extraction_failed'
    notes.append(result)
    if restricted:break
    time.sleep(max(2,float(cfg['interval_seconds'])))
   browser.close()
 finally:
  report={'allPlatformCoverage':False,'startDate':cfg['start_date'],'notes':notes,'retainedRecords':len(rows),'verificationBlocked':restricted,'status':('partial_comments_observed' if any(r['type']=='评论' for r in rows) else 'comments_not_observed') if rows else 'no_data'}
  (OUT/'feedback.json').write_text(json.dumps({'version':1,'records':rows},ensure_ascii=False,indent=2),encoding='utf-8')
  (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
  print('Retained records:',len(rows),'-- partial observations only; inspect report.json.')
 if not any(r['type']=='评论' for r in rows):
  print('::warning::No comments were observed. Collection is incomplete; this is not zero user feedback.')
 return 0 if any(r['type']=='评论' for r in rows) and not restricted else 2
if __name__=='__main__':sys.exit(run())
