import { GlassPanel, glassInset } from '@/components/glass/panel';
import { router } from 'expo-router';
import { Text, View, StyleSheet } from 'react-native';
import { useAdapt } from '@/features/adapt/context';
import { previewTravelChanges, travelRouteName } from '@/features/adapt/model';
import { Action, Header, OptionPanels, Page, PlacePhoto, palette, styles } from '@/features/adapt/ui';

export default function CompareScreen() {
  const { trip, response, request, busy, error, choose, reject, isMock } = useAdapt();
  if (!response || !request) return <Page><Header/><GlassPanel>
    <Text style={styles.title}>Chưa có đề xuất</Text>
    <Action title="Nhập yêu cầu" onPress={() => router.replace('/adapt/request')}/>
  </GlassPanel></Page>;
  const rest = request.kind === 'rest';
  const live = !isMock;
  return <Page>
    <Header/>
    <GlassPanel style={local.intro}>
      <Text style={local.title}>So sánh{'\n'}phương án</Text>
      <Text style={styles.text}>Chọn cách điều chỉnh phù hợp nhất với bạn.</Text>
      <Text style={local.optionCount}>{response.proposals.length} phương án hợp lệ · {rest ? 'Nghỉ thêm' : 'Đổi địa điểm'}</Text>
    </GlassPanel>
    {response.conflict && <GlassPanel>
      <Text style={styles.heading}>Chưa tìm được phương án</Text>
      <Text style={styles.text}>{response.conflict}</Text>
      <Text style={styles.muted}>Lịch hiện tại chưa thay đổi. Bạn có thể sửa yêu cầu.</Text>
    </GlassPanel>}

    <OptionPanels>{response.proposals.map((proposal, index) => {
      const kept = rest ? trip.activities.find(a => a.status === 'TODO' && a.id !== proposal.removeId) : undefined;
      const dropped = trip.activities.find(a => a.id === (rest ? proposal.removeId : proposal.replaceId));
      const name = live ? proposal.title : rest ? `Giữ ${kept?.title ?? 'hoạt động'}` : `Đổi sang ${proposal.replacement ?? 'địa điểm trong nhà'}`;
      const travelChanges = previewTravelChanges(trip, proposal);
      return <GlassPanel key={proposal.id} style={local.option}>
        <View style={local.optionHeader}>
          <View style={local.optionLetter}><Text style={local.letter}>{String.fromCharCode(65 + index)}</Text></View>
          <Text style={local.optionTitle}>{name}</Text>
        </View>
        {!live && <PlacePhoto place={rest ? kept?.title ?? '' : dropped?.title ?? ''} height={200}/>}
        <View style={local.change}>
          <Text style={local.sectionHeading}>Thay đổi</Text>
          <Text style={styles.text}>{live ? proposal.summary : rest ? `${trip.restEnd} → ${proposal.restUntil}` : `${dropped?.title} → ${proposal.replacement}`}</Text>
          <Text style={styles.muted}>{live ? 'Chi tiết điều chỉnh lịch trình' : rest ? `Bỏ: ${dropped?.title}` : 'Địa điểm trong nhà'}</Text>
        </View>
        <View style={local.reason}>
          <Text style={local.detailLabel}>Lý do</Text><Text style={styles.text}>{proposal.explanation}</Text>
        </View>
        <View style={local.reason}>
          <Text style={local.detailLabel}>Đánh đổi</Text><Text style={styles.text}>{proposal.tradeoff}</Text>
        </View>
        <View style={local.finish}>
          <Text style={styles.muted}>Kết thúc dự kiến</Text><Text style={local.finishTime}>{proposal.finish}</Text>
        </View>
        <View style={local.travel}>
          <Text style={local.sectionHeading}>Tuyến di chuyển trước / sau</Text>
          {live && proposal.apiTravelChanges?.length ? proposal.apiTravelChanges.map((change, i) => <Text key={i} style={styles.muted}>{change}</Text>) : travelChanges.length === 0 ? <Text style={styles.muted}>{live ? 'Không có thay đổi chặng di chuyển.' : 'Chưa có thông tin thay đổi tuyến di chuyển cho phương án này.'}</Text> : travelChanges.map((change, i) => {
            const leg = change.after ?? change.before;
            const route = leg ? travelRouteName(trip, leg.from_place_id, leg.to_place_id) : 'Chưa có dữ liệu chặng';
            const time = change.action === 'RESCHEDULE' ? `${change.before?.start_time}–${change.before?.end_time} → ${change.after?.start_time}–${change.after?.end_time}` : `${leg?.start_time}–${leg?.end_time}`;
            const label = change.action === 'REPLACE' ? 'Trước' : change.action === 'CREATE' ? 'Sau' : 'Đổi giờ';
            return <Text key={i} style={styles.muted}>{label}: {route} · {time}</Text>;
          })}
        </View>
        <Action title={busy ? 'Đang áp dụng…' : 'Áp dụng phương án này'} disabled={busy} onPress={async () => { if (await choose(proposal)) router.replace('/adapt/result'); }}/>
      </GlassPanel>;
    })}</OptionPanels>

    <GlassPanel>
      <Text style={local.sectionHeading}>Giữ nguyên trong các phương án</Text>
      <Text style={styles.muted}>Các hoạt động đã hoàn thành, những ngày khác và các hoạt động không bị điều chỉnh.</Text>
    </GlassPanel>
    {error && <Text style={styles.error}>{error}</Text>}
    <Action title="Sửa yêu cầu" secondary disabled={busy} onPress={() => router.replace('/adapt/request')}/>
    <Action title="Giữ lịch hiện tại" secondary disabled={busy} onPress={async () => { if (await reject()) router.replace('/adapt/result'); }}/>
  </Page>;
}
const local = StyleSheet.create({
  intro: { gap: 14, paddingVertical: 24 },
  title: { color: palette.ink, fontSize: 36, lineHeight: 42, letterSpacing: -1, fontWeight: '800' },
  optionCount: { color: palette.pine, fontSize: 14, lineHeight: 21, fontWeight: '700', paddingTop: 12, borderTopWidth: 1, borderColor: 'rgba(7,94,87,.16)' },
  option: { flex: 1, minWidth: 0, gap: 16, padding: 18 },
  optionHeader: { flexDirection: 'row', gap: 12, alignItems: 'center' },
  optionLetter: { width: 38, height: 38, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.pine },
  letter: { color: palette.foam, fontSize: 19, fontWeight: '700' },
  optionTitle: { flex: 1, color: palette.ink, fontSize: 23, fontWeight: '700', lineHeight: 30, letterSpacing: -.4 },
  sectionHeading: { color: palette.ink, fontSize: 16, lineHeight: 23, fontWeight: '700' },
  change: { ...glassInset, gap: 7, padding: 15, borderRadius: 16 },
  reason: { gap: 5 },
  detailLabel: { color: palette.pine, fontSize: 13, fontWeight: '700' },
  finish: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', gap: 10, alignItems: 'center', paddingTop: 12, borderTopWidth: 1, borderColor: 'rgba(7,94,87,.16)' },
  finishTime: { color: palette.pine, fontSize: 25, lineHeight: 32, fontWeight: '700', fontVariant: ['tabular-nums'] },
  travel: { gap: 9, paddingVertical: 13, borderTopWidth: 1, borderColor: 'rgba(7,94,87,.16)' },
});
