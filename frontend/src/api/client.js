import axios from 'axios';

const client = axios.create({
  baseURL: 'http://localhost:7999',
  timeout: 10000,
});

client.interceptors.response.use(
  (res) => {
    console.log('[API]', res.config.method?.toUpperCase(), res.config.url, res.data);
    return res;
  },
  (err) => {
    console.error('[API ERROR]', err.config?.url, err.message);
    return Promise.reject(err);
  }
);

export default client;
