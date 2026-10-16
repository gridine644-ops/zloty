// Złoty Plan offline cache: the page is fetched fresh when online and served from cache offline.
var CACHE = 'zloty-v3';
var CORE = ['./', './index.html', './manifest.webmanifest', './icon-180.png', './icon-192.png', './icon-512.png'];
self.addEventListener('install', function(e){ e.waitUntil(caches.open(CACHE).then(function(c){ return c.addAll(CORE); })); self.skipWaiting(); });
self.addEventListener('activate', function(e){ e.waitUntil(caches.keys().then(function(ks){ return Promise.all(ks.filter(function(k){ return k !== CACHE; }).map(function(k){ return caches.delete(k); })); })); self.clients.claim(); });
self.addEventListener('fetch', function(e){
  var req = e.request; if (req.method !== 'GET') return;
  if (req.mode === 'navigate'){
    e.respondWith(fetch(req).then(function(r){ var cp = r.clone(); caches.open(CACHE).then(function(c){ c.put('./index.html', cp); }); return r; })
      .catch(function(){ return caches.match('./index.html'); }));
    return;
  }
  e.respondWith(caches.open(CACHE).then(function(c){
    return c.match(req).then(function(hit){
      var net = fetch(req).then(function(r){ if (r && (r.ok || r.type === 'opaque')) c.put(req, r.clone()); return r; }).catch(function(){ return hit; });
      return hit || net;
    });
  }));
});
