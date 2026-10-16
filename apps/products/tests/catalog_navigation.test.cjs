const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
const source=fs.readFileSync(path.resolve(__dirname,'../../../static/js/catalog-navigation.js'),'utf8');
function setup(storage,url,isList=true) {
 const location=new URL(url), events={}, scroll=[];
 const document={getElementById:()=>isList?{}:null,addEventListener:(type,fn)=>events[type]=fn};
 const window={scrollY:1234,addEventListener:(type,fn)=>events[type]=fn,requestAnimationFrame:fn=>fn(),scrollTo:options=>scroll.push(options.top)};
 const sessionStorage={getItem:k=>storage[k]||null,setItem:(k,v)=>storage[k]=v,removeItem:k=>delete storage[k]};
 vm.runInNewContext(source,{document,window,location,URL,sessionStorage,Date,JSON});
 function click(attribute,href) {const link={href,hasAttribute:name=>name===attribute};events.click({target:{closest:()=>link}});}
 return {events,scroll,click};
}
test('return restores the saved position only for the exact filtered page',()=>{
 const storage={}, url='https://shop.example/proizvodi/?page=3&sort=price_asc';
 setup(storage,url).click('data-product-link','https://shop.example/proizvodi/item/');
 setup(storage,'https://shop.example/proizvodi/item/',false).click('data-catalog-back',url);
 const wrong=setup(storage,'https://shop.example/proizvodi/?page=1');wrong.events.pageshow();assert.deepEqual(wrong.scroll,[]);
 const returned=setup(storage,url);returned.events.pageshow();assert.deepEqual(returned.scroll,[1234]);
 returned.events.pageshow();assert.deepEqual(returned.scroll,[1234]);
});
test('a direct listing visit does not reuse an earlier browsing position',()=>{
 const storage={},url='https://shop.example/proizvodi/?page=3';
 setup(storage,url).click('data-product-link','https://shop.example/proizvodi/item/');
 const next=setup(storage,url);next.events.pageshow();assert.deepEqual(next.scroll,[]);
});
