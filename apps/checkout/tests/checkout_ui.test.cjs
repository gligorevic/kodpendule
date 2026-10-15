// Run with: node --test apps/checkout/tests/checkout_ui.test.cjs
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.resolve(__dirname, '../../../static/js/checkout.js'), 'utf8');
function fixture({subtotal='1234.56',rules={base:'450.00',threshold:'',discounted_shipping_price:'',threshold_shipping_mode:'free'}}={}) {
    function element(extra={}) { return Object.assign({hidden:false,disabled:false,dataset:{},textContent:'',events:{},classList:{toggle(){},add(){},remove(){}},addEventListener(name,fn){this.events[name]=fn;},setAttribute(){},removeAttribute(){}},extra); }
    const button=element(), saving=element(), timing=element({value:'same_day'});
    const city=element({value:''}), date=element({value:'',checkValidity(){return /^\d{4}-\d{2}-\d{2}$/.test(this.value);}}), dateRow=element();
    const shipping=element(), total=element();
    const hint=element({dataset:{msgScheduledFree:'Scheduled free',msgFree:'Free',msgDiscounted:'Discounted',msgRemaining:'Add __AMOUNT__ RSD'}});
    const summary=element({dataset:{checkoutSubtotal:subtotal,currency:'RSD',totalPending:'Choose details',cityPending:'Choose city',datePending:'Choose date'}});
    const form=element({querySelector(s){return s==='[data-checkout-saving]'?saving:s.includes(':checked')?timing:null;},querySelectorAll(){return [timing];}});
    const ids={'shop-checkout-form':form,id_shipping_city:city,id_requested_delivery_date:date,'shop-delivery-date-row':dateRow,'checkout-shipping-hint':hint,'city-delivery-data':{textContent:JSON.stringify({'1':rules})},'checkout-today-data':{textContent:'"2026-10-15"'}};
    const windowEvents={};
    const document={getElementById:id=>ids[id],querySelector:()=>summary,querySelectorAll:s=>s==='.js-shipping-price'?[shipping]:s==='[data-checkout-total]'?[total]:[button],addEventListener:(name,fn)=>fn()};
    vm.runInNewContext(source,{document,window:{addEventListener:(name,fn)=>windowEvents[name]=fn}});
    return {city,date,dateRow,timing,total,shipping,hint,form,button,saving,windowEvents,refresh(){city.events.change();}};
}
test('decimal subtotal stays exact, city is required before quoting a total',()=>{
    const f=fixture(); assert.equal(f.total.textContent,'Choose details'); assert.equal(f.shipping.textContent,'Choose city');
    f.city.value='1'; f.refresh(); assert.equal(f.shipping.textContent,'450,00 RSD'); assert.equal(f.total.textContent,'1.684,56 RSD');
});
test('an incomplete or past scheduled date cannot masquerade as a same-day quote',()=>{
    const f=fixture(); f.city.value='1'; f.timing.value='scheduled'; f.refresh();
    assert.equal(f.dateRow.hidden,false); assert.equal(f.date.required,true); assert.equal(f.total.textContent,'Choose details');
    f.date.value='2026-10-14'; f.refresh(); assert.equal(f.total.textContent,'Choose details');
    f.date.value='2026-10-16'; f.refresh(); assert.equal(f.shipping.textContent,'0,00 RSD'); assert.equal(f.total.textContent,'1.234,56 RSD');
    f.timing.value='same_day'; f.refresh(); assert.equal(f.date.disabled,true); assert.equal(f.total.textContent,'1.684,56 RSD');
});
test('same-day free and discounted thresholds match the server rules, including a zero discount price',()=>{
    for (const [mode,discount,expected] of [['free','199.00','1.234,56 RSD'],['discounted','199.00','1.433,56 RSD'],['discounted','0.00','1.234,56 RSD'],['discounted','','1.684,56 RSD']]) {
        const f=fixture({rules:{base:'450.00',threshold:'1000.00',discounted_shipping_price:discount,threshold_shipping_mode:mode}});
        f.city.value='1'; f.refresh(); assert.equal(f.total.textContent,expected);
    }
});
test('duplicate form submission is stopped; browser Back restores usable controls',()=>{
    const f=fixture(); let prevented=0;
    f.form.events.submit({preventDefault(){prevented++;}}); assert.equal(f.button.disabled,true); assert.equal(f.saving.hidden,false);
    f.form.events.submit({preventDefault(){prevented++;}}); assert.equal(prevented,1);
    f.windowEvents.pageshow(); assert.equal(f.button.disabled,false); assert.equal(f.saving.hidden,true);
});
