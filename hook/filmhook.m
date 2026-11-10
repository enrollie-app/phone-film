// Film phone only: shows the Watch how button and the iOS 27 steps on the install page inside this simulator's Safari.
#import <Foundation/Foundation.h>
#import <WebKit/WebKit.h>
#import <objc/runtime.h>
#if defined(FILM_26) && defined(FILM_ES)
#define POINTER_LEFT "327px"
#define ROWS "var html=row(word('\\u2022\\u2022\\u2022'),'Toca \\u2022\\u2022\\u2022 abajo a la derecha')+row(icon('share'),'Toca Compartir')+row(icon('swipe'),'Desliza hacia arriba')+row(icon('add'),'Toca Agregar a inicio')+row(word('Agregar'),'Toca Agregar','Deja activado Abrir como app web.');"
#elif defined(FILM_26)
#define POINTER_LEFT "327px"
#define ROWS "var html=row(word('\\u2022\\u2022\\u2022'),'Tap \\u2022\\u2022\\u2022 at the bottom right')+row(icon('share'),'Tap Share')+row(icon('swipe'),'Swipe up')+row(icon('add'),'Tap Add to Home Screen')+row(word('Add'),'Tap Add','Keep Open as Web App on.');"
#elif defined(FILM_ES)
#define POINTER_LEFT "97px"
#define ROWS "var html=row(word('\\u2261'),'Toca \\u2261 en la barra de direcciones')+row(icon('share'),'Toca Compartir')+row(icon('swipe'),'Desliza hacia arriba')+row(icon('add'),'Toca Agregar a inicio')+row(word('Agregar'),'Toca Agregar','Deja activado Abrir como app web.');"
#else
#define POINTER_LEFT "97px"
#define ROWS "var html=row(word('\\u2261'),'Tap \\u2261 in the address bar')+row(icon('share'),'Tap Share')+row(icon('swipe'),'Swipe up')+row(icon('add'),'Tap Add to Home Screen')+row(word('Add'),'Tap Add','Keep Open as Web App on.');"
#endif
static NSString *const kJS = @"(function(){if(location.hostname!=='enrollie.app')return;"
  "var icon=function(n){return '<span class=\"glyph\"><svg aria-hidden=\"true\"><use href=\"#g-'+n+'\"></use></svg></span>';};"
  "var word=function(w){return '<span class=\"glyph glyph-word\">'+w+'</span>';};"
  "var row=function(g,t,s){return '<li>'+g+'<span><b>'+t+'</b>'+(s?'<small>'+s+'</small>':'')+'</span></li>';};"
  ROWS
  "var go=function(){document.querySelectorAll('[data-view=\"ios-safari\"] [data-watch],[data-view=\"ios-safari\"] [data-watch-or]').forEach(function(e){if(e.hidden)e.hidden=false;});"
  "var l=document.querySelector('[data-steps=\"ios\"]');if(l&&l.children.length&&!l.dataset.film){l.dataset.film='1';l.innerHTML=html;}"
  "var p=document.querySelector('[data-pointer]');if(p&&p.style.left!=='" POINTER_LEFT "'){p.style.left='" POINTER_LEFT "';}};"
  "go();new MutationObserver(go).observe(document.documentElement,{subtree:true,attributes:true,attributeFilter:['hidden'],childList:true});})();";
static id (*orig)(id, SEL, CGRect, WKWebViewConfiguration *);
static id hook(id self, SEL _cmd, CGRect f, WKWebViewConfiguration *c) {
  WKUserScript *s = [[WKUserScript alloc] initWithSource:kJS injectionTime:WKUserScriptInjectionTimeAtDocumentEnd forMainFrameOnly:YES];
  [c.userContentController addUserScript:s];
  return orig(self, _cmd, f, c);
}
__attribute__((constructor)) static void start(void) {
  Method m = class_getInstanceMethod([WKWebView class], @selector(initWithFrame:configuration:));
  orig = (void *)method_setImplementation(m, (IMP)hook);
  NSLog(@"filmhook on");
}
