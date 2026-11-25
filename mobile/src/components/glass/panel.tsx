import { createContext, useContext, useRef, type ComponentRef, type ReactNode, type RefObject } from 'react';
import { Image, Platform, StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';
import { BlurTargetView, BlurView } from 'expo-blur';
import { GlassView, isGlassEffectAPIAvailable, isLiquidGlassAvailable } from 'expo-glass-effect';
import { palette } from './colors';

type PhotoTarget = ComponentRef<typeof View>;
const Scene = createContext<RefObject<PhotoTarget | null> | undefined>(undefined);

/** Only the photo is a blur target. Text above the lens never gets sampled. */
export function GlassScene({ children }: { children: ReactNode }) {
  const target = useRef<PhotoTarget>(null);
  return <Scene.Provider value={target}><View style={s.scene}>
    <BlurTargetView ref={target} collapsable={false} pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={StyleSheet.absoluteFill}>
      <Image accessible={false} source={require('../../../assets/images/plan/background-original.jpg')} resizeMode="cover" style={s.photo} />
      <View style={[StyleSheet.absoluteFill, s.daylight]} />
    </BlurTargetView>
    {children}
  </View></Scene.Provider>;
}

type Kind = 'card' | 'field' | 'chip' | 'caption';
const radii = { card: 24, field: 14, chip: 22, caption: 23 };
const webLens = { backdropFilter: 'blur(9px) saturate(138%)', WebkitBackdropFilter: 'blur(9px) saturate(138%)' };
const topLight = 'linear-gradient(146deg, rgba(255,255,255,0.44) 0%, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0) 62%, rgba(185,241,234,0.18) 100%)';
const darkLight = 'linear-gradient(145deg, rgba(211,255,246,0.18) 0%, rgba(211,255,246,0) 52%, rgba(34,100,90,0.22) 100%)';

export function GlassPanel({ children, kind = 'card', style, testID }: { children: ReactNode; kind?: Kind; style?: StyleProp<ViewStyle>; testID?: string }) {
  const target = useContext(Scene);
  const dark = kind === 'caption';
  const radius = radii[kind];
  const nativeGlass = Platform.OS === 'ios' && isGlassEffectAPIAvailable() && isLiquidGlassAvailable();
  // An inset field is already over a blurred card: add its own lens coating, not
  // another capture of the same photograph (which would erase the parent tint).
  const inset = kind === 'field';
  const fill = dark ? 'rgba(5,38,40,0.70)' : inset ? 'rgba(237,255,253,0.29)' : palette.pane;
  return <View testID={testID} style={[s.shell, { borderRadius: radius }, kind === 'card' && s.card, inset && s.inset, style]}>
    <View pointerEvents="none" accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={[StyleSheet.absoluteFill, s.clip, { borderRadius: radius }]}>
      {!inset && Platform.OS !== 'web' && (nativeGlass
        ? <GlassView colorScheme={dark ? 'dark' : 'light'} glassEffectStyle="clear" style={[StyleSheet.absoluteFill, { borderRadius: radius }]} />
        : <BlurView tint="default" intensity={34} blurReductionFactor={2} {...(Platform.OS === 'android' ? { blurTarget: target, blurMethod: 'dimezisBlurViewSdk31Plus' as const } : {})} style={[StyleSheet.absoluteFill, { borderRadius: radius }]} />)}
      <View style={[StyleSheet.absoluteFill, Platform.OS === 'web' && !inset ? webLens as ViewStyle : undefined, { borderRadius: radius, backgroundColor: fill, backgroundImage: dark ? darkLight : topLight }]} />
      <View style={[StyleSheet.absoluteFill, s.edge, { borderRadius: radius }]} />
    </View>
    {children}
  </View>;
}

// Small controls that sit on top of an existing lens need a bevel, not another blur pass.
export const glassInset = {
  backgroundColor: 'rgba(238,254,251,0.31)', backgroundImage: topLight, borderWidth: 1,
  borderColor: 'rgba(64,102,100,0.52)', borderTopColor: '#FFFFFFE8', borderLeftColor: '#FFFFFFB8',
} satisfies ViewStyle;
const s = StyleSheet.create({
  scene: { flex: 1, backgroundColor: palette.mist },
  photo: { width: '100%', height: '100%' },
  daylight: { backgroundColor: 'rgba(229,247,246,0.22)' },
  shell: { position: 'relative', boxShadow: '0px 4px 14px rgba(10,41,43,0.18)' },
  card: { padding: 19, gap: 13 }, inset: { boxShadow: '0px 1px 3px rgba(10,41,43,0.18)' },
  clip: { overflow: 'hidden' },
  edge: { borderWidth: 1, borderTopColor: '#FFFFFFEF', borderLeftColor: '#FFFFFFC7', borderRightColor: '#E3FBF6AD', borderBottomColor: '#DAFFF2B3', boxShadow: 'inset 0px 1px 1px rgba(255,255,255,0.57), inset 0px -2px 3px rgba(33,88,88,0.17)' },
});
