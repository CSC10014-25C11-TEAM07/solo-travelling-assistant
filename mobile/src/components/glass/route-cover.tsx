import { StyleSheet, Text, View } from 'react-native';
import { palette } from './colors';
import { GlassPanel } from './panel';

// Keep the landscape between the two lenses uncovered, so the edge of the glass reads.
export function RouteCover() {
  return <View style={s.cover}>
    <GlassPanel kind="chip" style={s.route}><View style={s.origin} /><Text style={s.from}>Đi từ TP. Hồ Chí Minh</Text></GlassPanel>
    <GlassPanel kind="caption" style={s.caption}>
      <Text accessibilityRole="header" style={s.city}>Đà Lạt</Text>
      <Text style={s.byline}>Sổ hành trình xe máy</Text>
    </GlassPanel>
  </View>;
}
const s = StyleSheet.create({
  cover: { minHeight: 202, alignItems: 'flex-start', justifyContent: 'space-between', gap: 18 },
  route: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 14, paddingVertical: 8 },
  origin: { borderColor: palette.pine, borderWidth: 2, width: 10, height: 10, borderRadius: 5 },
  from: { color: palette.ink, fontSize: 13, lineHeight: 19, fontWeight: '600' },
  caption: { paddingHorizontal: 18, paddingVertical: 12, minWidth: '55%' },
  city: { color: palette.foam, fontSize: 38, lineHeight: 48, letterSpacing: -1.1, fontWeight: '700' },
  byline: { color: '#ECFCF6', fontSize: 14, lineHeight: 21, fontWeight: '500' },
});
