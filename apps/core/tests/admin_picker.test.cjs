const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
function fixture(){
 const node=(extra={})=>Object.assign({value:'',checked:false,hidden:false,disabled:false,dataset:{},events:{},addEventListener(type,fn){this.events[type]=fn;},focus(){}},extra);
 const controls={};
 const get=s=>controls[s]||(controls[s]=node());
 const rows=Array.from({length:60},(_,i)=>{const box=node();return node({textContent:(i<30?'Čokolada ':'Voda ')+i,querySelector:()=>box,classList:{contains:()=>false}});});
 get('[data-picker-status]').dataset={selectedLabel:'selected',resultsLabel:'results'};
 const picker=node({querySelector:get,querySelectorAll:()=>rows});
 const document={querySelector:()=>picker,querySelectorAll:()=>[]};
 vm.runInNewContext(fs.readFileSync('static/admin/js/pages.js','utf8'),{document,Array,Set,Math,Boolean});
 return {rows,get,click:s=>get(s).events.click(),search:q=>{get('[data-picker-search]').value=q;get('[data-picker-search]').events.input();}};
}
test('pagination selects only shown rows and preserves choices across searching',()=>{
 const f=fixture();assert.equal(f.rows.filter(r=>!r.hidden).length,25);
 f.click('#kp-recommended-select-all, #kp-promo-select-all');
 assert.equal(f.rows.filter(r=>r.querySelector().checked).length,25);
 f.search('voda');assert.equal(f.rows.filter(r=>!r.hidden).length,25);
 assert.equal(f.rows.filter(r=>r.querySelector().checked).length,25);
 f.click('#kp-recommended-select-all, #kp-promo-select-all');
 assert.equal(f.rows.filter(r=>r.querySelector().checked).length,50);
 f.click('#kp-recommended-select-none, #kp-promo-select-none');
 assert.equal(f.rows.filter(r=>r.querySelector().checked).length,25);
});
test('search folds accents, selected-only view and empty results stay usable',()=>{
 const f=fixture();f.search('cokolada');assert.match(f.get('[data-picker-status]').textContent,/30 results/);
 f.click('#kp-recommended-select-all, #kp-promo-select-all');
 f.get('[data-picker-selected]').checked=true;f.get('[data-picker-selected]').events.change();
 assert.match(f.get('[data-picker-status]').textContent,/25 selected · 25 results/);
 f.search('does not exist');assert.equal(f.get('[data-picker-empty]').hidden,false);
 assert.equal(f.rows.filter(r=>r.querySelector().checked).length,25);
});
