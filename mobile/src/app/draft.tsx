import { GlassPanel, glassInset } from '@/components/glass/panel';
import { useState } from 'react';
import { router } from 'expo-router';
import { Text, View, TextInput, Pressable, StyleSheet } from 'react-native';
import { Action, Page, styles, palette } from '@/features/plan/ui';
import { usePlan, tripDays } from '@/features/plan/state';
import { configured, confirmDraft, sourcedDemo } from '@/features/plan/api';
import { arrivalEstimates } from '@/features/plan/arrival-review';

export default function Draft() {
  const { trip, setTrip, draftId, setDraftId } = usePlan();
  const [day, D] = useState(1);
  const [busy, B] = useState(false);
  const [err, E] = useState('');
  if (!trip) return <Page>
    <GlassPanel><Text style={styles.title}>Chưa có lịch nháp</Text><Action title="Nhập nhu cầu" onPress={() => router.replace('/plan')}/></GlassPanel>
  </Page>;

  const days = tripDays(trip);
  const arrivals = arrivalEstimates(days);
  const selectedDay = days.find(d => d.day_number === day);
  function changeTime(activityId: string, field: 'start_time' | 'end_time', value: string) {
    if (configured || !trip) return;
    setTrip({ ...trip, itinerary_days: days.map(d => ({ ...d, activities: d.activities.map(a => a.activity_id === activityId ? { ...a, [field]: value } : a) })) });
  }
  function adjustTime(activityId: string, field: 'start_time' | 'end_time', delta: number) {
    if (configured) return;
    const a = days.flatMap(d => d.activities).find(x => x.activity_id === activityId);
    if (!a) return;
    const value = a[field];
    if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(value)) return;
    const [h, m] = value.split(':').map(Number);
    const total = Math.max(0, Math.min(1439, h * 60 + m + delta));
    const newTime = String(Math.floor(total / 60)).padStart(2, '0') + ':' + String(total % 60).padStart(2, '0');
    changeTime(activityId, field, newTime);
  }
  async function confirm() {
    if (!trip || busy || !arrivals) return;
    if (!draftId) { E('Không tìm thấy mã lịch nháp. Vui lòng tạo lại lịch.'); return; }
    B(true); E('');
    try {
      const next = await confirmDraft(draftId, true);
      setTrip(next); setDraftId(null); router.replace('/current');
    } catch (e) { E(e instanceof Error ? e.message : 'Không xác nhận được lịch.'); }
    finally { B(false); }
  }
  return <Page>
    <GlassPanel style={{ gap: 14, paddingVertical: 24 }}>
      <Text style={local.state}>Lịch nháp · {days.length} ngày</Text>
      <Text accessibilityRole="header" style={local.routeTitle}>Xem lại hành trình</Text>
      <Text style={styles.text}>{trip.departure_date} → {trip.return_date}</Text>
      <Text style={styles.muted}>Xem lại từng ngày. Lịch chỉ được lưu khi bạn đồng ý bên dưới.</Text>
    </GlassPanel>
    {sourcedDemo && <GlassPanel><Text style={styles.muted}>Khứ hồi từ Công trường Công xã Paris, nghỉ ở La Ngà, Bảo Lộc và Đức Trọng. Mốc qua đêm ở đường Huỳnh Thúc Kháng gần Crazy House. Thời gian xe máy là ước tính từ OpenStreetMap và Valhalla. Chặng TP.HCM ↔ La Ngà có hạn chế theo giờ trên bản đồ. Kiểm tra tình trạng đường và chỗ nghỉ trước chuyến đi.</Text></GlassPanel>}

    <GlassPanel>
      <Text style={styles.heading}>Giờ đến dự kiến</Text>
      <Text style={styles.text}>Xem giờ đến từng ngày trước khi lưu lịch.</Text>
      {arrivals ? arrivals.map(arrival => <View key={arrival.dayNumber} style={local.arrival}>
        <View style={{ flex: 1, gap: 3 }}><Text style={local.label}>Ngày {arrival.dayNumber}</Text><Text style={styles.muted}>{arrival.date.split('-').reverse().join('-')}</Text></View>
        <View style={{ gap: 3 }}><Text style={local.arrivalTime}>{arrival.time}</Text><Text style={styles.muted}>Dự kiến đến nơi</Text></View>
      </View>) : <Text style={styles.error}>Không đọc được giờ đến. Vui lòng tạo lại lịch.</Text>}
      <Text style={styles.muted}>Giờ đến được tính theo thời gian di chuyển và nghỉ trong lịch; thực tế có thể thay đổi.</Text>
    </GlassPanel>

    <View style={styles.row}>{days.map(d => <Pressable key={d.day_id} accessibilityRole="tab" accessibilityState={{ selected: day === d.day_number }} onPress={() => D(d.day_number)} style={[local.day, day === d.day_number && local.daySelected]}>
      <Text style={[local.dayLabel, day === d.day_number && { color: palette.foam }]}>Ngày {d.day_number}</Text>
    </Pressable>)}</View>

    <GlassPanel>
      <Text style={styles.heading}>Ngày {day}{selectedDay?.date ? ` · ${selectedDay.date.split('-').reverse().join('-')}` : ''}</Text>
      <Text style={styles.muted}>Lịch trình được sắp xếp theo thời gian.</Text>
      {[...(selectedDay?.activities || [])].sort((a, b) => a.start_time.localeCompare(b.start_time)).map(a => <View key={a.activity_id} style={local.activity}>
        <View style={local.rail}><View style={[local.dot, a.type === 'REST' && { backgroundColor: palette.mist }]}/></View>
        <View style={{ flex: 1, gap: 10 }}>
          <Text style={local.activityTitle}>{a.name}</Text>
          <View style={styles.row}>{(['start_time', 'end_time'] as const).map(field => <View key={field} style={{ flex: 1, minWidth: 160, gap: 5 }}>
            <Text style={styles.muted}>{field === 'start_time' ? 'Bắt đầu' : 'Kết thúc'}</Text>
            <View style={local.timeControls}>
              <Pressable accessibilityRole="button" accessibilityLabel={`Giảm 15 phút ${field === 'start_time' ? 'bắt đầu' : 'kết thúc'} ${a.name}`} accessibilityState={{ disabled: configured }} disabled={configured} onPress={() => adjustTime(a.activity_id, field, -15)} style={[local.step, configured && { opacity: .4 }]}><Text style={local.stepText}>−</Text></Pressable>
              <TextInput accessibilityLabel={`${field === 'start_time' ? 'Bắt đầu' : 'Kết thúc'} ${a.name}`} editable={!configured} value={a[field]} onChangeText={v => changeTime(a.activity_id, field, v)} style={local.timeInput}/>
              <Pressable accessibilityRole="button" accessibilityLabel={`Tăng 15 phút ${field === 'start_time' ? 'bắt đầu' : 'kết thúc'} ${a.name}`} accessibilityState={{ disabled: configured }} disabled={configured} onPress={() => adjustTime(a.activity_id, field, 15)} style={[local.step, configured && { opacity: .4 }]}><Text style={local.stepText}>+</Text></Pressable>
            </View>
          </View>)}</View>
          <Text style={styles.muted}>{a.type === 'REST' ? 'Nghỉ ngơi' : a.type === 'TRAVEL' ? 'Di chuyển bằng xe máy' : 'Tham quan'} · {a.status}</Text>
        </View>
      </View>)}
    </GlassPanel>

    {!!err && <Text style={styles.error}>{err}</Text>}
    <GlassPanel>
      <Text style={styles.text}>Bạn có đồng ý với các mốc giờ đến dự kiến này không?</Text>
      <Action title={busy ? 'Đang lưu…' : 'Đồng ý và lưu lịch'} disabled={busy || !arrivals} onPress={confirm}/>
      <Action title="Sửa yêu cầu" secondary disabled={busy} onPress={() => router.back()}/>
    </GlassPanel>
  </Page>;
}
const local = StyleSheet.create({
  state: { color: palette.pine, fontSize: 14, lineHeight: 20, fontWeight: '700' },
  routeTitle: { color: palette.ink, fontSize: 35, lineHeight: 42, letterSpacing: -1, fontWeight: '800' },
  label: { color: palette.ink, fontSize: 15, fontWeight: '700' },
  arrival: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 12, paddingVertical: 12, borderTopWidth: 1, borderColor: 'rgba(7,94,87,.16)' },
  arrivalTime: { color: palette.pine, fontSize: 28, lineHeight: 34, fontWeight: '700', fontVariant: ['tabular-nums'] },
  day: { ...glassInset, backgroundColor: palette.pane, flex: 1, minWidth: 62, minHeight: 46, justifyContent: 'center', alignItems: 'center', borderRadius: 13, padding: 9 },
  daySelected: { backgroundColor: palette.pine, borderColor: palette.pine },
  dayLabel: { color: palette.ink, fontSize: 14, fontWeight: '700' },
  activity: { flexDirection: 'row', gap: 12, paddingTop: 13, paddingBottom: 17 },
  rail: { width: 13, alignItems: 'center', borderLeftWidth: 1, borderColor: 'rgba(7,94,87,.22)', marginLeft: 5 },
  dot: { width: 11, height: 11, borderRadius: 6, backgroundColor: palette.pine, borderWidth: 2, borderColor: palette.foam, marginLeft: -13, marginTop: 5 },
  activityTitle: { color: palette.ink, fontSize: 18, lineHeight: 25, fontWeight: '700' },
  timeControls: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  step: { ...glassInset, width: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center', borderRadius: 11 },
  stepText: { color: palette.pine, fontSize: 23, fontWeight: '600' },
  timeInput: { ...glassInset, flex: 1, minWidth: 65, minHeight: 44, textAlign: 'center', fontVariant: ['tabular-nums'], fontWeight: '700', fontSize: 16, color: palette.ink, borderRadius: 11, padding: 7 },
});
