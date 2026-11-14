import { router } from 'expo-router';
import { Text, View } from 'react-native';
import { useAdapt } from '@/features/adapt/context';
import { activeTravelLegs, isActive, restPlaceName, travelRouteName } from '@/features/adapt/model';
import { Action, Page, PlacePhoto, Header, styles } from '@/features/adapt/ui';import { liveActivities, liveDays } from '@/features/adapt/adapter';
export default function CurrentScreen() {
  const { trip, setKind, reset, isMock, ready, available, busy, error, load } = useAdapt();
  if (!ready || (!available && busy)) return <Page><Header/><Text style={styles.title}>Đang tải lịch hiện hành…</Text></Page>;
  if (!available) return <Page><Header/><Text style={styles.title}>Chưa có lịch hiện hành</Text><Text style={styles.text}>{error || 'Vui lòng tạo và xác nhận lịch trước khi điều chỉnh.'}</Text><Action title='Thử tải lại' onPress={() => void load()}/><Action title='Xem S03' secondary onPress={() => router.replace('/current')}/></Page>;
  return <Page><Header/><Text style={styles.title}>Lịch hiện hành · Ngày {trip.day}</Text>{!isMock && <View style={styles.row}>{liveDays(trip).map(day => <View key={day} style={{flex:1}}><Action title={'Ngày '+day} secondary={day !== trip.day} disabled={busy} onPress={() => void load(day)}/></View>)}</View>}<View style={styles.card}><Text style={styles.text}>Nghỉ tại {restPlaceName(trip)}: {trip.restStart}–{trip.restEnd}</Text><Text style={styles.text}>Mốc kết thúc ngày: {trip.deadline}</Text>{trip.activities.filter(a => isActive(a.status)).sort((a, b) => a.time.localeCompare(b.time)).map(a => <View key={a.id} style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}><View style={{ flex: 1 }}><Text style={styles.text}>{a.time} · {a.title}</Text><Text style={styles.muted}>{a.status === 'DONE' ? 'Đã hoàn thành' : a.status === 'SKIPPED' ? 'Đã bỏ' : a.status === 'REPLACED' ? 'Đã thay thế' : 'Chưa thực hiện'}</Text></View>{a.outdoor && <View style={{ width: 92 }}><PlacePhoto place={a.title} height={64}/></View>}</View>)}{!isMock && liveActivities(trip).filter(a => a.type === 'TRAVEL' && (a.status === 'PENDING' || a.status === 'DONE')).sort((a,b) => a.start_time.localeCompare(b.start_time)).map(a => <Text key={a.activity_id} style={styles.text}>{a.start_time}–{a.end_time} · {a.name} · {a.status}</Text>)}{isMock && activeTravelLegs(trip).map(l => <Text key={l.activity_id} style={styles.text}>{travelRouteName(trip, l.from_place_id, l.to_place_id)} · {l.start_time}–{l.end_time} · {l.status}</Text>)}</View>{!isMock && <Action title="Tải lại lịch từ backend" secondary disabled={busy} onPress={() => void load()}/>}<Action title="Nghỉ thêm" onPress={() => { setKind('rest'); router.push('/adapt/request'); }}/><Action title="Đổi địa điểm vì mưa" onPress={() => { setKind('rain'); router.push('/adapt/request'); }}/>{isMock && (
  <Action
    title="Khôi phục lịch ban đầu"
    secondary
    onPress={reset}
  />
)}</Page>;
}
