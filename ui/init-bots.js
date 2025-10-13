// Auto-register bots into FreqUI on page load and prefill login details.
(function () {
  const bots = [
    { name: 'freqtrade-trader-ichi_v_1', url: 'http://localhost:8081' },
    { name: 'freqtrade-trader-lookahead_strategy', url: 'http://localhost:8082' },
    { name: 'freqtrade-trader-macd', url: 'http://localhost:8083' },
    { name: 'freqtrade-trader-custom_stoploss_with_psar', url: 'http://localhost:8084' },
    { name: 'freqtrade-trader-macdcci', url: 'http://localhost:8085' },
  ];

  // Expose for UI components that might read this
  window.freqtradeBots = bots.map(b => ({ name: b.name, apiUrl: b.url }));

  // Seed localStorage so the bots list shows up immediately and login dialog is prefilled
  try {
    const storeKey = 'ftAuthLoginInfo';
    const existing = JSON.parse(localStorage.getItem(storeKey) || '{}');
    let changed = false;
    const entries = bots.map((b, idx) => {
      const id = `ftbot.${idx + 1}`;
      const current = existing[id] || {};
      const desired = {
        botName: b.name,
        apiUrl: b.url,
        username: 'fq',
        accessToken: current.accessToken || '',
        refreshToken: current.refreshToken || '',
        autoRefresh: true,
        sortId: idx,
      };
      return { id, desired };
    });

    entries.forEach(({ id, desired }) => {
      if (JSON.stringify(existing[id] || {}) !== JSON.stringify(desired)) {
        existing[id] = desired;
        changed = true;
      }
    });
    if (changed) localStorage.setItem(storeKey, JSON.stringify(existing));

    // Select first bot by default
    localStorage.setItem('ftSelectedBot', 'ftbot.1');
  } catch (e) {
    console.warn('Failed to seed FreqUI bots:', e);
  }

  // Attempt auto-login to fetch tokens for each bot
  (async () => {
    try {
      const storeKey = 'ftAuthLoginInfo';
      const store = JSON.parse(localStorage.getItem(storeKey) || '{}');
      const creds = 'Basic ' + btoa('fq:fq');
      let updated = false;
      await Promise.all(
        bots.map(async (b, idx) => {
          const id = `ftbot.${idx + 1}`;
          const rec = store[id] || {};
          if (rec.accessToken && rec.refreshToken) return;
          try {
            const resp = await fetch(b.url + '/api/v1/token/login', {
              method: 'POST',
              headers: { Authorization: creds },
              credentials: 'omit',
            });
            if (!resp.ok) return;
            const data = await resp.json();
            if (data && data.access_token && data.refresh_token) {
              store[id] = {
                ...(store[id] || {}),
                accessToken: data.access_token,
                refreshToken: data.refresh_token,
              };
              updated = true;
            }
          } catch (err) {
            // ignore; user can login manually
          }
        })
      );
      if (updated) localStorage.setItem(storeKey, JSON.stringify(store));
    } catch (err) {
      // ignore auto-login errors
    }
  })();
})();
