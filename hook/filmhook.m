// Film phone only: shows the Watch how button on enrollie.app inside this simulator's Safari, so the film shows the real page.
#import <Foundation/Foundation.h>
#import <WebKit/WebKit.h>
#import <objc/runtime.h>
static NSString *const kJS = @"(function(){if(location.hostname!=='enrollie.app')return;var go=function(){document.querySelectorAll('[data-view=\"ios-safari\"] [data-watch],[data-view=\"ios-safari\"] [data-watch-or]').forEach(function(e){if(e.hidden)e.hidden=false;});};go();new MutationObserver(go).observe(document.documentElement,{subtree:true,attributes:true,attributeFilter:['hidden'],childList:true});})();";
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
