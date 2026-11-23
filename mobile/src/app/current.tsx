import { useCallback, useState } from 'react';
import { router, useFocusEffect } from 'expo-router';
import { Text, View } from 'react-native';

import {
  DayPicker, ScheduleActivity, ScheduleButton, ScheduleCover, ScheduleHeader, SchedulePage,
  Timeline, displayDate, scheduleStyles as s,
} from '@/features/plan/itinerary-ui';
import { usePlan, tripDays } from '@/features/plan/state';
import { latestTrip, markDone, selectDemoTrip, sourcedDemo } from '@/features/plan/api';

export default function Current() {
  const { trip, setTrip, ready } = usePlan();
  const [day, setDay] = useState(1);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [showSample, setShowSample] = useState(false);

  const reload = useCallback(async (): Promise<boolean> => {
    setBusy('reload');
    setLoading(true);
    setError('');
    try {
      setTrip(await latestTrip());
      return true;
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Không đọc được lịch đã lưu.');
      return false;
    } finally {
      setBusy('');
      setLoading(false);
    }
  }, [setTrip]);

  useFocusEffect(useCallback(() => {
    if (ready) void reload();
  }, [ready, reload]));

  async function done(activityId: string) {
    if (!trip || busy) return;
    setBusy(activityId);
    setError('');
    try {
      setTrip(await markDone(trip.itinerary_id, activityId, trip.version));
    } catch (e) {
      if ((e as { status?: number }).status === 409) {
        if (await reload()) setError('Lịch đã thay đổi. Vui lòng kiểm tra phiên bản mới.');
      } else {
        setError(e instanceof Error ? e.message : 'Không thể cập nhật hoạt động.');
      }
    } finally {
      setBusy('');
    }
  }

  async function switchSample(close: boolean) {
    if (busy || loading) return;
    setBusy('sample');
    setError('');
    try {
      setTrip(await selectDemoTrip(trip, close));
      setDay(close ? 1 : 2);
      if (close) setShowSample(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Chưa đổi được lịch. Hãy tải lại.');
    } finally {
      setBusy('');
    }
  }

  const days = trip ? tripDays(trip) : [];
  const selected = days.find(d => d.day_number === day) ?? days[0];
  const activities = (selected?.activities ?? [])
    .filter(a => a.status === 'PENDING' || a.status === 'DONE')
    .sort((a, b) => a.start_time.localeCompare(b.start_time));
  const completed = activities.filter(a => a.status === 'DONE').length;

  return (
    <SchedulePage
      footer={trip && selected ? (
        <ScheduleButton title="Điều chỉnh lịch trình" variant="primary" disabled={!!busy}
          onPress={() => router.push({ pathname: '/adapt', params: { day: String(selected.day_number) } })}/>
      ) : undefined}
    >
      <ScheduleHeader action={<ScheduleButton title={loading ? 'Đang tải…' : 'Tải lại'} variant="text" onPress={reload} disabled={!ready || !!busy}/>}/>
      <ScheduleCover title={trip?.is_demo_sample ? 'Lịch mẫu' : 'Lịch chuyến đi'}
        subtitle={trip ? [displayDate(trip.departure_date) + ' – ' + displayDate(trip.return_date), days.length + ' ngày'].join(' · ') : 'TP.HCM ⇄ Đà Lạt'}/>
      {!!error && <Text accessibilityRole="alert" style={s.error}>{error}</Text>}
      {!ready || (loading && !trip) ? (
        <Text style={s.note}>Đang tải lịch…</Text>
      ) : !trip ? (
        <View style={s.panel}>
          <Text style={s.panelTitle}>{error ? 'Chưa thể tải lịch' : 'Bạn chưa có lịch đã lưu'}</Text>
          <ScheduleButton title="Lên kế hoạch chuyến đi" variant="primary" onPress={() => router.push('/plan')}/>
        </View>
      ) : selected ? (
        <>
          <DayPicker days={days} selected={selected.day_number} onSelect={setDay}/>
          <View style={s.section}>
            <Text accessibilityRole="header" style={s.panelTitle}>Ngày {selected.day_number} · {displayDate(selected.date)}</Text>
            <Text style={s.note}>
              {completed}/{activities.length} hoạt động đã xong
              {selected.end_deadline ? ' · Hạn kết thúc ' + selected.end_deadline : ''}
            </Text>
            {activities.length ? (
              <Timeline>
                {activities.map(a => <ScheduleActivity key={a.activity_id} activity={a}
                  completion={a.status === 'PENDING' ? {
                    onPress: () => void done(a.activity_id),
                    disabled: !!busy,
                    saving: busy === a.activity_id,
                  } : undefined}/>)}
              </Timeline>
            ) : <Text style={s.note}>Ngày này chưa có hoạt động.</Text>}
          </View>
        </>
      ) : <Text style={s.note}>Lịch chưa có ngày nào.</Text>}
      {sourcedDemo && ready && !loading && (
        <View style={s.panel}>
          {!trip?.is_demo_sample && (
            <ScheduleButton title={showSample ? 'Ẩn mục lịch mẫu' : 'Lịch mẫu để thử điều chỉnh'} variant="text"
              selected={showSample} onPress={() => setShowSample(open => !open)}/>
          )}
          {(showSample || trip?.is_demo_sample) && (
            <>
              <Text style={s.note}>Ở ngày 2, bạn có thể thử nghỉ đến 15:00 hoặc đổi Hồ Xuân Hương khi trời mưa.</Text>
              <ScheduleButton title={trip?.is_demo_sample ? 'Nạp lại lịch mẫu từ đầu' : 'Mở lịch mẫu riêng'}
                disabled={!!busy} onPress={() => void switchSample(false)}/>
              {trip?.is_demo_sample && <ScheduleButton title="Về lịch cá nhân" disabled={!!busy} onPress={() => void switchSample(true)}/>}
            </>
          )}
        </View>
      )}
    </SchedulePage>
  );
}
