
var staticCacheName = "django-pwa-vd3547c2";
var filesToCache = [
    '/offline/',
    '/static/css/django-pwa-app.css',
    '/static/images/icons/icon-72x72.png',
    '/static/images/icons/icon-96x96.png',
    '/static/images/icons/icon-128x128.png',
    '/static/images/icons/icon-144x144.png',
    '/static/images/icons/icon-152x152.png',
    '/static/images/icons/icon-192x192.png',
    '/static/images/icons/icon-384x384.png',
    '/static/images/icons/icon-512x512.png',
    '/static/images/icons/splash-640x1136.png',
    '/static/images/icons/splash-750x1334.png',
    '/static/images/icons/splash-1242x2208.png',
    '/static/images/icons/splash-1125x2436.png',
    '/static/images/icons/splash-828x1792.png',
    '/static/images/icons/splash-1242x2688.png',
    '/static/images/icons/splash-1536x2048.png',
    '/static/images/icons/splash-1668x2224.png',
    '/static/images/icons/splash-1668x2388.png',
    '/static/images/icons/splash-2048x2732.png',
    '/static/node_configuration/style.css',
    '/static/bootstrap.min.css',
    '/static/bootstrap-icons.css',
    '/static/bootstrap.bundle.min.js',
    '/static/bootstrap.min.js',
    '/static/jquery.min.js',
    '/static/smoothscroll.min.js',
    '/static/rangeslider.min.js',
    '/static/api/animations.css',
    '/static/api/loading.css',
    '/static/api/overview.css',
    '/static/api/remote.css',
    '/static/api/sliders.css',
    '/static/api/style.css',
    '/static/api/api_card.js',
    '/static/api/record_macro.js',
    '/static/api/rule_sliders.js',
    '/static/api/schedule_rules.js',
    '/static/api/update_status.js',
    '/static/node_configuration/style.css',
    '/static/node_configuration/add-instance.js',
    '/static/node_configuration/apiTargetOptions.js',
    '/static/node_configuration/classes.js',
    '/static/node_configuration/page-buttons.js',
    '/static/node_configuration/rule_sliders.js',
    '/static/node_configuration/schedule-rules.js',
    '/static/node_configuration/submit.js',
    '/static/node_configuration/upload.js',
    '/static/node_configuration/validate.js',
];

// Cache on install
self.addEventListener("install", event => {
    this.skipWaiting();
    event.waitUntil(
        caches.open(staticCacheName)
            .then(cache => {
                return cache.addAll(filesToCache);
            })
    )
});

// Clear cache on activate
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames
                    .filter(cacheName => (cacheName.startsWith("django-pwa-")))
                    .filter(cacheName => (cacheName !== staticCacheName))
                    .map(cacheName => caches.delete(cacheName))
            );
        })
    );
});

// Serve from Cache
self.addEventListener("fetch", event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                return response || fetch(event.request);
            })
            .catch(() => {
                return caches.match('/offline/');
            })
    )
});
