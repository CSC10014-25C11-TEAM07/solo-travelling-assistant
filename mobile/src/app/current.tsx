
import { useCallback, useState } from 'react';
import { router, useFocusEffect } from 'expo-router';
import { Text, View } from 'react-native';

import { Action, Page, styles } from '@/features/plan/ui';
import { usePlan, tripDays } from '@/features/plan/state';
import { latestTrip, markDone, selectDemoTrip, sourcedDemo } from '@/features/plan/api';

export default function Current() {
  const { trip, setTrip, ready } = usePlan();

  const [day, setDay] = useState(1);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

const reload = useCallback(async (): Promise<boolean> => {
  setBusy('reload');
  setLoading(true);
  setError('');

  try {
    const latest = await latestTrip();
    setTrip(latest);
    return true;
  } catch (e) {
    setError(
      e instanceof Error
        ? e.message
        : 'Không đọc được lịch đã lưu.'
    );
    return false;
  } finally {
    setBusy('');
    setLoading(false);
  }
}, [setTrip]);
  useFocusEffect(
    useCallback(() => {
      if (ready) {
        void reload();
      }
    }, [ready, reload])
  );

  async function done(activityId: string) {
    if (!trip || busy) return;

    setBusy(activityId);
    setError('');

    try {
      const updated = await markDone(
        trip.itinerary_id,
        activityId,
        trip.version
      );
      setTrip(updated);
    } catch (e) {if ((e as { status?: number }).status === 409) {
  const success = await reload();

  if (success) {
    setError(
      'Lịch đã thay đổi. Vui lòng kiểm tra phiên bản mới.'
    );
  }
} else {
        setError(
          e instanceof Error
            ? e.message
            : 'Không thể cập nhật hoạt động.'
        );
      }
    } finally {
      setBusy('');
    }
  }

  const days = trip ? tripDays(trip) : [];

  async function switchSample(close: boolean) {
    if (busy || loading) return;
    setBusy('sample');
    setError('');
    try {
      const selected = await selectDemoTrip(trip, close);
      setTrip(selected);
      setDay(close ? 1 : 2);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Chưa đổi được lịch. Hãy tải lại.');
    } finally {
      setBusy('');
    }
  }

  return (
    <Page>
      <Text style={styles.title}>
        Chạm vào những phút giây bình yên
      </Text>

      <Action
        title={loading ? 'Đang tải lịch…' : 'Tải lại lịch'}
        secondary
        disabled={!!busy}
        onPress={reload}
      />

      {!ready || (loading && !trip) ? (
        <Text style={styles.muted}>
          Đang tải lịch…
        </Text>
      ) : !trip ? (
  <View style={styles.card}>
    <Text style={styles.heading}>
      {error
        ? 'Chưa thể tải lịch'
        : 'Bạn chưa có lịch đã lưu'}
    </Text>

            <Action
      title="Lên kế hoạch chuyến đi"
      onPress={() => router.push('/plan')}
    />
  </View>
      ) : (
        <>
          <Text style={styles.muted}>
            Lịch hiện hành · Phiên bản {trip.version}
          </Text>

          <View style={styles.card}>
            <Text style={styles.heading}>
              Điều chỉnh hành trình
            </Text>

            <Text style={styles.muted}>
              Theo dõi các hoạt động và đánh dấu
              khi bạn hoàn thành.
            </Text>

            <Text style={styles.muted}>
  Mã lịch: {trip.itinerary_id}
</Text>
<Action
  title="Điều chỉnh lịch trình"
  onPress={() => router.push('/adapt')}
  />
</View>
          <View style={styles.row}>
            {days.map(d => (
              <View
                key={d.day_id}
                style={{ flex: 1 }}
              >
                <Action
                  title={'Ngày ' + d.day_number}
                  secondary={day !== d.day_number}
                  onPress={() => setDay(d.day_number)}
                />
              </View>
            ))}
          </View>

          <View style={styles.card}>{[...(
  days.find(d => d.day_number === day)
    ?.activities || []
)]
  .filter(
    a => a.status === 'PENDING' || a.status === 'DONE'
  )
  .sort((a, b) =>
    a.start_time.localeCompare(b.start_time)
  )
  .map(a => (

                <View
                  key={a.activity_id}
                  style={{
                    gap: 7,
                    paddingVertical: 10,
                    borderBottomWidth: 1,
                    borderColor: '#dce8d6',
                  }}
                >
                  <Text style={styles.heading}>
                    {a.start_time}–{a.end_time} · {a.name}
                  </Text>

                  <Text style={styles.muted}>
                    {a.type} ·{' '}
                   {a.status === 'DONE'
                   ? 'Đã hoàn thành'
                   : 'Chưa thực hiện'}
                  </Text>

                  {a.status === 'PENDING' && (
                    <Action
                      title={
                        busy === a.activity_id
                          ? 'Đang lưu…'
                          : 'Đánh dấu hoàn thành'
                      }
                      disabled={!!busy}
                      secondary
                      onPress={() =>
                        done(a.activity_id)
                      }
                    />
                  )}
                </View>
              ))}
          </View>
        </>
      )}

      {sourcedDemo && ready && !loading && <View style={styles.card}>
        <Text style={styles.heading}>Thử điều chỉnh lịch</Text>
        <Text style={styles.muted}>Mẫu 3 ngày dùng địa điểm thật. Ngày 2 đã đi ga, đang nghỉ ở Still Cafe. Bạn có thể thử nghỉ đến 15:00 hoặc đổi Hồ Xuân Hương khi trời mưa.</Text>
        <Action title={trip?.is_demo_sample ? 'Nạp lại lịch mẫu từ đầu' : 'Mở lịch mẫu riêng'} secondary disabled={!!busy} onPress={() => switchSample(false)}/>
        {trip?.is_demo_sample && <Action title="Đóng mẫu, trở về lịch cá nhân" secondary disabled={!!busy} onPress={() => switchSample(true)}/>}
      </View>}

      {!!error && (
        <Text style={styles.error}>
          {error}
        </Text>
      )}
    </Page>
  );
}
