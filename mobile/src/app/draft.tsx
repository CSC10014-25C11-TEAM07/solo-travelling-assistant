import { useState } from 'react';
import { router } from 'expo-router';
import { Text, TextInput, View } from 'react-native';

import {
  DayPicker, ScheduleActivity, ScheduleButton, ScheduleCover, ScheduleHeader, SchedulePage,
  Timeline, displayDate, scheduleStyles as s,
} from '@/features/plan/itinerary-ui';
import { styles } from '@/features/plan/ui';
import { usePlan, tripDays } from '@/features/plan/state';
import { configured, confirmDraft, sourcedDemo, type Activity } from '@/features/plan/api';

type TimeField = 'start_time' | 'end_time';

export default function Draft() {
  const { trip, setTrip, draftId, setDraftId } = usePlan();
  const [day, setDay] = useState(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [showRoute, setShowRoute] = useState(false);

  if (!trip) {
    return (
      <SchedulePage>
        <ScheduleHeader/>
        <ScheduleCover title="Chưa có lịch nháp"/>
        <ScheduleButton title="Nhập nhu cầu" variant="primary" onPress={() => router.replace('/plan')}/>
      </SchedulePage>
    );
  }

  const days = tripDays(trip);
  const selected = days.find(d => d.day_number === day) ?? days[0];
  const activities = [...(selected?.activities ?? [])].sort((a, b) => a.start_time.localeCompare(b.start_time));

  function changeTime(activityId: string, field: TimeField, value: string) {
    if (configured || !trip) return;
    setTrip({
      ...trip,
      itinerary_days: days.map(d => ({
        ...d,
        activities: d.activities.map(a => a.activity_id === activityId ? { ...a, [field]: value } : a),
      })),
    });
  }

  function adjustTime(activity: Activity, field: TimeField, delta: number) {
    const value = activity[field];
    if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(value)) return;
    const [hour, minute] = value.split(':').map(Number);
    const total = Math.max(0, Math.min(1439, hour * 60 + minute + delta));
    const newTime = [Math.floor(total / 60), total % 60].map(part => String(part).padStart(2, '0')).join(':');
    changeTime(activity.activity_id, field, newTime);
  }

  async function confirm() {
    if (!trip || busy) return;
    if (!draftId) {
      setError('Không tìm thấy mã lịch nháp. Vui lòng tạo lại lịch.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      setTrip(await confirmDraft(draftId));
      setDraftId(null);
      router.replace('/current');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Không xác nhận được lịch.');
    } finally {
      setBusy(false);
    }
  }

  function editRequest() {
    if (router.canGoBack()) router.back();
    else router.replace('/plan');
  }

  return (
    <SchedulePage footer={
      <>
        {!!error && <Text accessibilityRole="alert" style={s.error}>{error}</Text>}
        <ScheduleButton title={busy ? 'Đang lưu…' : 'Xác nhận và lưu lịch'} variant="primary" disabled={busy} onPress={confirm}/>
        <ScheduleButton title="Sửa yêu cầu" variant="text" onPress={editRequest} disabled={busy}/>
      </>
    }>
      <ScheduleHeader/>
      <ScheduleCover title="Lịch nháp" subtitle={[displayDate(trip.departure_date) + ' – ' + displayDate(trip.return_date), days.length + ' ngày'].join(' · ')}/>
      {sourcedDemo && (
        <View style={s.panel}>
          <Text style={s.note}>Thời gian đi xe là ước tính. Chặng TP.HCM ⇄ La Ngà có hạn chế theo giờ trên bản đồ.</Text>
          <ScheduleButton title={showRoute ? 'Ẩn thông tin tuyến' : 'Xem điểm đi và điểm nghỉ'} variant="text"
            selected={showRoute} onPress={() => setShowRoute(!showRoute)}/>
          {showRoute && <Text style={s.note}>Khứ hồi từ Công trường Công xã Paris, nghỉ ở La Ngà, Bảo Lộc và Đức Trọng. Mốc qua đêm ở đường Huỳnh Thúc Kháng gần Crazy House. Kiểm tra tình trạng đường và chỗ nghỉ trước chuyến đi.</Text>}
        </View>
      )}
      {selected && (
        <>
          <DayPicker days={days} selected={selected.day_number} onSelect={setDay}/>
          <View style={s.section}>
            <Text accessibilityRole="header" style={s.panelTitle}>Ngày {selected.day_number} · {displayDate(selected.date)}</Text>
            {activities.length ? (
              <Timeline>
                {activities.map(a => (
                  <ScheduleActivity key={a.activity_id} activity={{
                    name: a.name, start_time: a.start_time, end_time: a.end_time, type: a.type,
                  }}>
                    {!configured && (['start_time', 'end_time'] as const).map(field => {
                      const label = field === 'start_time' ? 'Giờ bắt đầu' : 'Giờ kết thúc';
                      return (
                        <View key={field} style={s.section}>
                          <Text style={s.note}>{label}</Text>
                          <View style={styles.row}>
                            <ScheduleButton title="−" label={label + ': giảm 15 phút'} onPress={() => adjustTime(a, field, -15)}/>
                            <TextInput accessibilityLabel={label} value={a[field]}
                              onChangeText={value => changeTime(a.activity_id, field, value)}
                              style={[styles.input, { flex: 1, minWidth: 64, textAlign: 'center' }]}/>
                            <ScheduleButton title="+" label={label + ': tăng 15 phút'} onPress={() => adjustTime(a, field, 15)}/>
                          </View>
                        </View>
                      );
                    })}
                  </ScheduleActivity>
                ))}
              </Timeline>
            ) : <Text style={s.note}>Ngày này chưa có hoạt động.</Text>}
          </View>
        </>
      )}
    </SchedulePage>
  );
}
