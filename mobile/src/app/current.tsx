import { GlassPanel, glassInset } from '@/components/glass/panel';
import { useCallback, useState } from 'react';
import { router, useFocusEffect } from 'expo-router';
import { Text, View, Pressable, StyleSheet } from 'react-native';
import { Action, Page, styles, palette } from '@/features/plan/ui';
import { usePlan, tripDays } from '@/features/plan/state';
import { latestTrip, markDone, selectDemoTrip, sourcedDemo } from '@/features/plan/api';

export default function Current() {
  const { trip, setTrip, ready } = usePlan();
  const [day, setDay] = useState(1);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const reload = useCallback(async (): Promise<boolean> => {
    setBusy('reload'); setLoading(true); setError('');
    try { const latest = await latestTrip(); setTrip(latest); return true; }
    catch (e) { setError(e instanceof Error ? e.message : 'Không đọc được lịch đã lưu.'); return false; }
    finally { setBusy(''); setLoading(false); }
  }, [setTrip]);
  useFocusEffect(useCallback(() => { if (ready) void reload(); }, [ready, reload]));
  async function done(activityId: string) {
    if (!trip || busy) return;
    setBusy(activityId); setError('');
    try { const updated = await markDone(trip.itinerary_id, activityId, trip.version); setTrip(updated); }
    catch (e) {
      if ((e as { status?: number }).status === 409) {
        const success = await reload();
        if (success) setError('Lịch đã thay đổi. Vui lòng kiểm tra phiên bản mới.');
      } else setError(e instanceof Error ? e.message : 'Không thể cập nhật hoạt động.');
    } finally { setBusy(''); }
  }
  const days = trip ? tripDays(trip) : [];
  const selectedDay = days.find(d => d.day_number === day);
  async function switchSample(close: boolean) {
    if (busy || loading) return;
    setBusy('sample'); setError('');
    try { const selected = await selectDemoTrip(trip, close); setTrip(selected); setDay(close ? 1 : 2); }
    catch (e) { setError(e instanceof Error ? e.message : 'Chưa đổi được lịch. Hãy tải lại.'); }
    finally { setBusy(''); }
  }
  return <Page>
    <GlassPanel style={{ paddingVertical: 25, gap: 14 }}>
      <Text accessibilityRole="header" style={local.routeTitle}>Lịch đã lưu</Text>
      {trip && <Text style={styles.text}>{trip.departure_date} → {trip.return_date}</Text>}
      <Action title={loading ? 'Đang tải lịch…' : 'Tải lại lịch'} secondary disabled={!!busy} onPress={reload}/>
    </GlassPanel>
    {!ready || (loading && !trip) ? <GlassPanel><Text style={styles.muted}>Đang tải lịch…</Text></GlassPanel> : !trip ? <GlassPanel>
      <Text style={styles.heading}>{error ? 'Chưa thể tải lịch' : 'Bạn chưa có lịch đã lưu'}</Text>
      <Action title="Lên kế hoạch chuyến đi" onPress={() => router.push('/plan')}/>
    </GlassPanel> : <>
      <GlassPanel>
        <Text style={styles.heading}>Điều chỉnh hành trình</Text>
        <Text style={styles.muted}>Theo dõi các hoạt động và đánh dấu khi bạn hoàn thành.</Text>
        <Text style={styles.muted}>Lịch hiện hành · Phiên bản {trip.version}</Text>
        <Text selectable style={local.tripId}>Mã lịch: {trip.itinerary_id}</Text>
        <Action title="Điều chỉnh lịch trình" onPress={() => router.push('/adapt')}/>
      </GlassPanel>
      <View style={styles.row}>{days.map(d => <Pressable key={d.day_id} accessibilityRole="tab" accessibilityState={{ selected: day === d.day_number }} onPress={() => setDay(d.day_number)} style={[local.day, day === d.day_number && local.daySelected]}>
        <Text style={[local.dayLabel, day === d.day_number && { color: palette.foam }]}>Ngày {d.day_number}</Text>
      </Pressable>)}</View>
      <GlassPanel>
        <Text style={styles.heading}>Ngày {day}{selectedDay?.date ? ` · ${selectedDay.date.split('-').reverse().join('-')}` : ''}</Text>
        {[...(selectedDay?.activities || [])].filter(a => a.status === 'PENDING' || a.status === 'DONE').sort((a, b) => a.start_time.localeCompare(b.start_time)).map(a => <View key={a.activity_id} style={local.activity}>
          <View style={local.rail}><View style={[local.dot, a.status === 'DONE' && { backgroundColor: palette.mist }]}><Text style={local.dotLabel}>{a.status === 'DONE' ? '✓' : ''}</Text></View></View>
          <View style={{ flex: 1, gap: 8 }}>
            <Text style={local.time}>{a.start_time}–{a.end_time}</Text>
            <Text style={local.activityTitle}>{a.name}</Text>
            <Text style={styles.muted}>{a.type === 'REST' ? 'Nghỉ ngơi' : a.type === 'TRAVEL' ? 'Di chuyển bằng xe máy' : 'Tham quan'} · {a.status === 'DONE' ? 'Đã hoàn thành' : 'Chưa thực hiện'}</Text>
            {a.status === 'PENDING' && <Action title={busy === a.activity_id ? 'Đang lưu…' : 'Đánh dấu hoàn thành'} disabled={!!busy} secondary onPress={() => done(a.activity_id)}/>}
          </View>
        </View>)}
      </GlassPanel>
    </>}
    {sourcedDemo && ready && !loading && <GlassPanel>
      <Text style={styles.heading}>Thử điều chỉnh lịch</Text>
      <Text style={styles.muted}>Mẫu 3 ngày dùng địa điểm thật. Ngày 2 đã đi ga, đang nghỉ ở Still Cafe. Bạn có thể thử nghỉ đến 15:00 hoặc đổi Hồ Xuân Hương khi trời mưa.</Text>
      <Action title={trip?.is_demo_sample ? 'Nạp lại lịch mẫu từ đầu' : 'Mở lịch mẫu riêng'} secondary disabled={!!busy} onPress={() => switchSample(false)}/>
      {trip?.is_demo_sample && <Action title="Đóng mẫu, trở về lịch cá nhân" secondary disabled={!!busy} onPress={() => switchSample(true)}/>}
    </GlassPanel>}
    {!!error && <Text style={styles.error}>{error}</Text>}
  </Page>;
}
const local = StyleSheet.create({
  routeTitle: { color: palette.ink, fontSize: 34, lineHeight: 41, letterSpacing: -1, fontWeight: '800' },
  tripId: { color: palette.slate, fontSize: 12, lineHeight: 18 },
  day: { ...glassInset, backgroundColor: palette.pane, flex: 1, minWidth: 62, minHeight: 46, alignItems: 'center', justifyContent: 'center', borderRadius: 13, padding: 9 },
  daySelected: { backgroundColor: palette.pine, borderColor: palette.pine },
  dayLabel: { color: palette.ink, fontWeight: '700', fontSize: 14 },
  activity: { flexDirection: 'row', gap: 13, paddingTop: 14, paddingBottom: 18 },
  rail: { width: 19, borderLeftWidth: 1, borderColor: 'rgba(7,94,87,.22)', marginLeft: 9 },
  dot: { width: 19, height: 19, marginLeft: -10, marginTop: 1, borderRadius: 10, borderWidth: 3, borderColor: palette.foam, backgroundColor: palette.pine, alignItems: 'center', justifyContent: 'center' },
  dotLabel: { color: palette.pine, fontSize: 10, fontWeight: '800' },
  time: { color: palette.pine, fontSize: 14, fontWeight: '700', fontVariant: ['tabular-nums'] },
  activityTitle: { color: palette.ink, fontSize: 19, lineHeight: 26, fontWeight: '700' },
});
