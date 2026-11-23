import type { ReactNode } from 'react';
import { router } from 'expo-router';
import { ImageBackground, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import type { Activity } from './api';

const ink = '#17382f';
const muted = '#50635a';
const green = '#185541';

export function SchedulePage({ children, footer }: { children: ReactNode; footer?: ReactNode }) {
  return (
    <SafeAreaView style={s.screen}>
      <ScrollView contentContainerStyle={s.content} keyboardShouldPersistTaps="handled">
        {children}
      </ScrollView>
      {footer && <View style={s.footer}><View style={s.footerContent}>{footer}</View></View>}
    </SafeAreaView>
  );
}

export function ScheduleButton({ title, onPress, disabled, variant = 'secondary', label, selected }: {
  title: string;
  onPress: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'text';
  label?: string;
  selected?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled: !!disabled, selected }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        s.button, variant === 'primary' && s.primary, variant === 'text' && s.textButton,
        (pressed || disabled) && s.dimmed,
      ]}
    >
      <Text style={[s.buttonTitle, variant === 'primary' && s.primaryTitle]}>{title}</Text>
    </Pressable>
  );
}

export function ScheduleHeader({ action }: { action?: ReactNode }) {
  return (
    <View style={s.header}>
      <ScheduleButton title="‹  Quay lại" variant="text" onPress={() => {
        if (router.canGoBack()) router.back();
        else router.replace('/plan');
      }}/>
      {action}
    </View>
  );
}

export function ScheduleCover({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <ImageBackground
      source={require('../../../assets/images/plan/background-original.jpg')}
      imageStyle={s.coverImage}
      style={s.cover}
      resizeMode="cover"
    >
      <View style={s.coverShade}>
        <Text accessibilityRole="header" style={s.coverTitle}>{title}</Text>
        {subtitle && <Text style={s.coverSubtitle}>{subtitle}</Text>}
      </View>
    </ImageBackground>
  );
}

export function displayDate(value: string) {
  const parts = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  return parts ? [parts[3], parts[2], parts[1]].join('/') : value;
}

export function DayPicker({ days, selected, onSelect, disabled }: {
  days: { day_number: number; date?: string }[];
  selected: number;
  onSelect: (day: number) => void;
  disabled?: boolean;
}) {
  return (
    <View style={s.days}>
      {days.map(day => (
        <Pressable
          key={day.day_number}
          accessibilityRole="tab"
          aria-selected={day.day_number === selected}
          accessibilityLabel={['Ngày ' + day.day_number, day.date && displayDate(day.date)].filter(Boolean).join(', ')}
          disabled={disabled}
          onPress={() => onSelect(day.day_number)}
          style={[s.day, day.day_number === selected && s.activeDay]}
        >
          <Text style={s.dayTitle}>Ngày {day.day_number}</Text>
        </Pressable>
      ))}
    </View>
  );
}

type TimelineActivity = Pick<Activity, 'name' | 'start_time' | 'end_time' | 'type'> & { status?: Activity['status'] };
const activityLabels = {
  VISIT: { label: 'Tham quan', sign: '●', color: '#205c46', background: '#e3f2e8' },
  TRAVEL: { label: 'Di chuyển', sign: '→', color: '#285675', background: '#e8f2fa' },
  REST: { label: 'Nghỉ ngơi', sign: 'Ⅱ', color: '#81531b', background: '#fbefdc' },
};
const statusLabels = { PENDING: 'Chưa thực hiện', DONE: 'Đã xong', DROPPED: 'Đã bỏ', REPLACED: 'Đã thay thế' };

export function Timeline({ children }: { children: ReactNode }) {
  return <View style={s.timeline}>{children}</View>;
}

export function ScheduleActivity({ activity, children, completion }: {
  activity: TimelineActivity;
  children?: ReactNode;
  completion?: { saving: boolean; disabled: boolean; onPress: () => void };
}) {
  const kind = activityLabels[activity.type];
  return (
    <View style={s.event}>
      <View style={s.eventRail}>
        <View style={[s.eventIcon, { backgroundColor: kind.background }]}>
          <Text accessible={false} style={[s.iconText, { color: kind.color }]}>{kind.sign}</Text>
        </View>
        <View style={s.railLine}/>
      </View>
      <View style={s.eventBody}>
        <View style={s.eventMeta}>
          <Text style={s.eventTime}>{activity.start_time}–{activity.end_time}</Text>
          <Text style={[s.kind, { color: kind.color }]}>{kind.label}</Text>
        </View>
        <Text style={s.eventTitle}>
          {activity.type === 'TRAVEL' ? activity.name.replace(/^Di chuyển (?=\S)/, '') : activity.name}
        </Text>
        {(activity.status || completion) && (
          <View style={s.eventMeta}>
            {activity.status && <Text style={activity.status === 'DONE' ? s.done : s.note}>{statusLabels[activity.status]}</Text>}
            {completion && (
              <ScheduleButton
                variant="text"
                title={completion.saving ? 'Đang lưu…' : 'Đánh dấu đã xong'}
                label={'Đánh dấu đã xong: ' + activity.name}
                disabled={completion.disabled}
                onPress={completion.onPress}
              />
            )}
          </View>
        )}
        {children}
      </View>
    </View>
  );
}

export const scheduleStyles = StyleSheet.create({
  panel: { backgroundColor: '#fff', borderRadius: 18, borderWidth: 1, borderColor: '#dde7df', padding: 16, gap: 8 },
  panelTitle: { color: ink, fontSize: 19, fontWeight: '800' },
  note: { color: muted, fontSize: 14, lineHeight: 20 },
  section: { gap: 10 },
  error: { color: '#842828', backgroundColor: '#fdeceb', padding: 12, borderRadius: 12, fontSize: 14, lineHeight: 20 },
});

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#f4f7f3' },
  content: { width: '100%', maxWidth: 620, alignSelf: 'center', paddingHorizontal: 18, paddingTop: 6, paddingBottom: 24, gap: 16 },
  footer: { backgroundColor: '#fff', borderTopWidth: 1, borderColor: '#dde7df' },
  footerContent: { width: '100%', maxWidth: 620, alignSelf: 'center', paddingHorizontal: 18, paddingVertical: 8, gap: 2 },
  header: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' },
  cover: { borderRadius: 20, overflow: 'hidden', backgroundColor: green },
  coverImage: { opacity: 0.88 },
  coverShade: { paddingHorizontal: 20, paddingVertical: 23, gap: 5, backgroundColor: 'rgba(10,42,32,0.62)' },
  coverTitle: { color: '#fff', fontSize: 29, lineHeight: 35, fontWeight: '800' },
  coverSubtitle: { color: '#e8f4ea', fontSize: 14, lineHeight: 21, fontWeight: '600' },
  days: { flexDirection: 'row', flexWrap: 'wrap', gap: 7 },
  day: { flexGrow: 1, minWidth: 62, backgroundColor: '#fff', borderRadius: 12, borderWidth: 1, borderColor: '#d8e4dc', paddingHorizontal: 9, paddingVertical: 10, minHeight: 44, alignItems: 'center', justifyContent: 'center' },
  activeDay: { backgroundColor: '#e3f1e8', borderColor: green },
  dayTitle: { color: ink, fontSize: 14, fontWeight: '700', textAlign: 'center' },
  timeline: { borderWidth: 1, borderColor: '#dde7df', borderRadius: 18, backgroundColor: '#fff', padding: 12 },
  event: { flexDirection: 'row', alignItems: 'stretch', gap: 10 },
  eventRail: { alignItems: 'center', width: 30, paddingTop: 8 },
  eventIcon: { width: 30, height: 30, borderRadius: 15, alignItems: 'center', justifyContent: 'center' },
  iconText: { fontSize: 15, fontWeight: '800' },
  railLine: { width: 1, flex: 1, marginTop: 3, backgroundColor: '#d9e5dd' },
  eventBody: { flex: 1, minWidth: 0, paddingVertical: 10, gap: 4, borderBottomWidth: StyleSheet.hairlineWidth, borderColor: '#e0e9e2' },
  eventMeta: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 8 },
  eventTime: { color: ink, fontSize: 13, fontWeight: '800', fontVariant: ['tabular-nums'] },
  kind: { fontSize: 12, fontWeight: '700' },
  eventTitle: { color: ink, fontSize: 17, lineHeight: 23, fontWeight: '700' },
  note: { color: muted, fontSize: 13, lineHeight: 18 },
  done: { color: green, fontSize: 13, lineHeight: 18, fontWeight: '700' },
  button: { minHeight: 44, alignItems: 'center', justifyContent: 'center', paddingVertical: 9, paddingHorizontal: 13, borderRadius: 12, borderWidth: 1, borderColor: '#bdd5c6', backgroundColor: '#fff' },
  primary: { backgroundColor: green, borderColor: green },
  textButton: { alignSelf: 'flex-start', borderWidth: 0, backgroundColor: 'transparent', paddingHorizontal: 3 },
  buttonTitle: { color: green, textAlign: 'center', fontSize: 15, fontWeight: '700' },
  primaryTitle: { color: '#fff' },
  dimmed: { opacity: 0.58 },
});
