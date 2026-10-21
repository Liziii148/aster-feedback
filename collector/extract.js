() => {
 const visible=e=>!!(e&&(e.offsetWidth||e.offsetHeight||e.getClientRects().length));
 const text=e=>e?.innerText?.trim()||'';
 const desc=document.querySelector('#detail-desc');
 const dates=[...document.querySelectorAll('.date')].filter(e=>visible(e)&&!e.closest('[id^="comment-"]'));
 const comments=[...document.querySelectorAll('[id^="comment-"]')].filter(visible).map(e=>({
  sourceId:e.id.replace(/^comment-/,''),text:text(e.querySelector('.content')),
  rawDate:text(e.querySelector('.date span:first-child'))||text(e.querySelector('.date')),
  reply:e.classList.contains('comment-item-sub')
 })).filter(e=>e.sourceId&&e.text);
 return {title:text(document.querySelector('#detail-title')),description:text(desc),rawDate:text(dates[0]),comments,
  loginLimited:[...document.querySelectorAll('button,div,span')].some(e=>visible(e)&&e.childElementCount===0&&/登录查看全部评论内容/.test(text(e))),
  pageText:document.body.innerText.slice(0,30000)};
}
