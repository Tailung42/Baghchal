import { useAuth } from "./useAuth";

export function useUsername() {
  const { auth } = useAuth();

  const username = auth?.user?.username || auth?.guest.username || "";
  return { username };
}
