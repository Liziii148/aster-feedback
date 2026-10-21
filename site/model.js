(function(root){'use strict';
const GROUPS=[['生态应用',['有麦K歌','QQ音乐','播客类应用','音源显示体验']],['个性系统',['百变小萤生图功能','发光小队','车模样式','快捷控制','系统账户记忆']],['语音交互',['lumo语音功能','lumo GPT']],['智能场景',['惊喜问候','露营模式']],['整车体验',['尾门开启空间提醒','能量回收显示','续航风险提醒','守卫模式','车辆热点分享','换电体验']],['其他系统反馈',['升级后其他问题（归因待核实）','其他车机功能']],['新功能许愿',['许愿：导航与智驾','许愿：影音与应用','许愿：语音与AI','许愿：个性化与交互','许愿：安全与车辆控制','许愿：充电与续航','许愿：其他']]];
const FEATURES=GROUPS.flatMap(x=>x[1]), SENTIMENTS=['赞赏','抱怨','建议','中性/操作说明'];
const aliases={'有麦K歌':['有麦','k歌','ktv'],'QQ音乐':['qq音乐'],'播客类应用':['播客'],'音源显示体验':['音源'],'百变小萤生图功能':['百变小萤','生图'],'发光小队':['发光小队'],'车模样式':['车模'],'快捷控制':['快捷控制'],'系统账户记忆':['账户记忆','账号记忆'],'lumo语音功能':['lumo','语音'],'lumo GPT':['gpt'],'惊喜问候':['惊喜问候'],'露营模式':['露营模式'],'尾门开启空间提醒':['尾门'],'能量回收显示':['能量回收显示'],'续航风险提醒':['续航风险'],'守卫模式':['守卫','哨兵'],'车辆热点分享':['热点'],'换电体验':['换电']};
const signal=/系统|升级|更新|车机|紫菀|aster|ota|2[.．]1|210|lumo|gpt|语音|导航|地图|快捷|账户|账号|记忆|k歌|ktv|有麦|音乐|播客|音源|小萤|发光小队|车模|问候|露营|尾门|能量回收|动能回收|续航提醒|续航风险|守卫|哨兵|热点|换电|软件|蓝牙|连接|投屏|许愿|功能|空调|温控|屏幕/i;
function url(v){try{const u=new URL(v);return u.protocol==='https:'&&['xiaohongshu.com','xhslink.cn','xhslink.com'].some(d=>u.hostname===d||u.hostname.endsWith('.'+d))?u.href:''}catch{return ''}}
function key(r){return [r.type,r.type==='评论'?r.parentId:'',r.sourceId||new URL(r.url).pathname].join('|')}
function validDate(v){return !v||/^\d{4}-\d{2}-\d{2}$/.test(v)&&Number.isFinite(Date.parse(v))&&new Date(v).toISOString().slice(0,10)===v}
function suggest(r){const text=(r.text||r.title||'').toLowerCase();let fs=Object.entries(aliases).filter(([,a])=>a.some(k=>text.includes(k))).map(([f])=>f);if(!fs.length&&signal.test(text))fs=[/许愿|希望增加|想要增加/.test(text)?'许愿：其他':'其他车机功能'];return fs.map(feature=>({feature,sentiments:[]}))}
function normalize(x,{restore=false}={}){
 if(!x||typeof x!=='object')throw Error('原声必须是对象');
 const u=url(x.url);if(!u)throw Error('存在无效的小红书HTTPS链接');
 const type=x.type||'帖子';if(!['帖子','评论'].includes(type))throw Error('原声类型须为帖子或评论');
 const sourceId=String(x.sourceId||'').trim(),parentId=String(x.parentId||'').trim();if(type==='评论'&&(!sourceId||!parentId))throw Error('评论必须包含评论ID和所属帖子ID');
 const date=String(x.date||'');if(!validDate(date))throw Error('日期无效，应为YYYY-MM-DD或空');
 const text=typeof x.text==='string'?x.text:'',title=String(x.title||'');if(!text.trim()&&!title.trim())throw Error('原声缺少标题或正文');
 let labels;if(Array.isArray(x.labels))labels=x.labels;else labels=(Array.isArray(x.features)?x.features:[]).map(feature=>({feature,sentiments:Array.isArray(x.sentiments)?x.sentiments:[]}));
 for(const l of labels)if(!l||!FEATURES.includes(l.feature)||!Array.isArray(l.sentiments)||l.sentiments.some(s=>!SENTIMENTS.includes(s)))throw Error('标签中存在未支持的功能或态度');
 labels=labels.map(l=>({feature:l.feature,sentiments:[...new Set(l.sentiments)]}));
 const r={...x,type,sourceId,parentId,url:u,date,title,text,labels,context:String(x.context||''),rawDate:String(x.rawDate||''),bodyStatus:x.bodyStatus||'loaded',systemVersion:['2.1.0','other','unknown'].includes(x.systemVersion)?x.systemVersion:'unknown',relevance:['system','unrelated','unknown'].includes(x.relevance)?x.relevance:'unknown',status:restore&&['pending','approved','excluded'].includes(x.status)?x.status:'pending',id:key({type,sourceId,parentId,url:u}),candidate:typeof x.candidate==='boolean'?x.candidate:labels.length>0||signal.test(text+' '+title+' '+String(x.context||'')),reason:String(x.reason||'')};
 if(!r.labels.length&&r.candidate)r.labels=suggest(r);
 if(!r.reason)r.reason=r.candidate?'文本出现系统/功能相关信号，需确认上下文及版本':'尚未发现明确系统信号，保留在全部语料，未自动排除';
 return r;
}
function canApprove(r){if(r.mediaNeedsReview&&!r.mediaReviewed)return '请先打开原文查看图片/视频，并勾选已核对媒体内容';if(r.bodyStatus==='card_only')return '仅有搜索卡片，尚未读取正文，不能作为已复核原声';if(r.relevance!=='system')return '请先确认是否与系统/功能有关';if(!r.labels.length||r.labels.some(l=>!FEATURES.includes(l.feature)||!l.sentiments.length))return '请为每项功能选择态度，操作说明可选择中性';return ''}
function inRange(r,from,to,unknown=false){if(!r.date)return unknown;if(from&&r.date<from)return false;if(to&&r.date>to)return false;return true}
function eligible(r,{from='',to='',version='2.1.0',feature=''}={}){return r.status==='approved'&&r.relevance==='system'&&r.bodyStatus!=='card_only'&&(!r.mediaNeedsReview||r.mediaReviewed)&&r.date&&inRange(r,from,to)&&(feature.startsWith('许愿：')||(r.systemVersion!=='unknown'&&(version==='all'||r.systemVersion===version)))}
function count(records,feature,sentiment,type,opts){return new Set(records.filter(r=>eligible(r,{...opts,feature})&&(!type||r.type===type)&&r.labels.some(l=>l.feature===feature&&(!sentiment||l.sentiments.includes(sentiment))&&l.sentiments.some(s=>s!=='中性/操作说明'))).map(key)).size}
function merge(existing,incoming){const m=new Map(existing.map(r=>[key(r),r]));let added=0,updated=0,duplicate=0;for(const x of incoming){const k=key(x),old=m.get(k);if(!old){m.set(k,x);added++}else if((old.bodyStatus==='card_only'&&x.bodyStatus!=='card_only')||old.text!==x.text){m.set(k,{...x,status:'pending'});updated++}else if(old.status==='pending'&&!old.manualTouched&&['candidate','labels','relevance','reason','systemVersion','mediaNeedsReview'].some(f=>JSON.stringify(old[f])!==JSON.stringify(x[f]))){m.set(k,{...old,...x,status:'pending'});updated++}else duplicate++}return {records:[...m.values()],added,updated,duplicate}}
const api={GROUPS,FEATURES,SENTIMENTS,aliases,signal,url,key,validDate,suggest,normalize,canApprove,inRange,eligible,count,merge};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.ReviewModel=api;
})(typeof window!=='undefined'?window:globalThis);
