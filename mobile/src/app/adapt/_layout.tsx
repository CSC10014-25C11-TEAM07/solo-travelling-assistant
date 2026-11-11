import { Stack } from 'expo-router';
import { AdaptProvider } from '@/features/adapt/context';
export default function AdaptLayout() {
  return <AdaptProvider><Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: '#86bde9' } }}><Stack.Screen name="index" options={{ title: 'Lịch hiện hành' }} /><Stack.Screen name="request" options={{ title: 'S04 · Điều chỉnh' }} /><Stack.Screen name="compare" options={{ title: 'S05 · Phương án A/B' }} /><Stack.Screen name="result" options={{ title: 'S06 · Kết quả' }} /></Stack></AdaptProvider>;
}
