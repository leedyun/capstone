import axios from 'axios';

const instance = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// 개발 환경에서 SSL 인증서 검증 무시
if (process.env.NODE_ENV === 'development') {
  process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
}

// 요청 인터셉터 추가
instance.interceptors.request.use(
  (config) => {
    // URL에서 중복 슬래시 제거
    if (config.url) {
      config.url = config.url.replace(/([^:]\/)\/+/g, "$1");
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default instance; 