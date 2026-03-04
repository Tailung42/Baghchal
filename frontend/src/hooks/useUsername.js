import { useAuth } from './useAuth';

export function useUsername() {
  const { auth } = useAuth();

  const username = auth?.user?.username || auth?.guestId || '';
  const isLoggedIn = auth?.isLoggedIn || false;

  return { username, isLoggedIn };
}
