import { useQuery, UseQueryResult } from 'react-query';
import axios from 'axios';
import { axiosInstance } from './common';
import {
  ConsumeData,
  LogData,
  ConfigData,
  ConfigDataWithUiInfo,
  AddonData,
  WifiData,
  DefinedConfigData,
  IssueData,
} from '../types/models';

const options_url = '/options';

// Config
export const getConfig = async (): Promise<ConfigDataWithUiInfo> => {
  return axiosInstance.get<ConfigDataWithUiInfo>(`${options_url}/full`).then((res) => res.data);
};

export const getConfigValues = async (): Promise<DefinedConfigData> => {
  return axiosInstance.get<DefinedConfigData>(options_url).then((res) => res.data);
};

export const useConfig = (): UseQueryResult<ConfigDataWithUiInfo, Error> => {
  return useQuery<ConfigDataWithUiInfo, Error>('options', getConfig);
};

export const updateOptions = async (options: ConfigData): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(options_url, options).then((res) => res.data);
};

// Clean
export const cleanMachine = async (): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${options_url}/clean`).then((res) => res.data);
};

// OS/System Management
export const rebootSystem = async (): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${options_url}/reboot`).then((res) => res.data);
};

export const shutdownSystem = async (): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${options_url}/shutdown`).then((res) => res.data);
};

export const updateSystem = async (): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${options_url}/update/system`).then((res) => res.data);
};

export const updateSoftware = async (): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${options_url}/update/software`).then((res) => res.data);
};

export const createBackup = async (): Promise<{ data: Blob; fileName: string }> => {
  const response = await axiosInstance.get(`${options_url}/backup`, {
    responseType: 'blob',
  });

  const contentDisposition = response.headers['content-disposition'];
  let fileName = 'backup.zip'; // fallback filename

  if (contentDisposition) {
    const match = contentDisposition.match(/filename="(.+?)"/);
    if (match && match[1]) {
      fileName = match[1];
    }
  }

  return { data: response.data, fileName };
};

export const uploadBackup = async (file: File): Promise<{ message: string }> => {
  const formData = new FormData();
  formData.append('file', file);

  return axios
    .post<{ message: string }>(`${options_url}/backup`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    .then((res) => res.data);
};

// Logs and data
export const getLogs = async (): Promise<LogData> => {
  return axiosInstance.get<LogData>(`${options_url}/logs`).then((res) => res.data);
};

export const useLogs = (): UseQueryResult<LogData, Error> => {
  return useQuery<LogData, Error>('logs', getLogs);
};

export const getConsumeData = async (): Promise<ConsumeData> => {
  return axiosInstance.get<ConsumeData>(`${options_url}/data`).then((res) => res.data);
};

export const useConsumeData = (): UseQueryResult<ConsumeData, Error> => {
  return useQuery<ConsumeData, Error>('consumeData', getConsumeData);
};

export const resetDataInsights = async (): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${options_url}/data/reset`).then((res) => res.data);
};

// Internet and Wifi
export const checkInternetConnection = async (): Promise<{ is_connected: boolean }> => {
  return axiosInstance.get<{ is_connected: boolean }>(`${options_url}/connection`).then((res) => res.data);
};

export const getAvailableSsids = async (): Promise<string[]> => {
  return axiosInstance.get<string[]>(`${options_url}/wifi`).then((res) => res.data);
};

export const useAvailableSsids = (): UseQueryResult<string[], Error> => {
  return useQuery<string[], Error>('availableSsids', getAvailableSsids);
};

export const updateWifiData = async (wifiData: WifiData): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${options_url}/wifi`, wifiData).then((res) => res.data);
};

// Addons
export const getAddonData = async (): Promise<AddonData[]> => {
  return axiosInstance.get<AddonData[]>(`${options_url}/addon`).then((res) => res.data);
};

export const useAddonData = (): UseQueryResult<AddonData[], Error> => {
  return useQuery<AddonData[], Error>('addonData', getAddonData);
};

export const addAddon = async (addon: AddonData): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${options_url}/addon`, addon).then((res) => res.data);
};

export const deleteAddon = async (addon: AddonData): Promise<{ message: string }> => {
  return axiosInstance
    .delete<{ message: string }>(`${options_url}/addon/remove`, { data: addon })
    .then((res) => res.data);
};

// Authentication
export const validateMakerPassword = async (password: number): Promise<{ message: string }> => {
  return axiosInstance
    .post<{ message: string }>(`${options_url}/password/maker/validate`, { password })
    .then((res) => res.data);
};

export const validateMasterPassword = async (password: number): Promise<{ message: string }> => {
  return axiosInstance
    .post<{ message: string }>(`${options_url}/password/master/validate`, { password })
    .then((res) => res.data);
};

// State management / user information
export const getIssues = async (): Promise<IssueData> => {
  return axiosInstance.get<IssueData>(`${options_url}/issues`).then((res) => res.data);
};

export const useIssues = (): UseQueryResult<IssueData, Error> => {
  return useQuery<IssueData, Error>('issues', getIssues, {
    staleTime: 60000,
  });
};

export const ignoreIssues = async (): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${options_url}/issues/ignore`).then((res) => res.data);
};

export const updateDateTime = async (date: string, time: string): Promise<{ message: string }> => {
  const data = { date, time };
  return axiosInstance.post<{ message: string }>(`${options_url}/datetime`, data).then((res) => res.data);
};
