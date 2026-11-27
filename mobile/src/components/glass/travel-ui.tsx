import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import type { ReactNode } from 'react';
import { Image, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { palette as p } from './colors';
import { GlassScene, glassInset } from './panel';

export { palette } from './colors';
const edge = { borderWidth: 1, borderColor: p.rim, borderBottomColor: '#C0D8D0' } as const;
export const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: p.mist },
  content: { alignSelf: 'center', width: '100%', maxWidth: 720, flexGrow: 1, paddingHorizontal: 16, paddingTop: 12, paddingBottom: 36, gap: 16 },
  title: { fontSize: 30, lineHeight: 39, letterSpacing: -.8, fontWeight: '700', color: p.ink },
  subtitle: { fontSize: 16, lineHeight: 24, color: p.ink },
  poetic: { fontSize: 22, lineHeight: 30, fontWeight: '600', color: p.pine },
  heading: { fontSize: 20, lineHeight: 28, letterSpacing: -.35, fontWeight: '700', color: p.ink },
  text: { fontSize: 16, lineHeight: 24, color: p.ink },
  muted: { fontSize: 14, lineHeight: 21, color: p.slate },
  input: { minHeight: 49, borderWidth: 1, borderColor: '#FFFFFFBA', borderRadius: 14, paddingHorizontal: 13, paddingVertical: 10, fontSize: 16, color: p.ink, backgroundColor: 'rgba(237,255,253,0.34)' },
  error: { borderLeftWidth: 3, borderColor: p.oxide, backgroundColor: '#FFEBE5', color: '#742F26', fontSize: 15, lineHeight: 22, fontWeight: '600', borderRadius: 8, padding: 12 },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 9 },
});

export function Page({ children }: { children: ReactNode }) {
  return <GlassScene>
    <StatusBar style="dark" />
    <SafeAreaView style={{ flex: 1 }}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>{children}</ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  </GlassScene>;
}

export function Header({ weather = true }: { weather?: boolean }) {
  return <View style={ui.header}>
    <Pressable accessibilityRole="button" accessibilityLabel="Quay lại" onPress={() => router.back()} style={({ pressed }) => [ui.back, pressed && ui.pressed]}>
      <Text style={{ color: p.ink, fontSize: 24 }} accessibilityElementsHidden>‹</Text><Text style={ui.label}>Quay lại</Text>
    </Pressable>
    {weather && <Text style={[ui.label, ui.locale]}>Đà Lạt</Text>}
  </View>;
}

export function Action({ title, onPress, disabled = false, secondary = false, icon }: { title: string; onPress: () => void; disabled?: boolean; secondary?: boolean; icon?: string }) {
  return <Pressable accessibilityRole="button" accessibilityState={{ disabled }} disabled={disabled} onPress={onPress} style={({ pressed }) => [ui.action, secondary ? ui.secondary : ui.primary, pressed && ui.pressed, disabled && ui.disabled]}>
    <Text style={[ui.actionText, { color: secondary ? p.ink : p.foam }]}>{icon ? `${icon}  ` : ''}{title}</Text>
  </Pressable>;
}

export function MockLabel(_props: { isMock: boolean }) { return null; }
export function TimeTile({ label, value, children, icon }: { label: string; value: string; children?: ReactNode; icon?: string }) {
  return <View style={ui.tile}>{icon && <Text style={ui.label}>{icon}</Text>}<Text style={styles.muted}>{label}</Text>{children ?? <Text style={ui.time}>{value}</Text>}</View>;
}
export function OptionPanels({ children }: { children: ReactNode }) {
  const { width, fontScale } = useWindowDimensions();
  return <View style={{ flexDirection: width >= 740 && fontScale <= 1.15 ? 'row' : 'column', gap: 12, alignItems: 'stretch' }}>{children}</View>;
}
export function TimelineLine({ time, title, status, symbol }: { time: string; title: string; status: string; symbol?: string }) {
  const { width, fontScale } = useWindowDimensions();
  const stack = width < 360 || fontScale > 1.2;
  return <View style={ui.timeline}><View style={ui.station}><Text style={{ color: status === 'Đã bỏ' ? p.oxide : p.pine }}>{symbol ?? '•'}</Text></View><View style={{ flex: 1, flexDirection: stack ? 'column' : 'row', gap: stack ? 3 : 10 }}><Text style={[ui.time, { fontSize: 14 }]}>{time}</Text><View style={{ flex: 1 }}><Text style={ui.label}>{title}</Text><Text style={styles.muted}>{status}</Text></View></View></View>;
}
export function SectionTitle({ title, subtitle }: { title: string; subtitle?: string }) {
  return <View style={{ gap: 4 }}><Text accessibilityRole="header" style={styles.title}>{title}</Text>{subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}</View>;
}
export function ChangePanel({ before, after, detail }: { before: string; after: string; detail?: string }) {
  return <View style={ui.tile}><Text style={ui.label}>Thay đổi chính</Text><Text style={styles.muted}>Trước: {before}</Text><Text style={styles.text}>Sau: {after}</Text>{!!detail && <Text style={styles.muted}>{detail}</Text>}</View>;
}
function photoFor(place: string) {
  const name = place.toLocaleLowerCase('vi');
  if (name.includes('xuân hương')) return require('../../../assets/images/adapt/ho-xuan-huong.png');
  if (name.includes('vườn hoa')) return require('../../../assets/images/adapt/vuon-hoa-da-lat.png');
  return null;
}
export function PlacePhoto({ place, height = 116 }: { place: string; height?: number }) {
  const source = photoFor(place);
  return source ? <Image source={source} resizeMode="cover" accessibilityLabel={`Ảnh ${place}`} style={{ width: '100%', height, borderRadius: 12, backgroundColor: p.mist }} /> : null;
}
export function PlaceChoice({ title, selected, onPress, subtitle }: { title: string; selected: boolean; onPress: () => void; subtitle?: string }) {
  return <Pressable accessibilityRole="radio" accessibilityState={{ checked: selected }} onPress={onPress} style={({ pressed }) => [ui.choice, selected && ui.chosen, pressed && ui.pressed]}>
    <View style={[ui.radio, selected && { backgroundColor: p.pine }]}>{selected && <Text style={{ color: p.foam, fontWeight: '700' }}>✓</Text>}</View>
    <View style={{ flex: 1 }}><Text style={ui.label}>{title}</Text>{!!subtitle && <Text style={styles.muted}>{subtitle}</Text>}</View>
    {photoFor(title) != null && <View style={{ width: 64 }}><PlacePhoto place={title} height={54} /></View>}
  </Pressable>;
}
const ui = StyleSheet.create({
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  back: { ...edge, borderRadius: 24, flexDirection: 'row', gap: 7, paddingHorizontal: 14, minHeight: 44, alignItems: 'center', backgroundColor: p.pane },
  locale: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 16, backgroundColor: p.pane, overflow: 'hidden' },
  label: { fontSize: 15, lineHeight: 21, fontWeight: '600', color: p.ink },
  action: { minHeight: 48, borderRadius: 15, paddingHorizontal: 14, paddingVertical: 12, alignItems: 'center', justifyContent: 'center', borderWidth: 1 },
  primary: { backgroundColor: p.pine, borderColor: '#14675B' }, secondary: { ...glassInset, backgroundColor: p.pane },
  pressed: { opacity: .8 }, disabled: { opacity: .62 },
  actionText: { fontSize: 15, lineHeight: 22, fontWeight: '700', textAlign: 'center', fontVariant: ['tabular-nums'] },
  tile: { ...glassInset, flexGrow: 1, flexBasis: 100, minWidth: 86, gap: 4, borderRadius: 13, padding: 12 },
  time: { fontSize: 18, lineHeight: 24, fontWeight: '700', color: p.ink, fontVariant: ['tabular-nums'] },
  timeline: { flexDirection: 'row', gap: 9, paddingVertical: 10, borderBottomWidth: StyleSheet.hairlineWidth, borderColor: p.line },
  station: { width: 22, height: 22, borderRadius: 11, backgroundColor: p.mist, alignItems: 'center', justifyContent: 'center' },
  choice: { ...glassInset, flexDirection: 'row', alignItems: 'center', gap: 10, minHeight: 48, padding: 11, borderRadius: 14 },
  chosen: { borderColor: p.pine, backgroundColor: '#D9EEE8' }, radio: { borderWidth: 1.5, borderColor: p.pine, width: 22, height: 22, borderRadius: 11, alignItems: 'center', justifyContent: 'center' },
});
