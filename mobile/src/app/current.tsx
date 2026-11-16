
import { useCallback, useState } from 'react';
import { router, useFocusEffect } from 'expo-router';
import { Text, View } from 'react-native';

import { Action, Page, styles } from '@/features/plan/ui';
import { usePlan, tripDays } from '@/features/plan/state';
import { latestTrip, markDone } from '@/features/plan/api';

export default function Current() {
  const { trip, setTrip, ready } = usePlan();

  const [day, setDay] = useState(1);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    setBusy('reload');
    setLoading(true);
    setError('');

    try {
      const latest = await latestTrip();
      setTrip(latest);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : 'Không đọc được lịch đã lưu.'
      );
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
    } catch (e) {
      if ((e as { status?: number }).status === 409) {
        setError(
          'Lịch đã thay đổi. Đang tải phiên bản mới.'
        );
        await reload();
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
            </Text><Action
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

          <View style={styles.card}>

            {[...(
              days.find(d => d.day_number === day)
                ?.activities || []
            )]
              .filter(a =>
                a.status === 'PENDING' ||
                a.status === 'DONE'
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
                      : a.status === 'DROPPED'
                      ? 'Đã bỏ'
                      : a.status === 'REPLACED'
                      ? 'Đã thay thế'
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

          <View style={styles.card}>
            <Text style={styles.heading}>
              Lịch sử điều chỉnh
            </Text>

            {(days.find(d => d.day_number === day)
              ?.activities || [])
              .filter(a =>
                a.status === 'DROPPED' ||
                a.status === 'REPLACED'
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
                  <Text style={styles.muted}>
                    {a.start_time}–{a.end_time} · {a.name}
                  </Text>

                  <Text style={styles.muted}>
                    {a.status === 'DROPPED'
                      ? 'Đã bỏ'
                      : 'Đã thay thế'}
                  </Text>
                </View>
              ))}
          </View>

        </>
      )}

      {!!error && (
        <Text style={styles.error}>
          {error}
        </Text>
      )}
    </Page>
  );
}
