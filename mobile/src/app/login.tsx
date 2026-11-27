import { GlassPanel } from '@/components/glass/panel';
import { useState } from 'react';
import { router } from 'expo-router';
import { Pressable, Text, View } from 'react-native';
import { RouteCover } from '@/components/glass/route-cover';
import { Action, Field, Page, styles, palette } from '@/features/plan/ui';
import { usePlan } from '@/features/plan/state';
import { login } from '@/features/plan/api';

export default function Login() {
  const { setAccount } = usePlan();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [show, setShow] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit() {
    setError('');
    const account = username.trim().toLowerCase();
    if (!/^[a-z0-9_]{3,30}$/.test(account)) return setError('Tên đăng nhập gồm 3–30 ký tự: a–z, số hoặc _.');
    if (Array.from(password).length < 15 || Array.from(password).length > 128) return setError('Mật khẩu cần 15–128 ký tự.');
    setBusy(true);
    try { await login(username, password); setAccount(account); router.replace('/plan'); }
    catch (e) { setError(e instanceof Error ? e.message : 'Không thể đăng nhập.'); }
    finally { setBusy(false); }
  }
  return <Page><RouteCover />
    <GlassPanel>
      <View style={{ gap: 3 }}><Text accessibilityRole="header" style={styles.title}>Đăng nhập</Text><Text style={styles.muted}>Mở lịch đã lưu hoặc lên kế hoạch cho chuyến đi mới.</Text></View>
      <Field label="Tên đăng nhập" value={username} onChangeText={setUsername} placeholder="Nhập tên đăng nhập" />
      <Field label="Mật khẩu" secure={!show} value={password} onChangeText={setPassword} placeholder="Nhập mật khẩu" />
      <Pressable accessibilityRole="button" onPress={() => setShow(v => !v)} style={({ pressed }) => ({ alignSelf: 'flex-end', minHeight: 44, justifyContent: 'center', paddingHorizontal: 6, opacity: pressed ? .65 : 1 })}>
        <Text style={{ color: palette.pine, fontSize: 14, fontWeight: '600' }}>{show ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}</Text>
      </Pressable>
      {!!error && <Text accessibilityRole="alert" style={styles.error}>{error}</Text>}
      <Action title={busy ? 'Đang đăng nhập…' : 'Đăng nhập'} disabled={busy} onPress={submit} />
      <Action title="Tạo tài khoản mới" secondary onPress={() => router.push('/register')} />
    </GlassPanel>
  </Page>;
}
