import { type UseQueryResult, useQuery } from 'react-query';
import type { Role, RoleCreate, RoleUpdate } from '../types/models';
import { axiosInstance } from './common';

const rolesUrl = '/roles';

export const getRoles = async (): Promise<Role[]> => {
  return axiosInstance.get<Role[]>(rolesUrl).then((res) => res.data);
};

export const useRoles = (): UseQueryResult<Role[], Error> => {
  return useQuery<Role[], Error>('roles', getRoles);
};

export const createRole = async (data: RoleCreate): Promise<Role> => {
  return axiosInstance.post<Role>(rolesUrl, data).then((res) => res.data);
};

export const updateRole = async (id: number, data: RoleUpdate): Promise<Role> => {
  return axiosInstance.put<Role>(`${rolesUrl}/${id}`, data).then((res) => res.data);
};

export const deleteRole = async (id: number): Promise<{ message: string }> => {
  return axiosInstance.delete<{ message: string }>(`${rolesUrl}/${id}`).then((res) => res.data);
};
