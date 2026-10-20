// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
const escape=v=>String(v??'Unknown').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function adminPage(tab,rows,counts) {
 const e=escape,labels={review:'Needs review',queued:'Queued',published:'Published',github:'GitHub sources'};
 let page=`<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Pear · Report review</title><style>body{font:16px system-ui;background:#faf9f3;color:#263027;max-width:1050px;margin:40px auto;padding:0 24px}h1{font-size:36px}nav{display:flex;gap:20px;border-bottom:1px solid #ddd;padding:18px 0}a{color:#40643a}a[aria-current]{font-weight:bold}details{background:white;border-bottom:1px solid #ddd}summary{cursor:pointer;padding:18px;display:flex;justify-content:space-between;gap:20px}small{color:#66735f}.detail{padding:24px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f0f2ea;padding:16px}button{padding:12px;background:#40643a;color:white;border:0;border-radius:8px;cursor:pointer}input{padding:10px;min-width:280px}dt{font-weight:bold}dd{margin:4px 0 16px}</style><h1>Report review</h1><form action="/auth/logout" method="post"><button>Sign out</button></form><p>${counts.find(x=>x.state==='queued')?.count||0} reports queued for the next daily update.</p><nav>`;
 for(const [key,label] of Object.entries(labels))page+=`<a href="/admin?tab=${key}" ${key===tab?'aria-current="page"':''}>${label}${key==='github'?'':` (${counts.find(x=>x.state===key)?.count||0})`}</a>`;
 page+='</nav><p>Latest 200 records in this view. Notes remain private. Approval does not certify compatibility.</p>';
 for(const row of rows) {
  if(tab==='github') {
   page+=`<details><summary>${e(row.title)}<small>${e(row.kind)} · ${row.needs_review?'Needs review':'Linked'}</small></summary><div class="detail"><a href="${e(row.url)}" rel="noreferrer">Read original on GitHub</a><p>Updated: ${e(row.updated)}</p><p>Linked report: ${e(row.report_id||'None')}</p><form method="post"><input type="hidden" name="tab" value="github"><input type="hidden" name="action" value="link"><input type="hidden" name="sourceID" value="${e(row.id)}"><label>Existing Report ID <input name="reportID" required></label> <button>Link report</button></form></div></details>`;continue;
  }
  const r=JSON.parse(row.payload||'{}'),pub={...r};delete pub.note;
  const name=r.appID===3405340?'Megabonk':r.appID?`Steam App ${r.appID}`:'Game not shared';
  page+=`<details name="report"><summary><strong>${e(name)}</strong><small>${e(r.dateUTC||'Date not shared')} · ${e(r.processMinutes??'Unknown')} min process</small><span>${e(r.userResult)}</span></summary><div class="detail"><h2>Report details</h2><p>Report ID: ${e(row.id)} · Revision ${row.revision}</p><h3>Public fields after approval</h3><pre>${e(JSON.stringify(pub,null,2))}</pre><h3>Private note</h3><p>${e(r.note||'None')}</p>`;
  for(const action of tab==='review'?['approve']:tab==='queued'?['unqueue']:['withdraw'])page+=`<form method="post"><input type="hidden" name="id" value="${e(row.id)}"><input type="hidden" name="revision" value="${row.revision}"><input type="hidden" name="tab" value="${tab}"><input type="hidden" name="action" value="${action}"><button>${{approve:'Approve for next update',unqueue:'Cancel approval',withdraw:'Withdraw from next catalog update'}[action]}</button></form>`;
  page+='</div></details>';
 }
 if(!rows.length)page+='<p>No reports in this view.</p>';return page;
}
