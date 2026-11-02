import { useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { useAppContext } from '../context/AppContext';

/** Keeps global tax jurisdiction in sync with the authenticated user profile. */
export function SyncJurisdictionFromUser() {
  const { user } = useAuth();
  const { setCurrentJurisdiction } = useAppContext();

  useEffect(() => {
    if (user?.jurisdiction_code) {
      setCurrentJurisdiction(user.jurisdiction_code);
    }
  }, [user?.jurisdiction_code, setCurrentJurisdiction]);

  return null;
}
