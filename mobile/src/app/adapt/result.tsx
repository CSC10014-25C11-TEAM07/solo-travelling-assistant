import { router } from 'expo-router';
import { Text, View } from 'react-native';
import { useAdapt } from '@/features/adapt/context';
import { activeTravelLegs, isActive, restPlaceName, travelRouteName } from '@/features/adapt/model';
import { Action, Header, MockLabel, Page, TimelineLine, styles, palette } from '@/features/adapt/ui';
export default function ResultScreen() {
  const { trip, result, isMock, reset } = useAdapt();
  if (!result) return <Page><Header/><Text style={styles.title}>Chưa có kết quả</Text><Action title="Về lịch hiện hành" onPress={() => router.replace('/adapt')}/></Page>;
  return <Page>
    <Header/>
    <View style={{ alignItems: 'center', gap: 10, marginVertical: 18 }}>
      <View style={{ backgroundColor: '#ddf69c', width: 96, height: 96, borderRadius: 55, justifyContent: 'center', alignItems: 'center' }}><Text style={{ color: palette.green, fontSize: 58, fontWeight: '900' }}>{result.applied ? '✓' : '≡'}</Text></View>
      <Text style={[styles.title, { textAlign: 'center', fontSize: 30 }]}>{result.applied ? 'Lịch đã cập nhật!' : 'Lịch được giữ nguyên'}</Text>
      <Text style={[styles.subtitle, { textAlign: 'center' }]}>{result.applied ? `Đã áp dụng phương án ${result.choice} và điều chỉnh lịch trình cho bạn.` : 'Bạn đã chọn giữ lịch hiện tại. Không có thay đổi nào được áp dụng.'}</Text>
    </View>
    <View style={[styles.card, { padding: 16, gap: 13 }]}>
      <View style={{ backgroundColor: palette.green, borderRadius: 17, padding: 16, flexDirection: 'row', gap: 12, alignItems: 'center' }}><View style={{ width: 46, height: 46, borderRadius: 30, backgroundColor: '#e1f6a0', justifyContent: 'center', alignItems: 'center' }}><Text style={{ color: palette.green, fontSize: 24, fontWeight: '900' }}>{result.applied ? result.choice : '✓'}</Text></View><View style={{ flex: 1 }}><Text style={{ color: '#fff', fontSize: 13 }}> {result.applied ? 'Phương án đã áp dụng' : 'Không áp dụng phương án'}</Text><Text style={{ color: '#fff', fontSize: 17, fontWeight: '900' }}>{result.applied ? (result.message.includes('Giữ Vườn hoa') ? 'Giữ Vườn hoa Đà Lạt' : result.message.includes('Giữ Hồ Xuân Hương') ? 'Giữ Hồ Xuân Hương' : `Phương án ${result.choice}`) : 'Giữ lịch hiện tại'}</Text></View></View>
      <View style={{ backgroundColor: '#e7f2d1', borderRadius: 17, padding: 14, gap: 5 }}><Text style={[styles.heading, { fontSize: 16 }]}>⇄  {result.applied ? 'Thay đổi chính' : 'Lịch không thay đổi'}</Text><Text style={styles.text}>{result.message}</Text></View>
      <Text style={[styles.heading, { fontSize: 17 }]}>▣  Lịch hiện hành · Ngày {trip.day}</Text>
      <TimelineLine time={`${trip.restStart}–${trip.restEnd}`} title={`Nghỉ tại ${restPlaceName(trip)}`} status="Nghỉ" symbol="▣"/>
      {trip.activities.filter(a => isActive(a.status)).sort((a, b) => a.time.localeCompare(b.time)).map(a => <TimelineLine key={a.id} time={a.time} title={a.title} status={a.status === 'DONE' ? 'Đã hoàn thành' : a.status === 'SKIPPED' ? 'Đã bỏ' : a.status === 'REPLACED' ? 'Đã thay thế' : 'Chưa thực hiện'} symbol={a.status === 'SKIPPED' ? '×' : a.status === 'TODO' ? '○' : '✓'}/>)}
      <Text style={[styles.heading, { fontSize: 16 }]}>Tuyến di chuyển hiện hành · MOCK</Text>
      {activeTravelLegs(trip).map(l => <TimelineLine key={l.activity_id} time={`${l.start_time}–${l.end_time}`} title={travelRouteName(trip, l.from_place_id, l.to_place_id)} status={l.status} symbol="➜"/>)}
      <Text style={styles.muted}>Chặng REPLACED được giữ trong lịch sử nhưng không hiển thị trong lịch đang chạy.</Text>
      <Text style={styles.muted}>Những ngày khác và hoạt động đã hoàn thành được giữ nguyên.</Text>
    </View>
    <Action icon="▣" title="Xem lịch hiện hành" onPress={() => router.replace('/adapt')}/>
    
    {isMock && <Action title="Khôi phục lịch ban đầu" secondary onPress={() => { reset(); router.replace('/adapt'); }}/>} 
  </Page>;
}
