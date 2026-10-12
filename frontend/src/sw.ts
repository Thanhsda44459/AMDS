/// <reference lib="webworker" />
// Service Worker: precache app shell, POI NetworkFirst, audio CacheFirst theo ngôn ngữ.

import { cleanupOutdatedCaches, precacheAndRoute } from 'workbox-precaching'
import { registerRoute } from 'workbox-routing'
import { CacheFirst, NetworkFirst } from 'workbox-strategies'
import { ExpirationPlugin } from 'workbox-expiration'

declare const self: ServiceWorkerGlobalScope & { __WB_MANIFEST: Array<{ url: string; revision: string | null }> }

// Đổi build là dọn cache chunk cũ để không lẫn asset hai bản.
const BUILD_SYNC = 'quan4-build-v1'

precacheAndRoute(self.__WB_MANIFEST)
cleanupOutdatedCaches()
void caches.keys().then((ten) => {
  for (const t of ten) {
    if (t.startsWith('quan4-build-') && t !== BUILD_SYNC) void caches.delete(t)
  }
})

// POI đổi thường nên NetworkFirst 8s, giữ 15 phút.
registerRoute(
  ({ url }) => url.pathname === '/poi' || url.pathname === '/poi/load-all' || url.pathname === '/poi/delta',
  new NetworkFirst({
    cacheName: 'poi-load-all-cache',
    networkTimeoutSeconds: 8,
    plugins: [new ExpirationPlugin({ maxAgeSeconds: 15 * 60, maxEntries: 50 })],
  }),
)

// Tệp audio bất biến nên CacheFirst, phân mảnh theo ngôn ngữ, tối đa 3 shard.
registerRoute(
  ({ url }) => url.pathname.startsWith('/static/audio/'),
  async ({ request, url, event }) => {
    const lang = url.searchParams.get('l') ?? 'vi'
    const shard = `audio-pack-${lang}`
    const choPhep = (await caches.keys()).filter((t) => t.startsWith('audio-pack-'))
    if (!choPhep.includes(shard) && choPhep.length >= 3) {
      await caches.delete(choPhep.sort()[0])
    }
    const chienLuoc = new CacheFirst({
      cacheName: shard,
      plugins: [new ExpirationPlugin({ maxEntries: 300 })],
    })
    return chienLuoc.handle({ request, event } as never) as Promise<Response>
  },
)

// Gói bản đồ bất biến, tải một lần dùng mãi.
registerRoute(
  ({ url }) => url.pathname.startsWith('/maps/pack/'),
  new CacheFirst({
    cacheName: 'map-pack-cache',
    plugins: [new ExpirationPlugin({ maxEntries: 20 })],
  }),
)

self.addEventListener('message', (e) => {
  if (e.data === 'SKIP_WAITING') void self.skipWaiting()
})
