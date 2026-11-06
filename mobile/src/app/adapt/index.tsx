import { router } from 'expo-router';
import { Text, View } from 'react-native';
import { useAdapt } from '@/features/adapt/context';
import { Action, MockLabel, Page, PlacePhoto, Header, styles } from '@/features/adapt/ui';
export default function CurrentScreen() {
  const { trip, setKind, reset, isMock } = useAdapt();
  return <Page><Header/><Text style={styles.title}>Lịch hiện hành · Ngày {trip.day}</Text><View style={styles.card}><Text style={styles.text}>Nghỉ: {trip.restStart}–{trip.restEnd}</Text><Text style={styles.text}>Mốc kết thúc ngày: {trip.deadline}</Text>{trip.activities.map(a => <View key={a.id} style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}><View style={{ flex: 1 }}><Text style={styles.text}>{a.time} · {a.title}</Text><Text style={styles.muted}>{a.status === 'DONE' ? 'Đã hoàn thành' : a.status === 'SKIPPED' ? 'Đã bỏ' : a.status === 'REPLACED' ? 'Đã thay thế' : 'Chưa thực hiện'}</Text></View>{a.outdoor && <View style={{ width: 92 }}><PlacePhoto place={a.title} height={64}/></View>}</View>)}</View><Action title="Nghỉ thêm" onPress={() => { setKind('rest'); router.push('/adapt/request'); }}/><Action title="Đổi địa điểm vì mưa" onPress={() => { setKind('rain'); router.push('/adapt/request'); }}/><Action title="Khôi phục lịch ban đầu" secondary onPress={reset}/></Page>;
}
