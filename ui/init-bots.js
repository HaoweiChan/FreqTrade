// Auto-register bots into FreqUI on page load and prefill login details.
(function () {
  // Dynamically determine the base URL using the current hostname
  // This works regardless of whether accessed via localhost, IP, or domain
  const baseUrl = `${window.location.protocol}//${window.location.hostname}`;
  const port = window.location.port ? `:${window.location.port}` : '';
  
  const bots = [
    { name: 'freqtrade-trader-ichi_v_1', url: `${baseUrl}${port}/api/ichiv1/` },
    { name: 'freqtrade-trader-lookahead_strategy', url: `${baseUrl}${port}/api/lookaheadstrategy/` },
    { name: 'freqtrade-trader-macd', url: `${baseUrl}${port}/api/macd/` },
    { name: 'freqtrade-trader-custom_stoploss_with_psar', url: `${baseUrl}${port}/api/customstoplosswithpsar/` },
    { name: 'freqtrade-trader-macdcci', url: `${baseUrl}${port}/api/macdcci/` },
  ];

  // Expose for UI components that might read this
  window.freqtradeBots = bots.map(b => ({ name: b.name, apiUrl: b.url }));

  // Seed localStorage so the bots list shows up immediately.
  // Authentication is intentionally NOT pre-filled to ensure security.
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
        // Preserve existing auth if any, otherwise leave empty
        username: current.username || '',
        accessToken: current.accessToken || '',
        refreshToken: current.refreshToken || '',
        autoRefresh: true,
        sortId: idx,
      };
      return { id, desired };
    });

    entries.forEach(({ id, desired }) => {
      // Only update if the bot config (URL/Name) changed, preserving auth
      if (existing[id]?.apiUrl !== desired.apiUrl || existing[id]?.botName !== desired.botName) {
         // If URL changed, we might want to reset auth? 
         // For now, just update the config part
         existing[id] = { ...existing[id], ...desired };
         changed = true;
      } else if (!existing[id]) {
         existing[id] = desired;
         changed = true;
      }
    });
    if (changed) localStorage.setItem(storeKey, JSON.stringify(existing));

    // Select first bot by default if not selected
    if (!localStorage.getItem('ftSelectedBot')) {
      localStorage.setItem('ftSelectedBot', 'ftbot.1');
    }
  } catch (e) {
    console.warn('Failed to seed FreqUI bots:', e);
  }
})();
