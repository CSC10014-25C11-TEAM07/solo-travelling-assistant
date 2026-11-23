import { router } from 'expo-router';
import { Text, View } from 'react-native';

import { useAdapt } from '@/features/adapt/context';
import { activeTravelLegs, isActive, restPlaceName, travelRouteName } from '@/features/adapt/model';
import { isLiveTrip, liveActivities } from '@/features/adapt/adapter';
import type { Activity } from '@/features/plan/api';
import {
  DayPicker, ScheduleActivity, ScheduleButton, ScheduleCover, ScheduleHeader, SchedulePage,
  Timeline, displayDate, scheduleStyles as s,
} from '@/features/plan/itinerary-ui';

export default function AdaptIndex() {
  const { trip, setKind, reset, isMock, ready, available, busy, error, load } = useAdapt();
  const live = isLiveTrip(trip);
  const selectedDay = live ? trip.rawDays.find(d => d.day_number === trip.day) : undefined;
  const mockVisits: Activity[] = trip.activities.filter(a => isActive(a.status)).map(a => {
    const [start_time, end_time] = a.time.split('–');
    return {
      activity_id: a.id, name: a.title, type: 'VISIT', start_time, end_time,
      status: a.status === 'DONE' ? 'DONE' : 'PENDING',
    };
  });
  const mockTravel = activeTravelLegs(trip).map(a => ({ ...a, name: travelRouteName(trip, a.from_place_id, a.to_place_id) }));
  const mockRest: Activity = {
    activity_id: 'mock-rest', name: restPlaceName(trip), type: 'REST',
    start_time: trip.restStart, end_time: trip.restEnd, status: 'PENDING',
  };
  const activities = (live ? liveActivities(trip) : [...mockVisits, ...mockTravel, mockRest])
    .filter(a => a.status === 'PENDING' || a.status === 'DONE')
    .sort((a, b) => a.start_time.localeCompare(b.start_time));

  return (
    <SchedulePage footer={ready && available ? (
      <>
        <ScheduleButton title="Nghỉ thêm" variant="primary" disabled={busy} onPress={() => { setKind('rest'); router.push('/adapt/request'); }}/>
        <ScheduleButton title="Đổi địa điểm vì mưa" disabled={busy} onPress={() => { setKind('rain'); router.push('/adapt/request'); }}/>
      </>
    ) : undefined}>
      <ScheduleHeader action={!isMock && ready ? (
        <ScheduleButton title="Tải lại" variant="text" disabled={busy} onPress={() => void load(trip.day)}/>
      ) : undefined}/>
      <ScheduleCover title="Điều chỉnh lịch" subtitle={available ? 'Ngày ' + trip.day + (selectedDay ? ' · ' + displayDate(selectedDay.date) : '') : undefined}/>
      {!ready || (!available && busy) ? (
        <Text style={s.note}>Đang tải lịch hiện hành…</Text>
      ) : !available ? (
        <View style={s.panel}>
          <Text style={s.panelTitle}>{error ? 'Chưa thể tải lịch' : 'Chưa có lịch hiện hành'}</Text>
          <Text style={s.note}>{error || 'Tạo và xác nhận lịch trước khi điều chỉnh.'}</Text>
          <ScheduleButton title="Về lịch chuyến đi" onPress={() => router.replace('/current')}/>
        </View>
      ) : (
        <>
          {live && <DayPicker days={trip.rawDays} selected={trip.day} disabled={busy} onSelect={day => void load(day)}/>}
          <View style={s.section}>
            <Text accessibilityRole="header" style={s.panelTitle}>Hoạt động trong ngày</Text>
            {trip.deadline !== '—' && <Text style={s.note}>Hạn kết thúc {trip.deadline}</Text>}
            {activities.length ? (
              <Timeline>{activities.map(a => <ScheduleActivity key={a.activity_id} activity={a}/>)}</Timeline>
            ) : <Text style={s.note}>Ngày này chưa có hoạt động.</Text>}
          </View>
          {isMock && <ScheduleButton title="Khôi phục lịch ban đầu" onPress={reset}/>}
        </>
      )}
    </SchedulePage>
  );
}
