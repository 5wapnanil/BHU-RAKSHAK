export const authService = {
  async login(_email: string, _password: string) {
    throw new Error('Auth not configured');
  },
  async register(_name: string, _email: string, _password: string) {
    throw new Error('Auth not configured');
  },
  async logout() {
    throw new Error('Auth not configured');
  },
  async getCurrentUser() {
    return null;
  },
};
