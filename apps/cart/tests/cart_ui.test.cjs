// Run with: node --test apps/cart/tests/cart_ui.test.cjs
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.resolve(__dirname, '../../../static/js/cart.js'), 'utf8');
const tick = () => new Promise(resolve=>setImmediate(resolve));
function fixture() {
    function element(extra={}) { return Object.assign({dataset:{},disabled:false,isConnected:true,attrs:{},classList:{toggle(){},add(){},remove(){},contains(){return false;}},setAttribute(k,v){this.attrs[k]=v;},getAttribute(k){return this.attrs[k]||null;},removeAttribute(k){delete this.attrs[k];},querySelector(){return null;},querySelectorAll(){return [];},appendChild(){},remove(){},addEventListener(){},closest(){return null;}},extra); }
    const body=element(), nodes={};
    const drawer=element({getAttribute(name){return name==='data-cart-state-url'?'/state':'Please review your cart';},querySelector(selector){return nodes[selector]||(nodes[selector]=element());}});
    const notice=element({hidden:true,querySelector:selector=>nodes[selector]||(nodes[selector]=element())});
    const events={}, calls=[], opened=[];
    const document={body,readyState:'complete',activeElement:body,querySelector:s=>s==='[data-cart-drawer]'?drawer:s==='[data-cart-confirmation]'?notice:null,querySelectorAll:()=>[],getElementById:()=>null,createElement:()=>element(),addEventListener:(name,fn)=>events[name]=fn};
    const fetch=(url,options)=>new Promise((resolve,reject)=>calls.push({url,options,resolve,reject}));
    const window={bootstrap:{Offcanvas:{getOrCreateInstance:()=>({show:opener=>opened.push(opener)})}},fetch,FormData:class{},setTimeout(){},clearTimeout(){},requestAnimationFrame:fn=>fn()};
    vm.runInNewContext(source,{document,window,fetch,FormData:class {constructor(form){this.source=form.action;}},Promise,Array,Number,String,Error,Event:class{}});
    function form(id) {const button=element();return element({action:'/add/'+id,button,matches(){return true;},hasAttribute(name){return name==='data-shop-add-cart';},querySelectorAll:s=>s==='button, input:not([type=hidden])'?[button]:[]});}
    const submit=form=>events.submit({target:form,preventDefault(){}});
    const finish=(call, overrides={})=>call.resolve({ok:true,json:async()=>({ok:true,lines:[],item_count:0,subtotal_display:'0,00 RSD',message:'Added',...overrides})});
    return {calls,form,submit,finish,nodes,element,events,opened,document,notice};
}
test('two additions are serialized so the second request cannot overwrite an earlier cart session',async()=>{
    const f=fixture(), first=f.form('a'), second=f.form('b');
    f.submit(first); f.submit(second); await tick();
    assert.equal(f.calls.length,1); assert.equal(f.calls[0].url,'/add/a'); assert.equal(second.button.disabled,true);
    f.finish(f.calls[0]); await tick(); assert.equal(f.calls.length,2); assert.equal(f.calls[1].url,'/add/b');
    f.finish(f.calls[1]); await tick(); assert.equal(first.button.disabled,false); assert.equal(second.button.disabled,false);
});
test('a double click on the same form cannot send a duplicate addition',async()=>{
    const f=fixture(), form=f.form('a'); f.submit(form); f.submit(form); await tick();
    assert.equal(f.calls.length,1); f.finish(f.calls[0]); await tick(); assert.equal(form.button.disabled,false);
});
test('a lost POST response is reconciled with GET and is never retried as another addition',async()=>{
    const f=fixture(), form=f.form('a'); f.submit(form); await tick(); f.calls[0].reject(new Error('network')); await tick();
    assert.equal(f.calls.length,2); assert.equal(f.calls[1].url,'/state'); assert.equal(f.calls[1].options.method,'GET');
    f.finish(f.calls[1]); await tick(); assert.equal(f.calls.filter(call=>call.options.method==='POST').length,1); assert.equal(form.button.disabled,false);
});

test('refresh updates existing row unit price and total together without replacing its quantity control',async()=>{
    const f=fixture(), input=f.element({value:'1'}), unit=f.element({textContent:'100,00 RSD'}), total=f.element({textContent:'100,00 RSD'}), name=f.element({textContent:'Old name'});
    const row=f.element({dataset:{productId:'1'},querySelector(selector){
        if (selector==='input[name="quantity"]') return input;
        if (selector==='[data-cart-line-total]') return total;
        if (selector.includes('__unit')) return unit;
        if (selector.includes('__name')) return name;
        return null;
    }});
    f.nodes['[data-cart-drawer-lines]']=f.element({querySelectorAll:()=>[row],querySelector:()=>row});
    f.submit(f.form('a')); await tick();
    f.finish(f.calls[0],{item_count:1,subtotal_display:'125,50 RSD',lines:[{product_id:1,name:'Current name',url:'/current/',image_url:'',quantity:1,stock:5,unit_price_display:'125,50 RSD',line_total_display:'125,50 RSD'}]});
    await tick(); assert.equal(unit.textContent,'125,50 RSD'); assert.equal(total.textContent,'125,50 RSD');
    assert.equal(input.value,'1'); assert.equal(name.textContent,'Current name'); assert.equal(name.href,'/current/');
});


test('addition shows a non-blocking confirmation without opening the drawer or moving focus', async()=>{
    const f=fixture(), form=f.form('a'); f.document.activeElement=form.button;
    f.submit(form); await tick(); f.finish(f.calls[0]); await tick();
    assert.equal(f.opened.length,0); assert.equal(f.notice.hidden,false);
    assert.equal(f.document.activeElement,form.button);
    assert.equal(f.nodes['[data-cart-confirmation-message]'].textContent,'Added');
    assert.equal(f.nodes['[data-cart-confirmation-total]'].textContent,'0,00 RSD');
    f.notice.hidden=true;
    f.submit(form); await tick(); f.finish(f.calls[1],{ok:false,error:'Out of stock'}); await tick();
    assert.equal(f.notice.hidden,true); assert.equal(f.opened.length,0);
});

test('removal waits for an explicit confirmation and ignores a double confirmation',async()=>{
    const f=fixture(), trigger=f.element(), cancel=f.element({focus(){}});
    const panel=f.element({querySelector:()=>cancel});
    f.document.createElement=()=>panel;
    const form=f.form('remove');
    form.hasAttribute=name=>name==='data-cart-remove-form';
    let confirmation=null;
    form.querySelector=selector=>selector==='button[type=submit]'?trigger:selector==='[data-cart-remove-confirm]'?confirmation:null;
    form.appendChild=node=>confirmation=node;
    f.submit(form); await tick();
    assert.equal(f.calls.length,0); assert.equal(trigger.hidden,true);
    const target=f.element({closest:selector=>selector==='[data-cart-remove-yes]'?target:selector==='form'?form:null});
    f.events.click({target}); f.events.click({target}); await tick();
    assert.equal(f.calls.length,1); f.finish(f.calls[0]); await tick();
});


test('generic submit feedback leaves cart controls to the cart interaction handler',()=>{
    const attached=[];
    const forms=['data-shop-add-cart','data-cart-quantity-form','data-cart-remove-form','ordinary'];
    const document={addEventListener:(event,init)=>init(),querySelectorAll:()=>forms.map(type=>({
        hasAttribute:name=>name===type,closest:()=>null,addEventListener:()=>attached.push(type)
    }))};
    vm.runInNewContext(fs.readFileSync(path.resolve(__dirname,'../../../static/js/main.js'),'utf8'),{document});
    assert.deepEqual(attached,['ordinary']);
});
