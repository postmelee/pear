// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Synthetic local UI only; no external submission or compatibility claim.
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const {execFileSync} = require('node:child_process');
const source = execFileSync('python3', ['-c', "import sys;sys.path.insert(0,'tools');import catalog_locale;print(catalog_locale.javascript_messages())"], {cwd: require('node:path').resolve(__dirname, '../..'), encoding:'utf8'});
function context(lang) { const ctx = {document:{documentElement:{lang}}}; vm.createContext(ctx); vm.runInContext(source, ctx); return ctx; }
test('search and Steam statuses translate dynamically and preserve names/IDs', () => {
  const t = context('ko').PearI18n.t;
  assert.equal(t('3 results'), '검색 결과 3개');
  assert.equal(t('Steam App 3405340 · You can submit by ID. The name will be checked before publication.'), 'Steam App 3405340 · ID만으로 제출할 수 있습니다. 이름은 공개 전에 확인합니다.');
  assert.equal(t('Games selected · Steam App 10'), 'Games 선택됨 · Steam App 10');
  assert.match(t('Up to 8 suggestions. Loading Steam game list…'), /^최대 8개 추천/);
  assert.match(t('0 results — try a page, game, or topic such as Rosetta.'), /^검색 결과가 없습니다/);
  assert.equal(context('en').PearI18n.t('3 results'), '3 results');
});
test('Korean draft keeps GitHub field vocabulary, result values and raw user text', () => {
  const ctx=context('ko');
  const nodes = new Map();
  function node() {return {value:'', dataset:{}, hidden:false, events:{}, setAttribute(){}, removeAttribute(){}, addEventListener(k,f){this.events[k]=f;}, setCustomValidity(v){this.validity=v;}, reportValidity(){return true;}, focus(){}, scrollIntoView(){}};}
  for (const id of ['intake','game-name','app-id','steam-identity','identity-status','steam-game-link','steam-search','steam-results','steam-search-status','retry-steam-search','draft-body','draft-title','copy-status','duration','result','draft','copy-title','copy-body','github-handoff']) nodes.set('#'+id,node());
  const picker=node();picker.dataset.games=JSON.stringify([{app_id:'3405340',name:'Megabonk'}]);picker.dataset.steamIndex='';nodes.set('.game-picker',picker);
  nodes.get('#intake').dataset.kind='report';
  ctx.document.querySelector=s=>nodes.get(s)||null;ctx.document.querySelectorAll=()=>[];
  ctx.URL=URL;ctx.URLSearchParams=URLSearchParams;ctx.location={search:''};ctx.setTimeout=setTimeout;ctx.clearTimeout=clearTimeout;
  ctx.PearSteamSearch={index:x=>x};ctx.FormData=class {get(k){return ({game:nodes.get('#game-name').value,app:nodes.get('#app-id').value,date:'2026-10-20',track:'Rosetta Preview',environment:'합성 환경',versions:'0.1.0',result:'Active gameplay',minutes:'21',input:'Observed',audio:'Not tested',save_reload:'Failed',recovery:'Not tested',settings:'Download',steps:'게임 메모 <script> 원문'})[k]||'';}};
  vm.runInContext(fs.readFileSync(require('node:path').resolve(__dirname,'../../tools/catalog/catalog.js'),'utf8'),ctx);
  nodes.get('#steam-identity').value='https://store.steampowered.com/app/3405340/';nodes.get('#result').value='Active gameplay';nodes.get('#duration').value='21';
  nodes.get('#intake').events.submit({preventDefault(){}});
  const draft=nodes.get('#draft-body').value;
  assert.match(draft,/Steam App ID: 3405340/);assert.match(draft,/## Runtime path\nRosetta Preview/);assert.match(draft,/Active gameplay/);assert.match(draft,/Input: Observed/);assert.match(draft,/Save \/ reload: Failed/);assert.match(draft,/게임 메모 <script> 원문/);
  assert.equal(nodes.get('#draft-title').value,'[Game report] Megabonk (3405340)');assert.match(nodes.get('#copy-status').textContent,/초안/);
});
