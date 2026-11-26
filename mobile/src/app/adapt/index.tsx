import { GlassPanel } from '@/components/glass/panel';
import { router } from 'expo-router';
import { Text, View, StyleSheet } from 'react-native';
import { useAdapt } from '@/features/adapt/context';
import { activeTravelLegs, isActive, restPlaceName, travelRouteName } from '@/features/adapt/model';
import { Action, Page, PlacePhoto, Header, TimelineLine, styles, palette } from '@/features/adapt/ui';
import { liveActivities, liveDays } from '@/features/adapt/adapter';

export default function CurrentScreen() {
  const { trip, setKind, reset, isMock, ready, available, busy, error, load } = useAdapt();
  if (!ready || (!available && busy)) return <Page><Header/><GlassPanel><Text style={styles.title}>Đang tải lịch hiện hành…</Text></GlassPanel></Page>;
  if (!available) return <Page><Header/><GlassPanel>
    <Text style={styles.title}>Chưa có lịch hiện hành</Text>
    <Text style={styles.text}>{error || 'Vui lòng tạo và xác nhận lịch trước khi điều chỉnh.'}</Text>
    <Action title="Thử tải lại" onPress={() => void load()}/>
    <Action title="Xem lịch đã lưu" secondary onPress={() => router.replace('/current')}/>
  </GlassPanel></Page>;
  return <Page>
    <Header/>
    <GlassPanel style={local.intro}>
      <Text style={local.dayLabel}>Lịch hiện hành · Ngày {trip.day}</Text>
      <Text accessibilityRole="header" style={local.title}>Điều chỉnh hành trình</Text>
      <Text style={styles.text}>Mốc kết thúc ngày: {trip.deadline}</Text>
    </GlassPanel>
    {!isMock && <View style={styles.row}>{liveDays(trip).map(day => <View key={day} style={{ flex: 1, minWidth: 65 }}><Action title={'Ngày ' + day} secondary={day !== trip.day} disabled={busy} onPress={() => void load(day)}/></View>)}</View>}
    <GlassPanel>
      <Text style={styles.heading}>Khoảng nghỉ hiện tại</Text>
      <Text style={local.restTime}>{trip.restStart}–{trip.restEnd}</Text>
      <Text style={styles.text}>Nghỉ tại {restPlaceName(trip)}</Text>
      <View style={local.divider}/>
      <Text style={styles.heading}>Lịch trong ngày</Text>
      {trip.activities.filter(a => isActive(a.status)).sort((a, b) => a.time.localeCompare(b.time)).map(a => <View key={a.id} style={{ gap: 10 }}>
        <TimelineLine time={a.time} title={a.title} status={a.status === 'DONE' ? 'Đã hoàn thành' : a.status === 'SKIPPED' ? 'Đã bỏ' : a.status === 'REPLACED' ? 'Đã thay thế' : 'Chưa thực hiện'} symbol={a.status === 'DONE' ? '✓' : '○'}/>
        {a.outdoor && <PlacePhoto place={a.title} height={190}/>}
      </View>)}
      <Text style={[styles.heading, { fontSize: 17, marginTop: 8 }]}>Các chặng di chuyển</Text>
      {!isMock && liveActivities(trip).filter(a => a.type === 'TRAVEL' && (a.status === 'PENDING' || a.status === 'DONE')).sort((a, b) => a.start_time.localeCompare(b.start_time)).map(a => <TimelineLine key={a.activity_id} time={`${a.start_time}–${a.end_time}`} title={a.name} status={a.status === 'DONE' ? 'Đã hoàn thành' : 'Chưa thực hiện'} symbol="↗"/>)}
      {isMock && activeTravelLegs(trip).map(l => <TimelineLine key={l.activity_id} time={`${l.start_time}–${l.end_time}`} title={travelRouteName(trip, l.from_place_id, l.to_place_id)} status={l.status === 'DONE' ? 'Đã hoàn thành' : 'Chưa thực hiện'} symbol="↗"/>)}
    </GlassPanel>
    {!isMock && <Action title="Tải lại lịch từ backend" secondary disabled={busy} onPress={() => void load()}/>}
    <GlassPanel>
      <Text style={styles.heading}>Bạn muốn điều chỉnh gì?</Text>
      <Text style={styles.muted}>Xem phương án trước khi quyết định. Lịch chỉ thay đổi khi bạn chọn áp dụng.</Text>
      <Action title="Nghỉ thêm" onPress={() => { setKind('rest'); router.push('/adapt/request'); }}/>
      <Action title="Đổi địa điểm vì mưa" secondary onPress={() => { setKind('rain'); router.push('/adapt/request'); }}/>
    </GlassPanel>
    {isMock && <Action title="Khôi phục lịch ban đầu" secondary onPress={reset}/>}
  </Page>;
}
const local = StyleSheet.create({
  intro: { gap: 14, paddingVertical: 24 },
  dayLabel: { color: palette.pine, fontSize: 14, lineHeight: 20, fontWeight: '700' },
  title: { color: palette.ink, fontSize: 34, lineHeight: 41, letterSpacing: -1, fontWeight: '800' },
  restTime: { color: palette.pine, fontSize: 32, lineHeight: 39, fontWeight: '700', fontVariant: ['tabular-nums'] },
  divider: { height: 1, backgroundColor: 'rgba(7,94,87,.18)', marginVertical: 5 },
});
