import { router } from 'expo-router';
import { Text, View } from 'react-native';
import { useAdapt } from '@/features/adapt/context';
import { Action, ChangePanel, Header, MockLabel, OptionPanels, Page, SectionTitle, PlacePhoto, palette, styles } from '@/features/adapt/ui';
export default function CompareScreen() {
  const { trip, response, request, busy, error, choose, reject, isMock } = useAdapt();
  if (!response || !request) return <Page><Header/><Text style={styles.title}>Chưa có đề xuất</Text><Action title="Nhập yêu cầu" onPress={() => router.replace('/adapt/request')}/></Page>;
  const rest = request.kind === 'rest';
  return <Page>
    <Header/>
    <SectionTitle title="So sánh phương án" subtitle="Chọn cách điều chỉnh phù hợp nhất với bạn."/>
    <View style={{ backgroundColor: palette.cream, alignSelf: 'flex-start', borderRadius: 24, paddingHorizontal: 15, paddingVertical: 9 }}><Text style={{ color: palette.green, fontWeight: '800' }}>◇  {response.proposals.length} phương án hợp lệ · {rest ? 'Nghỉ thêm' : 'Đổi địa điểm'}</Text></View>
    {response.conflict && <View style={styles.card}><Text style={styles.heading}>Chưa tìm được phương án</Text><Text style={styles.text}>{response.conflict}</Text><Text style={styles.muted}>Lịch hiện tại chưa thay đổi. Bạn có thể sửa yêu cầu.</Text></View>}
    <OptionPanels>{response.proposals.map((proposal, index) => {
      const kept = rest ? trip.activities.find(a => a.status === 'TODO' && a.id !== proposal.removeId) : undefined;
      const dropped = trip.activities.find(a => a.id === (rest ? proposal.removeId : proposal.replaceId));
      const name = rest ? `Giữ ${kept?.title ?? 'hoạt động'}` : `Đổi sang ${proposal.replacement ?? 'điểm trong nhà'}`;
      return <View key={proposal.id} style={[styles.card, { flex: 1, minWidth: 0, padding: 15, gap: 11 }]}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}><View style={{ width: 40, height: 40, borderRadius: 24, backgroundColor: palette.green, alignItems: 'center', justifyContent: 'center' }}><Text style={{ color: '#fff', fontWeight: '900', fontSize: 24 }}>{index === 0 ? 'A' : 'B'}</Text></View><Text style={[styles.heading, { fontSize: 18, flex: 1 }]}>{name}</Text></View>
        <View style={{ flexDirection: 'row', gap: 11, alignItems: 'flex-start' }}>
          <View style={{ width: '41%', gap: 7 }}><PlacePhoto place={rest ? (kept?.title ?? '') : (dropped?.title ?? '')} height={142}/><Text style={{ color: palette.gray, fontSize: 11, textAlign: 'center' }}></Text></View>
          <View style={{ flex: 1, gap: 8 }}>
            <View style={{ backgroundColor: '#e7f2d1', padding: 10, borderRadius: 13, gap: 3 }}><Text style={{ color: palette.green, fontWeight: '900', fontSize: 13 }}>⇄  Thay đổi</Text><Text style={{ color: palette.green, fontSize: 12 }}>{rest ? `${trip.restEnd} → ${proposal.restUntil}` : `${dropped?.title} → ${proposal.replacement}`}</Text><Text style={{ color: palette.gray, fontSize: 11 }}>{rest ? `Bỏ: ${dropped?.title}` : 'Địa điểm trong nhà'}</Text></View>
            <Text style={{ color: palette.green, fontSize: 12 }}>♧  <Text style={{ fontWeight: '800' }}>Lý do:</Text> {proposal.explanation}</Text>
            <Text style={{ color: palette.green, fontSize: 12 }}>⚖  <Text style={{ fontWeight: '800' }}>Đánh đổi:</Text> {proposal.tradeoff}</Text>
            <Text style={{ color: palette.green, fontSize: 12 }}>⚑  <Text style={{ fontWeight: '800' }}>Kết thúc dự kiến:</Text> {proposal.finish}</Text>
          </View>
        </View>
        <Action title={busy ? 'Đang áp dụng…' : 'Áp dụng phương án này'} disabled={busy} onPress={async () => { if (await choose(proposal)) router.replace('/adapt/result'); }}/>
      </View>;
    })}</OptionPanels>
    <View style={[styles.card, { padding: 13 }]}><Text style={[styles.heading, { fontSize: 15 }]}>Giữ nguyên ở cả hai phương án</Text><Text style={styles.muted}>Các hoạt động đã hoàn thành, những ngày khác và các hoạt động không bị điều chỉnh.</Text></View>
    {error && <Text style={styles.error}>{error}</Text>}
    <View style={{ flexDirection: 'row', gap: 8 }}><View style={{ flex: 1 }}><Action icon="✎" title="Sửa yêu cầu" secondary disabled={busy} onPress={() => router.replace('/adapt/request')}/></View><View style={{ flex: 1.2 }}><Action icon="▣" title="Giữ lịch hiện tại" secondary disabled={busy} onPress={() => { reject(); router.replace('/adapt/result'); }}/></View></View>
    
  </Page>;
}
