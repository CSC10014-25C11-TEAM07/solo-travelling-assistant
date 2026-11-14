
import { router } from 'expo-router';
import { Text, View } from 'react-native';

import { useAdapt } from '@/features/adapt/context';
import {
  activeTravelLegs,
  isActive,
  restPlaceName,
  travelRouteName,
} from '@/features/adapt/model';
import { liveActivities } from '@/features/adapt/adapter';
import {
  Action,
  Header,
  Page,
  TimelineLine,
  styles,
  palette,
} from '@/features/adapt/ui';

export default function ResultScreen() {
  const {
    trip,
    result,
    isMock,
    reset,
    load,
    busy,
    error,
  } = useAdapt();

  if (!result) {
    return (
      <Page>
        <Header />
        <Text style={styles.title}>Chưa có kết quả</Text>
        <Action
          title="Về lịch hiện hành"
          onPress={() => router.replace('/adapt')}
        />
      </Page>
    );
  }

  const activeActivities = trip.activities
    .filter((activity) => isActive(activity.status))
    .sort((a, b) => a.time.localeCompare(b.time));

  const currentTravelActivities = !isMock
    ? liveActivities(trip)
        .filter(
          (activity) =>
            activity.type === 'TRAVEL' &&
            (activity.status === 'PENDING' ||
              activity.status === 'DONE')
        )
        .sort((a, b) =>
          a.start_time.localeCompare(b.start_time)
        )
    : [];

  const currentTravelLegs = isMock
    ? activeTravelLegs(trip)
    : [];

  const appliedOptionName = result.applied
    ? result.message.includes('Giữ Vườn hoa')
      ? 'Giữ Vườn hoa Đà Lạt'
      : result.message.includes('Giữ Hồ Xuân Hương')
        ? 'Giữ Hồ Xuân Hương'
        : `Phương án ${result.choice}`
    : 'Giữ lịch hiện tại';

  const handleViewCurrent = async () => {
    if (isMock) {
      router.replace('/adapt');
      return;
    }

    if (await load()) {
      router.replace('/current');
    }
  };

  const handleReset = () => {
    reset();
    router.replace('/adapt');
  };

  return (
    <Page>
      <Header />

      {/* Thông báo kết quả */}
      <View
        style={{
          alignItems: 'center',
          gap: 10,
          marginVertical: 18,
        }}
      >
        <View
          style={{
            backgroundColor: '#ddf69c',
            width: 96,
            height: 96,
            borderRadius: 55,
            justifyContent: 'center',
            alignItems: 'center',
          }}
        >
          <Text
            style={{
              color: palette.green,
              fontSize: 58,
              fontWeight: '900',
            }}
          >
            {result.applied ? '✓' : '≡'}
          </Text>
        </View>

        <Text
          style={[
            styles.title,
            {
              textAlign: 'center',
              fontSize: 30,
            },
          ]}
        >
          {result.applied
            ? 'Lịch đã cập nhật!'
            : 'Lịch được giữ nguyên'}
        </Text>

        <Text
          style={[
            styles.subtitle,
            {
              textAlign: 'center',
            },
          ]}
        >
          {result.applied
            ? `Đã áp dụng phương án ${result.choice} và điều chỉnh lịch trình cho bạn.`
            : 'Bạn đã chọn giữ lịch hiện tại. Không có thay đổi nào được áp dụng.'}
        </Text>
      </View>

      {/* Thẻ kết quả */}
      <View
        style={[
          styles.card,
          {
            padding: 16,
            gap: 13,
          },
        ]}
      >
        {/* Phương án đã chọn */}
        <View
          style={{
            backgroundColor: palette.green,
            borderRadius: 17,
            padding: 16,
            flexDirection: 'row',
            gap: 12,
            alignItems: 'center',
          }}
        >
          <View
            style={{
              width: 46,
              height: 46,
              borderRadius: 30,
              backgroundColor: '#e1f6a0',
              justifyContent: 'center',
              alignItems: 'center',
            }}
          >
            <Text
              style={{
                color: palette.green,
                fontSize: 24,
                fontWeight: '900',
              }}
            >
              {result.applied ? result.choice : '✓'}
            </Text>
          </View>

          <View style={{ flex: 1 }}>
            <Text
              style={{
                color: '#fff',
                fontSize: 13,
              }}
            >
              {result.applied
                ? 'Phương án đã áp dụng'
                : 'Không áp dụng phương án'}
            </Text>

            <Text
              style={{
                color: '#fff',
                fontSize: 17,
                fontWeight: '900',
              }}
            >
              {appliedOptionName}
            </Text>
          </View>
        </View>

        {/* Thay đổi chính */}
        <View
          style={{
            backgroundColor: '#e7f2d1',
            borderRadius: 17,
            padding: 14,
            gap: 5,
          }}
        >
          <Text
            style={[
              styles.heading,
              {
                fontSize: 16,
              },
            ]}
          >
            ⇄{' '}
            {result.applied
              ? 'Thay đổi chính'
              : 'Lịch không thay đổi'}
          </Text>

          <Text style={styles.text}>
            {result.message}
          </Text>
        </View>

        {/* Lịch hiện hành sau khi xử lý */}
        <Text
          style={[
            styles.heading,
            {
              fontSize: 17,
            },
          ]}
        >
          ▣ Lịch hiện hành · Ngày {trip.day}
        </Text>

        {/* Thời gian nghỉ */}
        <TimelineLine
          time={`${trip.restStart}–${trip.restEnd}`}
          title={`Nghỉ tại ${restPlaceName(trip)}`}
          status="Nghỉ"
          symbol="▣"
        />

        {/* Các hoạt động hiện hành */}
        {activeActivities.map((activity) => (
          <TimelineLine
            key={activity.id}
            time={activity.time}
            title={activity.title}
            status={
              activity.status === 'DONE'
                ? 'Đã hoàn thành'
                : activity.status === 'SKIPPED'
                  ? 'Đã bỏ'
                  : activity.status === 'REPLACED'
                    ? 'Đã thay thế'
                    : 'Chưa thực hiện'
            }
            symbol={
              activity.status === 'SKIPPED'
                ? '×'
                : activity.status === 'TODO'
                  ? '○'
                  : '✓'
            }
          />
        ))}

        {/* Tuyến di chuyển hiện hành */}
        <Text
          style={[
            styles.heading,
            {
              fontSize: 16,
            },
          ]}
        >
          Tuyến di chuyển hiện hành
        </Text>

        {/* Dữ liệu tuyến di chuyển từ API */}
        {!isMock &&
          currentTravelActivities.map((activity) => (
            <TimelineLine
              key={activity.activity_id}
              time={`${activity.start_time}–${activity.end_time}`}
              title={activity.name}
              status={
                activity.status === 'DONE'
                  ? 'Đã hoàn thành'
                  : 'Chưa thực hiện'
              }
              symbol="➜"
            />
          ))}

        {/* Dữ liệu tuyến di chuyển mô phỏng */}
        {isMock &&
          currentTravelLegs.map((leg) => (
            <TimelineLine
              key={leg.activity_id}
              time={`${leg.start_time}–${leg.end_time}`}
              title={travelRouteName(
                trip,
                leg.from_place_id,
                leg.to_place_id
              )}
              status={
                leg.status === 'DONE'
                  ? 'Đã hoàn thành'
                  : 'Chưa thực hiện'
              }
              symbol="➜"
            />
          ))}

        {/* Thông tin giữ nguyên */}
        <Text style={styles.muted}>
          Những chặng di chuyển đã được thay thế vẫn
          được lưu trong lịch sử nhưng không hiển thị
          trong lịch hiện hành.
        </Text>

        <Text style={styles.muted}>
          Những ngày khác và các hoạt động đã hoàn thành
          được giữ nguyên.
        </Text>
      </View>

      {/* Thông báo lỗi */}
      {error && (
        <Text style={styles.error}>
          {error}
        </Text>
      )}

      {/* Xem lịch hiện hành */}
      <Action
        icon="▣"
        title={
          busy
            ? 'Đang tải lịch…'
            : 'Xem lịch hiện hành'
        }
        disabled={busy}
        onPress={handleViewCurrent}
      />

      {/* Khôi phục dữ liệu demo */}
      {isMock && (
        <Action
          title="Khôi phục lịch ban đầu"
          secondary
          onPress={handleReset}
        />
      )}
    </Page>
  );
}
