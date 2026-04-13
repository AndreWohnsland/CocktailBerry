import { type UseQueryResult, useQuery } from 'react-query';
import { axiosInstance } from './common';

const scale_url = '/scale';

interface ScaleStatus {
  message: string;
  data: boolean;
}

interface ScaleReading {
  message: string;
  data: number;
}

export const getScaleStatus = async (): Promise<ScaleStatus> => {
  return axiosInstance.get<ScaleStatus>(`${scale_url}/status`).then((response) => response.data);
};

export const useScaleStatus = (): UseQueryResult<ScaleStatus, Error> => {
  return useQuery<ScaleStatus, Error>('scaleStatus', getScaleStatus);
};

export const tareScale = async (): Promise<ScaleReading> => {
  return axiosInstance.post<ScaleReading>(`${scale_url}/tare`).then((response) => response.data);
};

export const readScale = async (): Promise<ScaleReading> => {
  return axiosInstance.post<ScaleReading>(`${scale_url}/read`).then((response) => response.data);
};

export const calibrateScale = async (knownWeightGrams: number, zeroRawOffset: number): Promise<ScaleReading> => {
  const params: Record<string, number> = { known_weight_grams: knownWeightGrams, zero_raw_offset: zeroRawOffset };
  return axiosInstance.post<ScaleReading>(`${scale_url}/calibrate`, null, { params }).then((response) => response.data);
};
