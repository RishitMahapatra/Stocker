import client from './client';

export const fetchHealth       = ()         => client.get('/health').then(r => r.data);
export const fetchTickers      = ()         => client.get('/api/tickers').then(r => r.data);
export const fetchSignals      = ()         => client.get('/api/signals').then(r => r.data);
export const fetchSignal       = (ticker)   => client.get(`/api/signals/${ticker}`).then(r => r.data);
export const fetchSignalHistory= (ticker, limit = 20) =>
  client.get(`/api/signals/${ticker}/history?limit=${limit}`).then(r => r.data);
export const fetchPrices       = (ticker, days = 30) =>
  client.get(`/api/prices/${ticker}?days=${days}`).then(r => r.data);
export const fetchPortfolio    = ()         => client.get('/api/portfolio').then(r => r.data);
export const fetchTrades       = ()         => client.get('/api/trades').then(r => r.data);
export const fetchOpenTrades   = ()         => client.get('/api/trades/open').then(r => r.data);
