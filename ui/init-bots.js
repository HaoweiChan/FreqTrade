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
  // However, we propagate tokens between bots to allow "Login Once" behavior.
  try {
    const storeKey = 'ftAuthLoginInfo';
    const existing = JSON.parse(localStorage.getItem(storeKey) || '{}');
    
    // Find a master token from any bot that has one
    let masterToken = null;
    for (const key in existing) {
        if (existing[key].accessToken && existing[key].refreshToken) {
            masterToken = { 
                accessToken: existing[key].accessToken, 
                refreshToken: existing[key].refreshToken,
                username: existing[key].username
            };
            break;
        }
    }

    let changed = false;
    const entries = bots.map((b, idx) => {
      const id = `ftbot.${idx + 1}`;
      const current = existing[id] || {};
      
      // Use current token if exists, otherwise use master token (if available)
      const tokenSource = (current.accessToken && current.refreshToken) ? current : (masterToken || {});

      const desired = {
        botName: b.name,
        apiUrl: b.url,
        username: tokenSource.username || '',
        accessToken: tokenSource.accessToken || '',
        refreshToken: tokenSource.refreshToken || '',
        autoRefresh: true,
        sortId: idx,
      };
      return { id, desired };
    });

    entries.forEach(({ id, desired }) => {
      // Update if config changed OR if we are adding a missing token
      const current = existing[id];
      if (!current || 
          current.apiUrl !== desired.apiUrl || 
          current.botName !== desired.botName ||
          (!current.accessToken && desired.accessToken) // Propagate token if missing
      ) {
         // Merge to preserve other fields if needed, but overwrite auth
         existing[id] = { ...current, ...desired };
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
