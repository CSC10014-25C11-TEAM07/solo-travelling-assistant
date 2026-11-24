import { Stack, useGlobalSearchParams } from 'expo-router';
import { useState } from 'react';
import { AdaptProvider } from '@/features/adapt/context';
export default function AdaptLayout() {
  const { day } = useGlobalSearchParams<{ day?: string }>();
  const requestedDay = typeof day === 'string' && /^[1-4]$/.test(day) ? Number(day) : undefined;
  const [initialDay, setInitialDay] = useState(requestedDay);
  if (requestedDay !== undefined && requestedDay !== initialDay) {
    setInitialDay(requestedDay);
  }

  return (
    <AdaptProvider initialDay={initialDay}>
      <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: '#86bde9' } }}>
        <Stack.Screen name="index" options={{ title: 'Lịch hiện hành' }} />
        <Stack.Screen name="request" options={{ title: 'S04 · Điều chỉnh' }} />
        <Stack.Screen name="compare" options={{ title: 'S05 · Phương án A/B' }} />
        <Stack.Screen name="result" options={{ title: 'S06 · Kết quả' }} />
      </Stack>
    </AdaptProvider>
  );
}
