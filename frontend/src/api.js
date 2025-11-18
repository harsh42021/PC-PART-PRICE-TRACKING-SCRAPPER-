// frontend/src/api.js
// Creates a pre-configured axios instance for API requests

import axios from "axios";

const instance = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:5000",
  timeout: 20000,
});

// Optional logging interceptor (not required, but useful)
instance.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error("API Error:", err?.response || err);
    return Promise.reject(err);
  }
);

export default instance;
