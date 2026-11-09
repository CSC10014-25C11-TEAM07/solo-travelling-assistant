import { useState } from 'react';
import { router } from 'expo-router';
import { Pressable, Text, TextInput, View } from 'react-native';
import { useAdapt } from '@/features/adapt/context';
import { AdaptRequest, toMinutes, validateRequest } from '@/features/adapt/model';
import { Action, Header, MockLabel, Page, TimeTile, SectionTitle, PlaceChoice, styles, palette } from '@/features/adapt/ui';
export default function RequestScreen() {
  const { trip, kind, setKind, generate, busy, error, isMock, draft, setDraft } = useAdapt();
  const { restUntil, preferredKeep, activityId } = draft;
  const [localError, setLocalError] = useState<string | null>(null);
  async function submit() {
    const req: AdaptRequest = { kind, tripId: trip.id, baseVersion: trip.version, ...(kind === 'rest' ? { restUntil, preferredKeep } : { activityId }) };
    const invalid = validateRequest(trip, req); setLocalError(invalid); if (invalid) return;
    if (await generate(req)) router.push('/adapt/compare');
  }
  let extra = '—';
  try { const m = toMinutes(restUntil) - toMinutes(trip.restEnd); if (m >= 0) extra = m % 60 === 0 ? `+${m / 60} giờ` : `+${m} phút`; } catch { /* validation on submit */ }
  return <Page>
    <Header/>
    <SectionTitle title="Nhập yêu cầu điều chỉnh" subtitle="Cho lịch trình phù hợp hơn với tình hình hiện tại."/>
    <View style={{ flexDirection: 'row', gap: 8, marginVertical: 6 }}>
      <View style={{ flex: 1 }}><Action icon="▣" title="Nghỉ thêm" secondary={kind !== 'rest'} onPress={() => { setKind('rest'); setLocalError(null); }}/></View>
      <View style={{ flex: 1 }}><Action icon="☂" title="Đổi địa điểm" secondary={kind !== 'rain'} onPress={() => { setKind('rain'); setLocalError(null); }}/></View>
    </View>
    <View style={styles.card}>
      <Text style={styles.heading}>{kind === 'rest' ? '▣  Nghỉ thêm' : '☂  Đổi địa điểm vì mưa'}</Text>
      <Text style={styles.text}>{kind === 'rest' ? 'Bạn muốn kéo dài thời gian nghỉ để thư giãn hơn?' : 'Tìm một địa điểm trong nhà thay cho hoạt động ngoài trời chưa diễn ra.'}</Text>
      {kind === 'rest' ? <>
        <View style={{ flexDirection: 'row', gap: 8 }}>
          <TimeTile label="Nghỉ hiện tại" value={`${trip.restStart}–${trip.restEnd}`} icon="◷"/>
          <TimeTile label="Nghỉ đến" value={restUntil} icon="▣"><TextInput accessibilityLabel="Nghỉ đến (HH:mm)" style={[styles.input, { width: '100%', textAlign: 'center', fontSize: 16, paddingHorizontal: 2, paddingVertical: 6 }]} value={restUntil} onChangeText={restUntil => setDraft({ restUntil })} placeholder="15:00" keyboardType="numbers-and-punctuation" maxLength={5}/></TimeTile>
          <TimeTile label="Thêm" value={extra} icon="⊕"/>
        </View>
        <Text style={[styles.heading, { fontSize: 16, marginTop: 8 }]}>Hoạt động muốn giữ nếu có thể  ⓘ</Text>
        {trip.activities.filter(a => a.status === 'TODO').map(a => <PlaceChoice key={a.id} title={a.title} selected={preferredKeep === a.id} onPress={() => setDraft({ preferredKeep: a.id })}/>)}
      </> : <>
        <View style={{ backgroundColor: '#e7f5c5', borderRadius: 15, padding: 13 }}><Text style={styles.text}>☂  Lý do: Trời mưa</Text><Text style={styles.muted}>Yêu cầu: thay bằng địa điểm trong nhà, trong cùng ngày.</Text></View>
        <Text style={[styles.heading, { fontSize: 16 }]}>Hoạt động cần thay thế</Text>
        {trip.activities.filter(a => a.outdoor && a.status === 'TODO').map(a => <PlaceChoice key={a.id} title={a.title} subtitle={`${a.time} · Chưa thực hiện`} selected={activityId === a.id} onPress={() => setDraft({ activityId: a.id })}/>)}
      </>}
      <View style={{ backgroundColor: '#f0f0e7', borderRadius: 17, padding: 14, flexDirection: 'row', gap: 10 }}><Text style={{ color: palette.green, fontSize: 23 }}>ⓘ</Text><View style={{ flex: 1 }}><Text style={[styles.heading, { fontSize: 16 }]}>Lịch chưa thay đổi</Text><Text style={styles.muted}>Các hoạt động đã hoàn thành và những ngày khác được giữ nguyên.</Text></View></View>
    </View>
    
    {(localError || error) && <Text style={styles.error}>{localError || error}</Text>}
    <View style={{ flexDirection: 'row', gap: 9 }}><View style={{ flex: 1 }}><Action title="Quay lại" secondary onPress={() => router.back()}/></View><View style={{ flex: 1.6 }}><Action title={busy ? 'Đang tìm…' : 'Xem phương án →'} disabled={busy} onPress={submit}/></View></View>
  </Page>;
}
