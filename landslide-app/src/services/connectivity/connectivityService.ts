import NetInfo, { NetInfoState } from '@react-native-community/netinfo';
import { API_CONFIG } from '../api/apiConfig';

export type ConnectivityStatus = 'offline' | 'checking' | 'online' | 'backend_unavailable';

const HEALTH_TIMEOUT_MS = 5000;

function isNetworkReachable(state: NetInfoState): boolean {
  if (state.isConnected === false) return false;
  if (state.isInternetReachable === false) return false;
  return true;
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.health}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), HEALTH_TIMEOUT_MS);

    const response = await fetch(url, {
      method: 'GET',
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    return response.ok;
  } catch {
    return false;
  }
}

export async function checkNetwork(): Promise<boolean> {
  const state = await NetInfo.fetch();
  return isNetworkReachable(state);
}

export async function checkConnectivity(): Promise<ConnectivityStatus> {
  const hasNetwork = await checkNetwork();
  if (!hasNetwork) return 'offline';

  const backendOk = await checkBackendHealth();
  return backendOk ? 'online' : 'backend_unavailable';
}

export function subscribeToNetworkChanges(
  callback: (isConnected: boolean) => void
): () => void {
  return NetInfo.addEventListener((state) => {
    callback(isNetworkReachable(state));
  });
}
