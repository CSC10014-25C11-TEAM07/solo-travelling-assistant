import React from 'react';
import { Image, ImageBackground, Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
export const palette = { bg: '#e6f1d9', green: '#073b2d', accent: '#d5f65e', gray: '#42544b', white: '#fffaf0', red: '#a32626', cream: '#fffaf0' };
export const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#86bde9' },
  content: { width: '100%', maxWidth: 600, alignSelf: 'center', paddingHorizontal: 18, paddingTop: 14, paddingBottom: 115, gap: 16, minHeight: '100%' },
  title: { fontSize: 28, fontWeight: '900', color: '#082f28', lineHeight: 35 },
  subtitle: { fontSize: 15, color: '#102e27', lineHeight: 22 },
  poetic: { fontSize: 23, fontWeight: '700', fontStyle: 'italic', color: palette.green },
  heading: { fontSize: 19, fontWeight: '800', color: palette.green },
  text: { fontSize: 15, lineHeight: 22, color: '#102e27' },
  muted: { fontSize: 13, lineHeight: 19, color: palette.gray },
  card: { backgroundColor: 'rgba(255,251,241,0.97)', borderRadius: 25, padding: 17, gap: 13, borderWidth: 1, borderColor: 'rgba(255,255,255,0.95)', shadowColor: '#123b34', shadowOpacity: .19, shadowRadius: 10, elevation: 4 },
  input: { borderColor: '#a2b99a', borderWidth: 1.5, borderRadius: 14, padding: 10, fontSize: 17, fontWeight: '800', color: palette.green, backgroundColor: '#fff' },
  error: { color: '#fff', fontSize: 14, fontWeight: '700', backgroundColor: '#a32626', borderRadius: 10, padding: 12 },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 9 },
});
export function Page({ children }: { children: React.ReactNode }) {
  return <ImageBackground
    source={require('../../../assets/images/plan/background-original.jpg')}
    resizeMode="cover"
    style={{ flex: 1, backgroundColor: '#86bde9' }}
    imageStyle={{ width: '100%', height: '100%' }}
  >
    <SafeAreaView edges={['top', 'bottom']} style={{ flex: 1 }}>
      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={[styles.content, { minHeight: undefined, flexGrow: 1 }]}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {children}
      </ScrollView>
    </SafeAreaView>
  </ImageBackground>;
}
export function Header({ weather = true }: { weather?: boolean }) {
  return <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
    <Pressable accessibilityRole="button" accessibilityLabel="Quay lại" onPress={() => router.back()} style={{ width: 46, height: 46, backgroundColor: palette.cream, borderRadius: 25, alignItems: 'center', justifyContent: 'center', shadowOpacity: .12, shadowRadius: 5, shadowColor: '#000' }}><Text style={{ fontSize: 27, color: palette.green }}>‹</Text></Pressable>
    {weather && <View style={{ backgroundColor: palette.cream, borderRadius: 28, paddingHorizontal: 16, paddingVertical: 8, flexDirection: 'row', gap: 9, alignItems: 'center' }}><Text style={{ fontSize: 23 }}>☁</Text><View><Text style={{ fontSize: 14, fontWeight: '800', color: palette.green }}>Đà Lạt</Text><Text style={{ fontSize: 11, color: palette.green }}>Thời tiết tham khảo</Text></View></View>}
  </View>;
}
export function Action({ title, onPress, disabled, secondary, icon }: { title: string; onPress: () => void; disabled?: boolean; secondary?: boolean; icon?: string }) {
  return <Pressable accessibilityRole="button" accessibilityState={{ disabled: !!disabled }} disabled={disabled} onPress={onPress} style={({ pressed }) => ({ backgroundColor: secondary ? '#fffaf0' : palette.accent, borderRadius: 32, paddingVertical: 15, paddingHorizontal: 14, opacity: disabled ? .5 : pressed ? .8 : 1, borderWidth: secondary ? 1.5 : 2, borderColor: secondary ? '#143b32' : '#fff', minHeight: 55, justifyContent: 'center', shadowColor: '#102e27', shadowOpacity: .12, shadowRadius: 5, elevation: 2 })}>
    <Text style={{ textAlign: 'center', fontWeight: '800', fontSize: 15, color: palette.green }}>{icon ? `${icon}  ` : ''}{title}</Text>
  </Pressable>;
}
export function MockLabel({ isMock }: { isMock: boolean }) { return null; }
export function TimeTile({ label, value, children, icon }: { label: string; value: string; children?: React.ReactNode; icon?: string }) {
  return <View style={{ flex: 1, minWidth: 90, backgroundColor: '#e7f1d7', borderRadius: 18, padding: 10, gap: 6, alignItems: 'center', justifyContent: 'center' }}><Text style={{ fontSize: 23, color: palette.green }}>{icon ?? '◷'}</Text><Text style={{ color: palette.green, fontSize: 12, textAlign: 'center' }}>{label}</Text>{children ?? <Text style={{ color: palette.green, fontWeight: '900', fontSize: 16, textAlign: 'center' }}>{value}</Text>}</View>;
}
export function OptionPanels({ children }: { children: React.ReactNode }) { const { width } = useWindowDimensions(); return <View style={{ flexDirection: width >= 730 ? 'row' : 'column', gap: 12, alignItems: 'stretch' }}>{children}</View>; }
export function TimelineLine({ time, title, status, symbol }: { time: string; title: string; status: string; symbol?: string }) {
  return <View style={{ flexDirection: 'row', gap: 10, alignItems: 'center', paddingVertical: 9, borderBottomColor: '#e4e9da', borderBottomWidth: 1 }}><View style={{ backgroundColor: status === 'Đã bỏ' ? '#f8dede' : '#e6f2cf', width: 29, height: 29, borderRadius: 20, justifyContent: 'center', alignItems: 'center' }}><Text style={{ color: palette.green, fontWeight: '900' }}>{symbol ?? '✓'}</Text></View><Text style={{ color: palette.green, fontSize: 12, fontWeight: '800', width: 105 }}>{time}</Text><View style={{ flex: 1 }}><Text style={{ color: palette.green, fontSize: 14, fontWeight: '700' }}>{title}</Text><Text style={{ color: palette.gray, fontSize: 11 }}>{status}</Text></View></View>;
}
export function SectionTitle({ title, subtitle }: { title: string; subtitle?: string }) { return <View style={{ gap: 3 }}><Text style={styles.title}>{title}</Text>{subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}</View>; }
export function ChangePanel({ before, after, detail }: { before: string; after: string; detail?: string }) { return <View style={{ backgroundColor: '#e7f2d1', padding: 12, borderRadius: 15, gap: 5 }}><Text style={{ color: palette.green, fontWeight: '900' }}>⇄  Thay đổi chính</Text><Text style={{ color: palette.gray, fontSize: 12 }}>Trước: {before}</Text><Text style={{ color: palette.green, fontSize: 13, fontWeight: '800' }}>Sau: {after}</Text>{detail && <Text style={styles.muted}>{detail}</Text>}</View>; }

export function PlacePhoto({ place, height = 116 }: { place: string; height?: number }) {
  const lake = place.toLowerCase().includes('xuân hương');
  const flower = place.toLowerCase().includes('hoa') || place.toLowerCase().includes('vườn');
  if (!lake && !flower) return null;
  return <Image source={lake ? require('../../../assets/images/plan/background-original.jpg') : require('../../../assets/images/dalat-user-background.png')} resizeMode="cover" style={{ width: '100%', height, borderRadius: 15, backgroundColor: '#d8e9c8' }} accessibilityLabel={`Ảnh ${place}`}/>;
}
export function PlaceChoice({ title, selected, onPress, subtitle }: { title: string; selected: boolean; onPress: () => void; subtitle?: string }) {
  return <Pressable accessibilityRole="radio" accessibilityState={{ selected }} onPress={onPress} style={{ flexDirection: 'row', alignItems: 'center', gap: 11, backgroundColor: selected ? '#e7f4c4' : '#f7f8ee', padding: 10, borderRadius: 17, borderWidth: selected ? 1 : 0, borderColor: '#cfe78d' }}>
    <Text style={{ color: palette.green, fontSize: 23, fontWeight: '700' }}>{selected ? '☑' : '☐'}</Text>
    <View style={{ width: 106 }}><PlacePhoto place={title} height={78}/></View>
    <View style={{ flex: 1, gap: 3 }}><Text style={{ color: palette.green, fontSize: 15, fontWeight: '800' }}>{title}</Text>{subtitle && <Text style={styles.muted}>{subtitle}</Text>}</View>
  </Pressable>;
}
