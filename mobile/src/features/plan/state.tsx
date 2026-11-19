
import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from 'react';

import {
  FormData,
  Trip,
  clearSavedTrip,
  clearToken,
  token,
  me,
} from './api';

type Context = {
  ready: boolean;
  account: string | null;
  setAccount: (a: string | null) => void;

  form: FormData;
  setForm: (f: FormData) => void;

  trip: Trip | null;
  setTrip: (t: Trip | null) => void;

  draftId: string | null;
  setDraftId: (id: string | null) => void;

  selectedIds: string[];
  setSelectedIds: (v: string[]) => void;

  clearSession: () => Promise<void>;
};

const C = createContext<Context | null>(null);

function defaultForm(): FormData {
  const today = new Date();
  const localDate = (offset: number) => new Date(Date.UTC(
    today.getFullYear(), today.getMonth(), today.getDate() + offset
  )).toISOString().slice(0, 10);
  return {
  departure_date: localDate(1),
  return_date: localDate(4),
  departure_time: '06:00',
  min_rest_minutes: '60',
  interests: ['nature'],
  };
}

export function PlanProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [form, setForm] = useState<FormData>(defaultForm);
  const [trip, setTrip] = useState<Trip | null>(null);
  const [draftId, setDraftId] = useState<string | null>(null);
  const [account, setAccount] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let active = true;

    async function restoreSession() {
      try {
        const savedToken = await token();

        if (!savedToken) return;

        const user = await me();

        if (!active) return;

        const username =
          typeof user?.username === 'string'
            ? user.username
            : typeof user?.user?.username === 'string'
            ? user.user.username
            : null;

        if (!username) {
          throw new Error(
            'Không đọc được thông tin tài khoản.'
          );
        }

        setAccount(username);
      } catch (error) {
        if (!active) return;

        const status = (error as { status?: number }).status;

        if (status === 401) {
          await clearToken();

          if (active) {
            setAccount(null);
          }
        } else {
          // Không xóa token khi mất mạng hoặc lỗi máy chủ.
          console.warn('Không thể khôi phục phiên:', error);
        }
      } finally {
        if (active) {
          setReady(true);
        }
      }
    }

    void restoreSession();

    return () => {
      active = false;
    };
  }, []);

  const clearSession = useCallback(async () => {
    await clearSavedTrip();

    setAccount(null);
    setTrip(null);
    setDraftId(null);
    setSelectedIds([]);

    setForm(defaultForm());
  }, []);

  return (
    <C.Provider
      value={{
        ready,
        account,
        setAccount,
        form,
        setForm,
        trip,
        setTrip,
        draftId,
        setDraftId,
        selectedIds,
        setSelectedIds,
        clearSession,
      }}
    >
      {children}
    </C.Provider>
  );
}

export function usePlan() {
  const context = useContext(C);

  if (!context) {
    throw new Error('PlanProvider missing');
  }

  return context;
}

export const tripDays = (trip: Trip) =>
  trip.itinerary_days || trip.days || [];
