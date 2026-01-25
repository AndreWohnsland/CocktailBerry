import { type UseQueryResult, useQuery } from 'react-query';
import type {
  AboutInfo,
  AddonData,
  ConfigData,
  ConfigDataWithUiInfo,
  ConsumeData,
  DefinedConfigData,
  IssueData,
  LogData,
  ResourceInfo,
  ResourceStats,
  WifiData,
} from '../types/models';
import { axiosInstance } from './common';

const optionsUrl = '/options';

// Config
export const getConfig = async (): Promise<ConfigDataWithUiInfo> => {
  return axiosInstance.get<ConfigDataWithUiInfo>(`${optionsUrl}/full`).then((res) => res.data);
};

export const getConfigValues = async (): Promise<DefinedConfigData> => {
  return axiosInstance.get<DefinedConfigData>(optionsUrl).then((res) => res.data);
};

export const useConfig = (): UseQueryResult<ConfigDataWithUiInfo, Error> => {
  return useQuery<ConfigDataWithUiInfo, Error>('options', getConfig);
};

export const updateOptions = async (options: ConfigData): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(optionsUrl, options).then((res) => res.data);
};

// Clean
export const cleanMachine = async (): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${optionsUrl}/clean`).then((res) => res.data);
};

// OS/System Management
export const rebootSystem = async (): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${optionsUrl}/reboot`).then((res) => res.data);
};

export const shutdownSystem = async (): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${optionsUrl}/shutdown`).then((res) => res.data);
};

export const updateSystem = async (): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${optionsUrl}/update/system`).then((res) => res.data);
};

export const updateSoftware = async (): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${optionsUrl}/update/software`).then((res) => res.data);
};

export const createBackup = async (): Promise<{ data: Blob; fileName: string }> => {
  try {
    const response = await axiosInstance.get(`${optionsUrl}/backup`, {
      responseType: 'blob',
    });

    const contentDisposition = response.headers['content-disposition'];
    let fileName = 'backup.zip'; // fallback filename

    if (contentDisposition) {
      const match = contentDisposition.match(/filename="(.+?)"/);
      if (match?.[1]) fileName = match[1];
    }
    return { data: response.data, fileName };
  } catch (error: unknown) {
    if (error instanceof Blob) {
      const text = await error.text();
      const json = JSON.parse(text);
      throw new Error(json.detail || 'An error occurred while creating the backup');
    }
    throw error;
  }
};

export const uploadBackup = async (file: File): Promise<{ message: string }> => {
  const formData = new FormData();
  formData.append('file', file);

  return axiosInstance
    .post<{ message: string }>(`${optionsUrl}/backup`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    .then((res) => res.data);
};

// Logs and data
export const getLogs = async (): Promise<LogData> => {
  return axiosInstance.get<LogData>(`${optionsUrl}/logs`).then((res) => res.data);
};

export const useLogs = (): UseQueryResult<LogData, Error> => {
  return useQuery<LogData, Error>('logs', getLogs);
};

export const getConsumeData = async (): Promise<ConsumeData> => {
  return axiosInstance.get<ConsumeData>(`${optionsUrl}/data`).then((res) => res.data);
};

export const useConsumeData = (): UseQueryResult<ConsumeData, Error> => {
  return useQuery<ConsumeData, Error>('consumeData', getConsumeData);
};

export const resetDataInsights = async (): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${optionsUrl}/data/reset`).then((res) => res.data);
};

// Internet and Wifi
export const checkInternetConnection = async (): Promise<{ is_connected: boolean }> => {
  return axiosInstance.get<{ is_connected: boolean }>(`${optionsUrl}/connection`).then((res) => res.data);
};

export const getAvailableSsids = async (): Promise<string[]> => {
  return axiosInstance.get<string[]>(`${optionsUrl}/wifi`).then((res) => res.data);
};

export const useAvailableSsids = (): UseQueryResult<string[], Error> => {
  return useQuery<string[], Error>('availableSsids', getAvailableSsids);
};

export const updateWifiData = async (wifiData: WifiData): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${optionsUrl}/wifi`, wifiData).then((res) => res.data);
};

// Addons
export const getAddonData = async (): Promise<AddonData[]> => {
  return axiosInstance.get<AddonData[]>(`${optionsUrl}/addon`).then((res) => res.data);
};

export const useAddonData = (): UseQueryResult<AddonData[], Error> => {
  return useQuery<AddonData[], Error>('addonData', getAddonData);
};

export const addAddon = async (addon: AddonData): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${optionsUrl}/addon`, addon).then((res) => res.data);
};

export const deleteAddon = async (addon: AddonData): Promise<{ message: string }> => {
  return axiosInstance
    .delete<{ message: string }>(`${optionsUrl}/addon/remove`, { data: addon })
    .then((res) => res.data);
};

export const updateAddon = async (addon: AddonData): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${optionsUrl}/addon/update`, addon).then((res) => res.data);
};

// Authentication
export const validateMakerPassword = async (password: number): Promise<{ message: string }> => {
  return axiosInstance
    .post<{ message: string }>(`${optionsUrl}/password/maker/validate`, { password })
    .then((res) => res.data);
};

export const validateMasterPassword = async (password: number): Promise<{ message: string }> => {
  return axiosInstance
    .post<{ message: string }>(`${optionsUrl}/password/master/validate`, { password })
    .then((res) => res.data);
};

// State management / user information
export const getIssues = async (): Promise<IssueData> => {
  return axiosInstance.get<IssueData>(`${optionsUrl}/issues`).then((res) => res.data);
};

export const useIssues = (): UseQueryResult<IssueData, Error> => {
  return useQuery<IssueData, Error>('issues', getIssues);
};

export const ignoreIssues = async (): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${optionsUrl}/issues/ignore`).then((res) => res.data);
};

export const updateDateTime = async (date: string, time: string): Promise<{ message: string }> => {
  const data = { date, time };
  return axiosInstance.post<{ message: string }>(`${optionsUrl}/datetime`, data).then((res) => res.data);
};

export const getResourceInfo = async (): Promise<ResourceInfo[]> => {
  return axiosInstance.get<ResourceInfo[]>(`${optionsUrl}/resource_tracker/sessions`).then((res) => res.data.reverse()); // Always return reversed order (latest first)
};

export const useResourceInfo = (): UseQueryResult<ResourceInfo[], Error> => {
  return useQuery<ResourceInfo[], Error>('resourceInfo', getResourceInfo);
};

export const getResourceStats = async (sessionNumber: number): Promise<ResourceStats> => {
  return axiosInstance.get<ResourceStats>(`${optionsUrl}/resource_tracker/${sessionNumber}`).then((res) => res.data);
};

export const useResourceStats = (sessionNumber: number): UseQueryResult<ResourceStats, Error> => {
  return useQuery<ResourceStats, Error>(['resourceStats', sessionNumber], () => getResourceStats(sessionNumber));
};

// About info
export const getAboutInfo = async (): Promise<AboutInfo> => {
  return axiosInstance.get<AboutInfo>('/info').then((res) => res.data);
};

export const useAboutInfo = (): UseQueryResult<AboutInfo, Error> => {
  return useQuery<AboutInfo, Error>('aboutInfo', getAboutInfo);
};

// News
export const getNews = async (): Promise<Record<string, string>> => {
  return axiosInstance.get<{ data: Record<string, string> }>(`${optionsUrl}/news`).then((res) => res.data.data);
};

export const useNews = (): UseQueryResult<Record<string, string>, Error> => {
  return useQuery<Record<string, string>, Error>('news', getNews);
};

export const acknowledgeNews = async (newsKey: string): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${optionsUrl}/news/${newsKey}`).then((res) => res.data);
};
