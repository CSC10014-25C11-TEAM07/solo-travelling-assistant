import { GlassPanel, glassInset } from '@/components/glass/panel';
import { useState } from 'react';
import { router } from 'expo-router';
import { Text, TextInput, View, StyleSheet } from 'react-native';
import { useAdapt } from '@/features/adapt/context';
import { AdaptRequest, toMinutes, validateRequest, restPlaceName } from '@/features/adapt/model';
import { isLiveTrip, liveActivities } from '@/features/adapt/adapter';
import { Action, Header, Page, TimeTile, PlaceChoice, styles, palette } from '@/features/adapt/ui';

export default function RequestScreen() {
  const { trip, ready, available, kind, setKind, generate, busy, error, isMock, draft, setDraft, selectRest } = useAdapt();
  const { restUntil, preferredKeep, activityId } = draft;
  const [localError, setLocalError] = useState<string | null>(null);
  async function submit() {
    if (busy) return;
    const pending = trip.activities.filter(a => a.status === 'TODO');
    if (kind === 'rain' && !pending.some(a => a.id === activityId)) {
      setLocalError('Vui lòng chọn hoạt động cần thay thế.'); return;
    }
    const req: AdaptRequest = {
      kind, tripId: trip.id, baseVersion: trip.version,
      ...(kind === 'rest' ? { restUntil, preferredKeep: pending.some(a => a.id === preferredKeep) ? preferredKeep : undefined } : { activityId }),
    };
    const invalid = validateRequest(trip, req);
    setLocalError(invalid);
    if (invalid) return;
    if (await generate(req)) router.push('/adapt/compare');
  }
  let extra = '—';
  const rests = isMock ? [] : liveActivities(trip).filter(a => a.type === 'REST' && a.status === 'PENDING');
  try { const m = toMinutes(restUntil) - toMinutes(trip.restEnd); if (m >= 0) extra = m % 60 === 0 ? `+${m / 60} giờ` : `+${m} phút`; } catch { /* validation on submit */ }
  if (!ready || !available) return <Page><Header/><GlassPanel><Text style={styles.title}>Cần tải lịch hiện hành</Text><Action title="Quay về lịch" onPress={() => router.replace('/adapt')}/></GlassPanel></Page>;
  return <Page>
    <Header/>
    <GlassPanel style={local.intro}>
      <Text style={local.title}>Nhập yêu cầu{'\n'}điều chỉnh</Text>
      <Text style={styles.text}>Cho lịch trình phù hợp hơn với tình hình hiện tại.</Text>
    </GlassPanel>
    <View style={local.modeRow}>
      <View style={local.mode}><Action title="Nghỉ thêm" secondary={kind !== 'rest'} onPress={() => { setKind('rest'); setLocalError(null); }}/></View>
      <View style={local.mode}><Action title="Đổi địa điểm" secondary={kind !== 'rain'} onPress={() => { setKind('rain'); setLocalError(null); }}/></View>
    </View>
    <GlassPanel>
      <Text style={styles.heading}>{kind === 'rest' ? 'Nghỉ thêm' : 'Đổi địa điểm vì mưa'}</Text>
      <Text style={styles.text}>{kind === 'rest' ? 'Bạn muốn kéo dài thời gian nghỉ để thư giãn hơn?' : 'Tìm một địa điểm trong nhà thay cho hoạt động ngoài trời chưa diễn ra.'}</Text>
      {kind === 'rest' ? <>
        {rests.length > 1 && <>
          <Text style={local.sectionHeading}>Chọn khoảng nghỉ muốn kéo dài</Text>
          {rests.map(rest => <PlaceChoice key={rest.activity_id} title={rest.name} subtitle={`${rest.start_time}–${rest.end_time}`} selected={isLiveTrip(trip) && trip.restActivityId === rest.activity_id} onPress={() => { selectRest(rest.activity_id); setLocalError(null); }}/>) }
        </>}
        <View style={local.timeRow}>
          <View style={local.timeColumn}><TimeTile label="Nghỉ hiện tại" value={`${trip.restStart}–${trip.restEnd}`} icon="◷"/></View>
          <View style={local.timeColumn}><TimeTile label="Nghỉ đến" value={restUntil} icon="◷">
            <TextInput accessibilityLabel="Nghỉ đến (HH:mm)" style={[styles.input, local.timeInput]} value={restUntil} onChangeText={restUntil => setDraft({ restUntil })} placeholder="15:00" placeholderTextColor={palette.slate} keyboardType="numbers-and-punctuation" maxLength={5}/>
          </TimeTile></View>
        </View>
        <Text style={local.extension}>Thời gian nghỉ thêm: {extra}</Text>
        <Text style={local.sectionHeading}>Hoạt động muốn giữ nếu có thể</Text>
        {trip.activities.filter(a => a.status === 'TODO' && a.time.slice(0, 5) >= trip.restEnd).map(a => <PlaceChoice key={a.id} title={a.title} selected={preferredKeep === a.id} onPress={() => setDraft({ preferredKeep: preferredKeep === a.id ? '' : a.id })}/>)}
      </> : <>
        <View style={local.notice}><Text style={styles.text}>Lý do: Trời mưa</Text><Text style={styles.muted}>Yêu cầu: thay bằng địa điểm trong nhà, trong cùng ngày.</Text></View>
        <Text style={local.sectionHeading}>Hoạt động ngoài trời cần thay thế</Text>
        {!isMock && <Text style={styles.muted}>Chọn hoạt động chưa thực hiện mà bạn biết là ngoài trời. Backend kiểm tra điều kiện mưa theo bộ dữ liệu.</Text>}
        {trip.activities.filter(a => a.status === 'TODO' && (isMock ? a.outdoor : a.outdoor !== false)).map(a => <PlaceChoice key={a.id} title={a.title} subtitle={`${a.time} · Chưa thực hiện`} selected={activityId === a.id} onPress={() => setDraft({ activityId: a.id })}/>)}
      </>}
      <Text style={styles.muted}>Tính phương án từ: {restPlaceName(trip)}</Text>
    </GlassPanel>
    <GlassPanel>
      <Text style={local.sectionHeading}>Lịch chưa thay đổi</Text>
      <Text style={styles.muted}>Các hoạt động đã hoàn thành và những ngày khác được giữ nguyên.</Text>
    </GlassPanel>
    {(localError || error) && <Text style={styles.error}>{localError || error}</Text>}
    <Action title={busy ? 'Đang tìm…' : 'Xem phương án →'} disabled={busy} onPress={submit}/>
    <Action title="Quay lại" secondary onPress={() => router.back()}/>
  </Page>;
}
const local = StyleSheet.create({
  intro: { paddingVertical: 24, gap: 13 },
  title: { color: palette.ink, fontSize: 34, lineHeight: 41, letterSpacing: -1, fontWeight: '800' },
  modeRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 9 },
  mode: { flex: 1, minWidth: 130 },
  sectionHeading: { color: palette.ink, fontSize: 17, fontWeight: '700', lineHeight: 24 },
  timeRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  timeColumn: { flex: 1, minWidth: 120 },
  timeInput: { width: '100%', textAlign: 'center', fontSize: 21, fontVariant: ['tabular-nums'], minHeight: 44, paddingHorizontal: 2, paddingVertical: 6 },
  extension: { color: palette.pine, fontSize: 15, fontWeight: '700', fontVariant: ['tabular-nums'] },
  notice: { ...glassInset, borderRadius: 16, padding: 15, gap: 6 },
});
