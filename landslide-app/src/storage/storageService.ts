import AsyncStorage from '@react-native-async-storage/async-storage';

export interface StorageService {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
  removeItem(key: string): Promise<void>;
  clear(): Promise<void>;
}

export function createStorageService(): StorageService {
  return {
    async getItem(key: string): Promise<string | null> {
      try {
        return await AsyncStorage.getItem(key);
      } catch (error) {
        console.warn(`[StorageService] Failed to get item for key "${key}":`, error);
        return null;
      }
    },

    async setItem(key: string, value: string): Promise<void> {
      try {
        await AsyncStorage.setItem(key, value);
      } catch (error) {
        console.warn(`[StorageService] Failed to set item for key "${key}":`, error);
      }
    },

    async removeItem(key: string): Promise<void> {
      try {
        await AsyncStorage.removeItem(key);
      } catch (error) {
        console.warn(`[StorageService] Failed to remove item for key "${key}":`, error);
      }
    },

    async clear(): Promise<void> {
      try {
        await AsyncStorage.clear();
      } catch (error) {
        console.warn('[StorageService] Failed to clear storage:', error);
      }
    },
  };
}

export const storageService = createStorageService();