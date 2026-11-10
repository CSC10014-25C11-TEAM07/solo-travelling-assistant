
import { useState } from 'react';
import { router } from 'expo-router';
import {
  Text,
  View,
  TextInput,
  Pressable,
} from 'react-native';

import { Action, Page, styles } from '@/features/plan/ui';
import { usePlan, tripDays } from '@/features/plan/state';
import { configured, confirmDraft } from '@/features/plan/api';

export default function Draft() {
  const { trip, setTrip } = usePlan();

  const [day, D] = useState(1);
  const [busy, B] = useState(false);
  const [err, E] = useState('');

  if (!trip) {
    return (
      <Page>
        <Text style={styles.title}>Chưa có lịch nháp</Text>
        <Action
          title="Nhập nhu cầu"
          onPress={() => router.replace('/plan')}
        />
      </Page>
    );
  }

  const days = tripDays(trip);

  function changeTime(
    activityId: string,
    field: 'start_time' | 'end_time',
    value: string
  ) {
    if (configured || !trip) return;

    setTrip({
      ...trip,
      itinerary_days: days.map(d => ({
        ...d,
        activities: d.activities.map(a =>
          a.activity_id === activityId
            ? { ...a, [field]: value }
            : a
        ),
      })),
    });
  }

  function adjustTime(
    activityId: string,
    field: 'start_time' | 'end_time',
    delta: number
  ) {
    if (configured) return;

    const a = days
      .flatMap(d => d.activities)
      .find(x => x.activity_id === activityId);

    if (!a) return;

    const value = a[field];

    if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(value)) {
      return;
    }

    const [h, m] = value.split(':').map(Number);

    const total = Math.max(
      0,
      Math.min(1439, h * 60 + m + delta)
    );

    const newTime =
      String(Math.floor(total / 60)).padStart(2, '0') +
      ':' +
      String(total % 60).padStart(2, '0');

    changeTime(activityId, field, newTime);
  }

  async function confirm() {
    if (!trip || busy) return;

    B(true);
    E('');

    try {
      const next = configured
        ? await confirmDraft(trip.itinerary_id)
        : { ...trip, status: 'CURRENT' as const };

      setTrip(next);
      router.replace('/current');
    } catch (e) {
      E(
        e instanceof Error
          ? e.message
          : 'Không lưu được lịch'
      );
    } finally {
      B(false);
    }
  }

  return (
    <Page>
      <Text style={styles.title}>
        Hành trình mới đang chờ đợi
      </Text>

      <Text style={styles.muted}>
        {trip.departure_date} → {trip.return_date}
        {' · '}{days.length} ngày · Lịch nháp
      </Text>

      <View style={styles.row}>
        {days.map(d => (
          <View key={d.day_id} style={{ flex: 1 }}>
            <Action
              title={'Ngày ' + d.day_number}
              secondary={day !== d.day_number}
              onPress={() => D(d.day_number)}
            />
          </View>
        ))}
      </View>

      <View style={styles.card}>
        <Text style={styles.muted}>
          Lịch trình được sắp xếp theo thời gian.
        </Text>

        {[
          ...(days.find(d => d.day_number === day)
            ?.activities || []),
        ]
          .sort((a, b) =>
            a.start_time.localeCompare(b.start_time)
          )
          .map(a => (
            <View
              key={a.activity_id}
              style={{
                paddingVertical: 9,
                borderBottomWidth: 1,
                borderColor: '#dce8d6',
              }}
            >
              <Text style={styles.heading}>
                {a.name}
              </Text>

              <View
                style={{
                  flexDirection: 'row',
                  flexWrap: 'wrap',
                  gap: 8,
                }}
              >
                {(
                  ['start_time', 'end_time'] as const
                ).map(field => (
                  <View
                    key={field}
                    style={{
                      flex: 1,
                      minWidth: 130,
                      gap: 5,
                    }}
                  >
                    <Text
                      style={{
                        color: '#294b3c',
                        fontWeight: '800',
                      }}
                    >
                      {field === 'start_time'
                        ? 'Bắt đầu'
                        : 'Kết thúc'}
                    </Text>

                    <View
                      style={{
                        flexDirection: 'row',
                        alignItems: 'center',
                        gap: 5,
                      }}
                    >
                      <Pressable
                        disabled={configured}
                        onPress={() =>
                          adjustTime(
                            a.activity_id,
                            field,
                            -15
                          )
                        }
                        style={{
                          padding: 9,
                          backgroundColor: '#e0efc8',
                          borderRadius: 9,
                        }}
                      >
                        <Text
                          style={{
                            fontWeight: '900',
                            color: '#174735',
                          }}
                        >
                          −
                        </Text>
                      </Pressable>

                      <TextInput
                        editable={!configured}
                        value={a[field]}
                        onChangeText={v =>
                          changeTime(
                            a.activity_id,
                            field,
                            v
                          )
                        }
                        style={{
                          flex: 1,
                          minWidth: 60,
                          textAlign: 'center',
                          fontWeight: '900',
                          fontSize: 15,
                          color: '#163e2f',
                          backgroundColor: '#fff',
                          borderWidth: 1,
                          borderColor: '#abc1a8',
                          borderRadius: 10,
                          padding: 7,
                        }}
                      />

                      <Pressable
                        disabled={configured}
                        onPress={() =>
                          adjustTime(
                            a.activity_id,
                            field,
                            15
                          )
                        }
                        style={{
                          padding: 9,
                          backgroundColor: '#e0efc8',
                          borderRadius: 9,
                        }}
                      >
                        <Text
                          style={{
                            fontWeight: '900',
                            color: '#174735',
                          }}
                        >
                          +
                        </Text>
                      </Pressable>
                    </View>
                  </View>
                ))}
              </View>

              <Text style={styles.muted}>
                {a.type === 'REST'
                  ? 'Nghỉ ngơi'
                  : a.type === 'TRAVEL'
                  ? 'Di chuyển bằng xe máy'
                  : 'Tham quan'}
                {' · '}
                {a.status}
              </Text>
            </View>
          ))}
      </View>

      {!!err && (
        <Text style={styles.error}>
          {err}
        </Text>
      )}

      <Action
        title={
          busy
            ? 'Đang lưu…'
            : 'Xác nhận và lưu lịch'
        }
        disabled={busy}
        onPress={confirm}
      />

      <Action
        title="Sửa yêu cầu"
        secondary
        onPress={() => router.back()}
      />
    </Page>
  );
}
