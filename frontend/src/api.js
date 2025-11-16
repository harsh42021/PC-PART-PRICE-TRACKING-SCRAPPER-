import axios from 'axios';

const API_BASE = "";

export const getHealth = () => axios.get(`${API_BASE}/api/health`);
export const getRetailers = () => axios.get(`${API_BASE}/api/retailers`);
export const addRetailer = (payload) => axios.post(`${API_BASE}/api/retailers`, payload);
export const toggleRetailer = (id) => axios.post(`${API_BASE}/api/retailers/${id}/toggle`);

export const getBuilds = () => axios.get(`${API_BASE}/api/builds`);
export const addBuild = (payload) => axios.post(`${API_BASE}/api/builds`, payload);
export const getBuildParts = (build_id) => axios.get(`${API_BASE}/api/builds/${build_id}/parts`);
export const addBuildPart = (build_id, payload) => axios.post(`${API_BASE}/api/builds/${build_id}/parts`, payload);
export const deleteBuildPart = (build_id, payload) => axios.delete(`${API_BASE}/api/builds/${build_id}/parts`, { data: payload });

export const getProductUrls = (oem) => axios.get(`${API_BASE}/api/product_urls/${oem}`);
export const addProductUrl = (oem, payload) => axios.post(`${API_BASE}/api/product_urls/${oem}`, payload);
export const deleteProductUrl = (id) => axios.delete(`${API_BASE}/api/product_urls/${id}`);

export const refreshPrices = () => axios.post(`${API_BASE}/api/refresh`);
export const getPriceHistory = (oem) => axios.get(`${API_BASE}/api/price_history/${oem}`);

export const getNotificationSettings = () => axios.get(`${API_BASE}/api/notifications/settings`);
export const setNotificationSettings = (payload) => axios.post(`${API_BASE}/api/notifications/settings`, payload);
