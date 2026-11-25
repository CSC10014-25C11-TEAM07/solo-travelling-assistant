import { GlassPanel, glassInset } from '@/components/glass/panel';
import { router } from 'expo-router';
import { Text, View, StyleSheet } from 'react-native';
import { useAdapt } from '@/features/adapt/context';
import { activeTravelLegs, isActive, restPlaceName, travelRouteName } from '@/features/adapt/model';
import { liveActivities } from '@/features/adapt/adapter';
import { Action, Header, Page, TimelineLine, styles, palette } from '@/features/adapt/ui';

export default function ResultScreen() {
  const { trip, result, isMock, reset, load, busy, error } = useAdapt();
  if (!result) return <Page><Header/><GlassPanel>
    <Text style={styles.title}>Chưa có kết quả</Text>
    <Action title="Về lịch hiện hành" onPress={() => router.replace('/adapt')}/>
  </GlassPanel></Page>;
  const activeActivities = trip.activities.filter(activity => isActive(activity.status)).sort((a, b) => a.time.localeCompare(b.time));
  const currentTravelActivities = !isMock ? liveActivities(trip).filter(activity => activity.type === 'TRAVEL' && (activity.status === 'PENDING' || activity.status === 'DONE')).sort((a, b) => a.start_time.localeCompare(b.start_time)) : [];
  const currentTravelLegs = isMock ? activeTravelLegs(trip) : [];
  const appliedOptionName = result.applied ? result.message.includes('Giữ Vườn hoa') ? 'Giữ Vườn hoa Đà Lạt' : result.message.includes('Giữ Hồ Xuân Hương') ? 'Giữ Hồ Xuân Hương' : `Phương án ${result.choice}` : 'Giữ lịch hiện tại';
  const handleViewCurrent = async () => {
    if (isMock) { router.replace('/adapt'); return; }
    if (await load()) router.replace('/current');
  };
  const handleReset = () => { reset(); router.replace('/adapt'); };
  return <Page>
    <Header/>
    <GlassPanel style={local.intro}>
      <View style={local.confirmation}><Text style={local.confirmationSymbol}>{result.applied ? '✓' : '≡'}</Text></View>
      <Text style={local.title}>{result.applied ? 'Lịch đã cập nhật!' : 'Lịch được giữ nguyên'}</Text>
      <Text style={styles.text}>{result.applied ? `Đã áp dụng phương án ${result.choice} và điều chỉnh lịch trình cho bạn.` : 'Bạn đã chọn giữ lịch hiện tại. Không có thay đổi nào được áp dụng.'}</Text>
    </GlassPanel>

    <GlassPanel>
      <View style={local.appliedOption}>
        <Text style={local.optionLabel}>{result.applied ? 'Phương án đã áp dụng' : 'Không áp dụng phương án'}</Text>
        <Text style={local.optionTitle}>{appliedOptionName}</Text>
      </View>
      <View style={{ gap: 7, paddingVertical: 5 }}>
        <Text style={local.sectionHeading}>{result.applied ? 'Thay đổi chính' : 'Lịch không thay đổi'}</Text>
        <Text style={styles.text}>{result.message}</Text>
      </View>
    </GlassPanel>

    <GlassPanel>
      <Text style={styles.heading}>Lịch hiện hành · Ngày {trip.day}</Text>
      <TimelineLine time={`${trip.restStart}–${trip.restEnd}`} title={`Nghỉ tại ${restPlaceName(trip)}`} status="Nghỉ" symbol="◷"/>
      {activeActivities.map(activity => <TimelineLine key={activity.id} time={activity.time} title={activity.title}
        status={activity.status === 'DONE' ? 'Đã hoàn thành' : activity.status === 'SKIPPED' ? 'Đã bỏ' : activity.status === 'REPLACED' ? 'Đã thay thế' : 'Chưa thực hiện'}
        symbol={activity.status === 'SKIPPED' ? '×' : activity.status === 'TODO' ? '○' : '✓'}/>)}
    </GlassPanel>

    <GlassPanel>
      <Text style={styles.heading}>Tuyến di chuyển hiện hành</Text>
      {!isMock && currentTravelActivities.map(activity => <TimelineLine key={activity.activity_id} time={`${activity.start_time}–${activity.end_time}`} title={activity.name} status={activity.status === 'DONE' ? 'Đã hoàn thành' : 'Chưa thực hiện'} symbol="↗"/>)}
      {isMock && currentTravelLegs.map(leg => <TimelineLine key={leg.activity_id} time={`${leg.start_time}–${leg.end_time}`} title={travelRouteName(trip, leg.from_place_id, leg.to_place_id)} status={leg.status === 'DONE' ? 'Đã hoàn thành' : 'Chưa thực hiện'} symbol="↗"/>)}
      <Text style={styles.muted}>Những chặng di chuyển đã được thay thế vẫn được lưu trong lịch sử nhưng không hiển thị trong lịch hiện hành.</Text>
      <Text style={styles.muted}>Những ngày khác và các hoạt động đã hoàn thành được giữ nguyên.</Text>
    </GlassPanel>
    {error && <Text style={styles.error}>{error}</Text>}
    <Action title={busy ? 'Đang tải lịch…' : 'Xem lịch hiện hành'} disabled={busy} onPress={handleViewCurrent}/>
    {isMock && <Action title="Khôi phục lịch ban đầu" secondary onPress={handleReset}/>}
  </Page>;
}
const local = StyleSheet.create({
  intro: { gap: 16, paddingVertical: 24 },
  confirmation: { width: 48, height: 48, borderRadius: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.pine },
  confirmationSymbol: { color: palette.foam, fontSize: 29, fontWeight: '700' },
  title: { color: palette.ink, fontSize: 34, lineHeight: 41, letterSpacing: -1, fontWeight: '800' },
  appliedOption: { ...glassInset, borderRadius: 16, padding: 16, gap: 7 },
  optionLabel: { color: palette.slate, fontSize: 13, lineHeight: 19 },
  optionTitle: { color: palette.pine, fontSize: 23, lineHeight: 30, fontWeight: '700', letterSpacing: -.3 },
  sectionHeading: { color: palette.ink, fontSize: 17, lineHeight: 24, fontWeight: '700' },
});
