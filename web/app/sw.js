// Film-only stand-in for Enrollie's alert worker: shows the real test alert's words (packages/tell/src/alert-setup.ts).
const WORDS = { en: ["Test alert", "If this stayed on screen, you're set."], es: ["Alerta de prueba", "Si se quedó en la pantalla, todo está listo."] };
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(clients.claim()));
self.addEventListener("message", (e) => {
  const [title, body] = WORDS[e.data && e.data.lang === "es" ? "es" : "en"];
  e.waitUntil(new Promise((r) => setTimeout(r, (e.data && e.data.delay) || 5000)).then(() =>
    self.registration.showNotification(title, { body, icon: "/app/icons/icon-192.png", badge: "/app/icons/icon-192.png", tag: "alert-setup" })));
});
self.addEventListener("notificationclick", (e) => { e.notification.close(); e.waitUntil(clients.openWindow("/app/")); });
