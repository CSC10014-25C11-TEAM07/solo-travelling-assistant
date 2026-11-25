import { useState, type ReactNode } from 'react';
import { Text, TextInput, View } from 'react-native';
import { GlassPanel } from '@/components/glass/panel';
import { palette, styles } from '@/components/glass/travel-ui';
export { Action, Header, Page, palette, styles } from '@/components/glass/travel-ui';

export function Field({ label, value, onChangeText, secure = false, placeholder }: { label: string; value: string; onChangeText: (value: string) => void; secure?: boolean; placeholder?: string }) {
  const [focused, setFocused] = useState(false);
  return <View style={{ gap: 6 }}>
    <Text style={{ color: palette.ink, fontWeight: '600', fontSize: 15 }}>{label}</Text>
    <GlassPanel kind="field" style={focused ? { boxShadow: '0px 0px 0px 2px #08443F' } : undefined}>
      <TextInput accessibilityLabel={label} autoCapitalize="none" autoCorrect={false} secureTextEntry={secure} placeholder={placeholder ?? label} placeholderTextColor={palette.slate} value={value} onChangeText={onChangeText} onFocus={() => setFocused(true)} onBlur={() => setFocused(false)} selectionColor={palette.pine} underlineColorAndroid="transparent" style={[styles.input, { backgroundColor: 'transparent', borderWidth: 0 }]} />
    </GlassPanel>
  </View>;
}
export function Note({ children }: { children: ReactNode }) { return <Text style={styles.muted}>{children}</Text>; }
