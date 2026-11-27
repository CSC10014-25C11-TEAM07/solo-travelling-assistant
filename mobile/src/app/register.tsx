import { GlassPanel } from '@/components/glass/panel';
import { useState } from 'react';
import { router } from 'expo-router';
import { Text, View } from 'react-native';
import { RouteCover } from '@/components/glass/route-cover';
import { Action, Field, Page, styles } from '@/features/plan/ui';
import { register } from '@/features/plan/api';

export default function Register() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit() {
    setError('');
    if (!/^[a-z0-9_]{3,30}$/.test(username.trim().toLowerCase())) return setError('Tên đăng nhập cần 3–30 ký tự, gồm chữ a–z, số hoặc dấu gạch dưới.');
    if (Array.from(password).length < 15 || Array.from(password).length > 128) return setError('Mật khẩu cần từ 15 đến 128 ký tự.');
    if (password !== confirm) return setError('Mật khẩu nhập lại chưa khớp.');
    setBusy(true);
    try { await register(username, password); router.replace('/login'); }
    catch (e) { setError(e instanceof Error ? e.message : 'Không tạo được tài khoản.'); }
    finally { setBusy(false); }
  }
  return <Page><RouteCover />
    <GlassPanel>
      <View style={{ gap: 3 }}><Text accessibilityRole="header" style={styles.title}>Tạo tài khoản</Text><Text style={styles.muted}>Lưu lịch trình riêng để xem lại và điều chỉnh khi đang đi.</Text></View>
      <Field label="Tên đăng nhập" value={username} onChangeText={setUsername} placeholder="3–30 ký tự: a–z, số hoặc _" />
      <Field label="Mật khẩu (15–128 ký tự)" secure value={password} onChangeText={setPassword} placeholder="Nhập mật khẩu" />
      <Field label="Nhập lại mật khẩu" secure value={confirm} onChangeText={setConfirm} placeholder="Nhập lại mật khẩu" />
      {!!error && <Text accessibilityRole="alert" style={styles.error}>{error}</Text>}
      <Action title={busy ? 'Đang tạo…' : 'Tạo tài khoản'} disabled={busy} onPress={submit} />
      <Action title="Quay lại đăng nhập" secondary onPress={() => router.replace('/login')} />
    </GlassPanel>
  </Page>;
}
