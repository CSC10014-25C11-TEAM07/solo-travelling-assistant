import { GlassPanel, glassInset } from '@/components/glass/panel';
import { useEffect, useState } from 'react';
import { router } from 'expo-router';
import { Text, View, Image, Pressable, StyleSheet } from 'react-native';
import { Action, Field, Page, styles, palette } from '@/features/plan/ui';
import { usePlan } from '@/features/plan/state';
import { sourcedDemo, recommendations, createDraft, logout, Place } from '@/features/plan/api';
import { LOCAL_PLACES } from '@/features/plan/places';

const opts = [
  ['nature', 'Thiên nhiên', 'Rừng thông · Hồ · Trekking nhẹ'],
  ['coffee', 'Cà phê', 'Quán view đẹp · Săn mây'],
  ['culture', 'Văn hóa', 'Kiến trúc · Lịch sử · Nghệ thuật'],
  ['food', 'Ẩm thực', 'Đặc sản · Chợ đêm · Quán địa phương'],
];
const sourcedDetails: Record<string, string> = { nature: 'Đi dạo ven Hồ Xuân Hương', coffee: 'Still Cafe · An Cafe', culture: 'Ga Đà Lạt · Bảo tàng · Dinh III', food: 'Nhà hàng Tâm Châu · An Cafe' };
const extras = ['Vườn hoa', 'Chụp ảnh', 'Bình minh', 'Ngắm hoàng hôn', 'Thư giãn', 'Nông trại', 'Tiệm bánh', 'Thác nước', 'Hồ & chèo thuyền', 'Vườn thực vật'];
function dateToDisplay(iso: string) { const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso); return m ? `${m[3]}-${m[2]}-${m[1]}` : iso; }
function dateToISO(value: string) { const m = /^(\d{2})-(\d{2})-(\d{4})$/.exec(value); if (!m) return null; const d = Number(m[1]), mo = Number(m[2]), y = Number(m[3]); const date = new Date(Date.UTC(y, mo - 1, d)); return date.getUTCFullYear() === y && date.getUTCMonth() === mo - 1 && date.getUTCDate() === d ? `${m[3]}-${m[2]}-${m[1]}` : null; }
function Choice({ label, active, onPress, detail, compact = false }: { label: string; active: boolean; onPress: () => void; detail?: string; compact?: boolean }) {
  return <Pressable accessibilityRole="checkbox" accessibilityState={{ checked: active }} onPress={onPress}
    style={({ pressed }) => [local.choice, compact && local.compact, active && local.selected, { opacity: pressed ? .75 : 1 }]}>
    <Text style={[local.choiceLabel, active && { color: palette.foam }]}>{active ? '✓  ' : ''}{label}</Text>
    {detail ? <Text style={[local.choiceDetail, active && { color: palette.mist }]}>{detail}</Text> : null}
  </Pressable>;
}
export default function Plan() {
  const { form, setForm, setTrip, setDraftId, clearSession } = usePlan();
  const [err, E] = useState('');
  const [busy, B] = useState(false);
  const [extra, SE] = useState<string[]>([]);
  const [departureDisplay, SD] = useState(dateToDisplay(form.departure_date));
  const [returnDisplay, SR] = useState(dateToDisplay(form.return_date));
  const interestKey = form.interests.join(',');
  const [suggestions, setSuggestions] = useState<{ key: string; places: Place[]; error?: string }>();
  const loading = !!interestKey && suggestions?.key !== interestKey;
  const places = interestKey && suggestions?.key === interestKey ? suggestions.places : [];
  function change<K extends keyof typeof form>(key: K, value: (typeof form)[K]) { setForm({ ...form, [key]: value }); }
  function changeDates(dep: string, ret: string) { setForm({ ...form, departure_date: dep, return_date: ret }); }
  useEffect(() => {
    if (!interestKey) return;
    let active = true;
    recommendations(interestKey.split(',')).then(places => {
      if (active) setSuggestions({ key: interestKey, places: places.slice(0, 3) });
    }).catch(error => {
      if (active) setSuggestions({ key: interestKey, places: [], error: error instanceof Error ? error.message : 'Lỗi gợi ý' });
    });
    return () => { active = false; };
  }, [interestKey]);
  async function submit() {
    E('');
    const dep = dateToISO(departureDisplay), ret = dateToISO(returnDisplay);
    if (!dep || !ret) return E('Ngày không hợp lệ. Vui lòng nhập theo ngày-tháng-năm (DD-MM-YYYY).');
    changeDates(dep, ret);
    const a = Date.parse(dep), b = Date.parse(ret);
    if (!Number.isFinite(a) || !Number.isFinite(b) || b < a) return E('Ngày về phải bằng hoặc sau ngày đi.');
    const today = new Date();
    const localToday = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
    if (a < localToday) return E('Ngày đi không được trước ngày hôm nay.');
    const n = Math.round((b - a) / 86400000) + 1;
    if (n !== 3 && n !== 4) return E('Vui lòng chọn chuyến đi kéo dài 3 hoặc 4 ngày.');
    if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(form.departure_time)) return E('Giờ xuất phát phải theo HH:mm.');
    if (!form.interests.length) return E('Hãy chọn ít nhất một sở thích.');
    if (!Number.isSafeInteger(Number(form.min_rest_minutes)) || Number(form.min_rest_minutes) <= 0) return E('Thời gian nghỉ phải lớn hơn 0 phút.');
    B(true);
    try {
      const input = { ...form, departure_date: dep, return_date: ret };
      const result = await createDraft(input);
      setDraftId(result.draft_id);
      setTrip(result.itinerary);
      router.push('/draft');
    } catch (e) { console.error('S01: Loi tao lich', e); E(e instanceof Error ? e.message : 'Không tạo được lịch nháp'); }
    finally { B(false); }
  }
  async function signOut() { B(true); E(''); try { await logout(); await clearSession(); router.replace('/login'); } catch (e) { E(e instanceof Error ? e.message : 'Đăng xuất thất bại. Vui lòng thử lại.'); } finally { B(false); } }
  return <Page>
    <View style={{ alignSelf: 'flex-end' }}><Action title={busy ? 'Vui lòng đợi…' : 'Đăng xuất'} secondary disabled={busy} onPress={signOut}/></View>
    <GlassPanel style={local.hero}>
      <Text style={local.routeTitle}>Đà Lạt,{'\n'}theo cách của bạn.</Text>
      <Text style={styles.text}>Hành trình xe máy một mình, tập trung vào điểm đến và ẩm thực.</Text>
      <View style={local.route}><Text style={local.routeText}>TP. Hồ Chí Minh</Text><Text style={local.routeLine}>↔</Text><Text style={local.routeText}>Đà Lạt</Text></View>
    </GlassPanel>

    <GlassPanel>
      <Text style={styles.heading}>Thời gian chuyến đi</Text>
      <Text style={styles.muted}>Lịch trình 3–4 ngày · Nhập ngày theo DD-MM-YYYY</Text>
      <View style={styles.row}>
        <View style={local.field}><Field label="Ngày đi" value={departureDisplay} onChangeText={SD} placeholder="DD-MM-YYYY"/></View>
        <View style={local.field}><Field label="Ngày về" value={returnDisplay} onChangeText={SR} placeholder="DD-MM-YYYY"/></View>
      </View>
      <Text style={local.label}>Giờ xuất phát</Text>
      <View style={styles.row}>{['05:00', '06:00', '07:00', '08:00', '09:00', '10:00'].map(v => <Choice key={v} compact label={v} active={form.departure_time === v} onPress={() => change('departure_time', v)}/>)}</View>
      <Field label="Hoặc nhập giờ khác" value={form.departure_time} onChangeText={v => change('departure_time', v)} placeholder="HH:mm"/>
    </GlassPanel>

    <GlassPanel>
      <Text style={styles.heading}>Sở thích của bạn</Text><Text style={styles.muted}>Có thể chọn nhiều sở thích.</Text>
      <View style={styles.row}>{opts.map(([id, label, detail]) => <Choice key={id} label={label} detail={sourcedDemo ? sourcedDetails[id] : detail} active={form.interests.includes(id)} onPress={() => change('interests', form.interests.includes(id) ? form.interests.filter(x => x !== id) : [...form.interests, id])}/>)}</View>
      {!sourcedDemo && <>
        <Text style={local.label}>Trải nghiệm yêu thích</Text>
        <View style={styles.row}>{extras.map(x => <Choice key={x} compact label={x} active={extra.includes(x)} onPress={() => SE(extra.includes(x) ? extra.filter(v => v !== x) : [...extra, x])}/>)}</View>
        <Text style={styles.muted}>{form.interests.length} sở thích · {extra.length} trải nghiệm</Text>
      </>}
    </GlassPanel>

    <GlassPanel>
      <Text style={styles.heading}>Thời gian nghỉ tối thiểu</Text>
      <View style={styles.row}>{['30', '60', '90', '120'].map(v => <Choice key={v} compact label={v + ' phút'} active={form.min_rest_minutes === v} onPress={() => change('min_rest_minutes', v)}/>)}</View>
      <Field label="Nhập số phút nghỉ" value={form.min_rest_minutes} onChangeText={v => change('min_rest_minutes', v)}/>
    </GlassPanel>

    <GlassPanel>
      <Text style={styles.heading}>Điểm xuất phát</Text>
      <View style={local.departure}>
        <View style={local.routeDot}/><View style={{ flex: 1, gap: 7 }}>
          <Text style={local.label}>{sourcedDemo ? 'Công trường Công xã Paris, trước Bưu điện TP.HCM' : 'TP. Hồ Chí Minh'}</Text>
          <Text style={styles.muted}>Một mình · Xe máy · Khứ hồi</Text>
          {sourcedDemo && <Text style={styles.muted}>Mỗi chiều có điểm nghỉ tại La Ngà, Bảo Lộc và Đức Trọng. Tại Đà Lạt, mỗi ngày bắt đầu và kết thúc trên đường Huỳnh Thúc Kháng gần Crazy House. Bạn tự đặt chỗ nghỉ. Thời gian xe máy là ước tính từ bản đồ.</Text>}
        </View>
      </View>
    </GlassPanel>

    {!sourcedDemo && <GlassPanel>
      <Text style={styles.heading}>Khám phá Đà Lạt</Text><Text style={styles.muted}>Khám phá các địa điểm tham quan, cà phê và ăn uống.</Text>
      {LOCAL_PLACES.filter(p => form.interests.includes(p.category)).slice(0, 6).map(p => <View key={p.id} style={local.placeRow}><Text style={local.label}>{p.name}</Text><Text style={styles.muted}>{p.area} · {p.description}</Text></View>)}
      <Text style={styles.muted}>Giờ mở cửa có thể thay đổi.</Text>
    </GlassPanel>}

    <GlassPanel>
      <Text style={styles.heading}>Dành cho bạn</Text><Text style={styles.muted}>Tối đa 3 địa điểm hợp sở thích.</Text>
      {loading ? <Text style={styles.muted}>Đang tải gợi ý…</Text> : null}
      {places.slice(0, 3).map(p => <View key={p.place_id} style={local.recommendation}>
        {p.image_url ? <Image source={{ uri: p.image_url }} accessibilityLabel={`Ảnh ${p.name}`} resizeMode="cover" style={local.photo}/> : null}
        <View style={{ padding: 15, gap: 7 }}><Text style={styles.heading}>{p.name}</Text><Text style={styles.text}>{p.reason}</Text></View>
      </View>)}
      {suggestions?.key === interestKey && suggestions.error && <Text style={styles.error}>{suggestions.error}</Text>}
      {!loading && places.length === 0 && !suggestions?.error ? <Text style={styles.muted}>Chưa có gợi ý phù hợp.</Text> : null}
    </GlassPanel>
    {!!err && <Text style={styles.error}>{err}</Text>}
    <Action title={busy ? 'Đang tạo lịch…' : '✦ Tạo hành trình của tôi'} disabled={busy} onPress={submit}/>
    <Action title="Xem lịch đã lưu" secondary onPress={() => router.push('/current')}/>
  </Page>;
}

const local = StyleSheet.create({
  hero: { paddingVertical: 26, gap: 17 },
  routeTitle: { color: palette.ink, fontSize: 38, lineHeight: 44, letterSpacing: -1.3, fontWeight: '800' },
  route: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 10, paddingTop: 15, borderTopWidth: 1, borderColor: 'rgba(7,94,87,.18)' },
  routeText: { color: palette.ink, fontSize: 14, fontWeight: '700' },
  routeLine: { color: palette.pine, fontSize: 21 },
  field: { flex: 1, minWidth: 132 },
  label: { color: palette.ink, fontWeight: '700', fontSize: 16, lineHeight: 23 },
  choice: { ...glassInset, flexGrow: 1, flexBasis: 135, minWidth: 125, borderRadius: 16, padding: 13, gap: 5, minHeight: 48, justifyContent: 'center' },
  compact: { flexGrow: 0, flexBasis: 'auto', minWidth: 76, paddingHorizontal: 12, paddingVertical: 10, borderRadius: 13 },
  selected: { backgroundColor: palette.pine, borderColor: palette.pine },
  choiceLabel: { color: palette.ink, fontSize: 14, lineHeight: 20, fontWeight: '700', fontVariant: ['tabular-nums'] },
  choiceDetail: { color: palette.slate, fontSize: 12, lineHeight: 18 },
  departure: { flexDirection: 'row', gap: 13, paddingVertical: 5 },
  routeDot: { width: 12, height: 12, marginTop: 5, borderRadius: 6, backgroundColor: palette.pine, borderWidth: 3, borderColor: palette.mist },
  placeRow: { gap: 4, paddingVertical: 12, borderTopWidth: 1, borderColor: 'rgba(7,94,87,.14)' },
  recommendation: { ...glassInset, overflow: 'hidden', borderRadius: 19 },
  photo: { width: '100%', height: 210 },
});
