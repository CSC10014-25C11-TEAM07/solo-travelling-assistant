
import { router } from 'expo-router';
import { Text, View } from 'react-native';

import { useAdapt } from '@/features/adapt/context';
import {
  previewTravelChanges,
  travelRouteName,
} from '@/features/adapt/model';
import {
  Action,
  Header,
  OptionPanels,
  Page,
  SectionTitle,
  PlacePhoto,
  palette,
  styles,
} from '@/features/adapt/ui';

export default function CompareScreen() {
  const {
    trip,
    response,
    request,
    busy,
    error,
    choose,
    reject,
    isMock,
  } = useAdapt();

  if (!response || !request) {
    return (
      <Page>
        <Header />
        <Text style={styles.title}>Chưa có đề xuất</Text>
        <Action
          title="Nhập yêu cầu"
          onPress={() => router.replace('/adapt/request')}
        />
      </Page>
    );
  }

  const rest = request.kind === 'rest';
  const live = !isMock;

  return (
    <Page>
      <Header />

      <SectionTitle
        title="So sánh phương án"
        subtitle="Chọn cách điều chỉnh phù hợp nhất với bạn."
      />

      <View
        style={{
          backgroundColor: palette.cream,
          alignSelf: 'flex-start',
          borderRadius: 24,
          paddingHorizontal: 15,
          paddingVertical: 9,
        }}
      >
        <Text
          style={{
            color: palette.green,
            fontWeight: '800',
          }}
        >
          ◇ {response.proposals.length} phương án hợp lệ ·{' '}
          {rest ? 'Nghỉ thêm' : 'Đổi địa điểm'}
        </Text>
      </View>

      {response.conflict && (
        <View style={styles.card}>
          <Text style={styles.heading}>
            Chưa tìm được phương án
          </Text>

          <Text style={styles.text}>
            {response.conflict}
          </Text>

          <Text style={styles.muted}>
            Lịch hiện tại chưa thay đổi. Bạn có thể sửa yêu cầu.
          </Text>
        </View>
      )}

      <OptionPanels>
        {response.proposals.map((proposal, index) => {
          const kept = rest
            ? trip.activities.find(
                (a) =>
                  a.status === 'TODO' &&
                  a.id !== proposal.removeId
              )
            : undefined;

          const dropped = trip.activities.find(
            (a) =>
              a.id ===
              (rest ? proposal.removeId : proposal.replaceId)
          );

          const name = live
            ? proposal.title
            : rest
              ? `Giữ ${kept?.title ?? 'hoạt động'}`
              : `Đổi sang ${
                  proposal.replacement ?? 'địa điểm trong nhà'
                }`;

          const travelChanges = previewTravelChanges(
            trip,
            proposal
          );

          return (
            <View
              key={proposal.id}
              style={[
                styles.card,
                {
                  flex: 1,
                  minWidth: 0,
                  padding: 15,
                  gap: 11,
                },
              ]}
            >
              {/* Tên phương án */}
              <View
                style={{
                  flexDirection: 'row',
                  alignItems: 'center',
                  gap: 10,
                }}
              >
                <View
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 24,
                    backgroundColor: palette.green,
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Text
                    style={{
                      color: '#fff',
                      fontWeight: '900',
                      fontSize: 24,
                    }}
                  >
                    {index === 0 ? 'A' : 'B'}
                  </Text>
                </View>

                <Text
                  style={[
                    styles.heading,
                    {
                      fontSize: 18,
                      flex: 1,
                    },
                  ]}
                >
                  {name}
                </Text>
              </View>

              {/* Hình ảnh và thông tin thay đổi */}
              <View
                style={{
                  flexDirection: 'row',
                  gap: 11,
                  alignItems: 'flex-start',
                }}
              >
                <View
                  style={{
                    width: '41%',
                    gap: 7,
                  }}
                >
                  <PlacePhoto
                    place={
                      rest
                        ? kept?.title ?? ''
                        : dropped?.title ?? ''
                    }
                    height={142}
                  />
                </View>

                <View
                  style={{
                    flex: 1,
                    gap: 8,
                  }}
                >
                  <View
                    style={{
                      backgroundColor: '#e7f2d1',
                      padding: 10,
                      borderRadius: 13,
                      gap: 3,
                    }}
                  >
                    <Text
                      style={{
                        color: palette.green,
                        fontWeight: '900',
                        fontSize: 13,
                      }}
                    >
                      ⇄ Thay đổi
                    </Text>

                    <Text
                      style={{
                        color: palette.green,
                        fontSize: 12,
                      }}
                    >
                      {live
                        ? proposal.summary
                        : rest
                          ? `${trip.restEnd} → ${proposal.restUntil}`
                          : `${dropped?.title} → ${proposal.replacement}`}
                    </Text>

                    <Text
                      style={{
                        color: palette.gray,
                        fontSize: 11,
                      }}
                    >
                      {live
                        ? 'Chi tiết điều chỉnh lịch trình'
                        : rest
                          ? `Bỏ: ${dropped?.title}`
                          : 'Địa điểm trong nhà'}
                    </Text>
                  </View>

                  <Text
                    style={{
                      color: palette.green,
                      fontSize: 12,
                    }}
                  >
                    ♧{' '}
                    <Text style={{ fontWeight: '800' }}>
                      Lý do:
                    </Text>{' '}
                    {proposal.explanation}
                  </Text>

                  <Text
                    style={{
                      color: palette.green,
                      fontSize: 12,
                    }}
                  >
                    ⚖{' '}
                    <Text style={{ fontWeight: '800' }}>
                      Đánh đổi:
                    </Text>{' '}
                    {proposal.tradeoff}
                  </Text>

                  <Text
                    style={{
                      color: palette.green,
                      fontSize: 12,
                    }}
                  >
                    ⚑{' '}
                    <Text style={{ fontWeight: '800' }}>
                      Kết thúc dự kiến:
                    </Text>{' '}
                    {proposal.finish}
                  </Text>
                </View>
              </View>

              {/* Các thay đổi do API trả về */}
              {live &&
                !!proposal.apiChanges?.length && (
                  <View style={{ gap: 6 }}>
                    {proposal.apiChanges.map((change, i) => (
                      <Text key={i} style={styles.muted}>
                        {change}
                      </Text>
                    ))}
                  </View>
                )}

              {/* Tuyến di chuyển trước và sau */}
              <View
                style={{
                  backgroundColor: '#edf4e4',
                  padding: 10,
                  borderRadius: 12,
                  gap: 4,
                }}
              >
                <Text
                  style={{
                    color: palette.green,
                    fontWeight: '900',
                  }}
                >
                  Tuyến di chuyển trước / sau
                </Text>

                {travelChanges.length === 0 ? (
                  <Text style={styles.muted}>
                    {live
                      ? 'Thông tin di chuyển được thể hiện trong danh sách thay đổi và lịch xem trước.'
                      : 'Chưa có thông tin thay đổi tuyến di chuyển cho phương án này.'}
                  </Text>
                ) : (
                  travelChanges.map((change, i) => {
                    const leg =
                      change.after ?? change.before;

                    const route = leg
                      ? travelRouteName(
                          trip,
                          leg.from_place_id,
                          leg.to_place_id
                        )
                      : 'Chưa có dữ liệu chặng';

                    const time =
                      change.action === 'RESCHEDULE'
                        ? `${change.before?.start_time}–${change.before?.end_time} → ${change.after?.start_time}–${change.after?.end_time}`
                        : `${leg?.start_time}–${leg?.end_time}`;

                    const label =
                      change.action === 'REPLACE'
                        ? 'Trước'
                        : change.action === 'CREATE'
                          ? 'Sau'
                          : 'Đổi giờ';

                    return (
                      <Text key={i} style={styles.muted}>
                        {label}: {route} · {time}
                      </Text>
                    );
                  })
                )}
              </View>

              {/* Áp dụng phương án */}
              <Action
                title={
                  busy
                    ? 'Đang áp dụng…'
                    : 'Áp dụng phương án này'
                }
                disabled={busy}
                onPress={async () => {
                  if (await choose(proposal)) {
                    router.replace('/adapt/result');
                  }
                }}
              />
            </View>
          );
        })}
      </OptionPanels>

      {/* Những hoạt động không thay đổi */}
      <View
        style={[
          styles.card,
          {
            padding: 13,
          },
        ]}
      >
        <Text
          style={[
            styles.heading,
            {
              fontSize: 15,
            },
          ]}
        >
          Giữ nguyên ở cả hai phương án
        </Text>

        <Text style={styles.muted}>
          Các hoạt động đã hoàn thành, những ngày khác và các
          hoạt động không bị điều chỉnh.
        </Text>
      </View>

      {/* Thông báo lỗi */}
      {error && (
        <Text style={styles.error}>{error}</Text>
      )}

      {/* Nút điều hướng */}
      <View
        style={{
          flexDirection: 'row',
          gap: 8,
        }}
      >
        <View style={{ flex: 1 }}>
          <Action
            icon="✎"
            title="Sửa yêu cầu"
            secondary
            disabled={busy}
            onPress={() =>
              router.replace('/adapt/request')
            }
          />
        </View>

        <View style={{ flex: 1.2 }}>
          <Action
            icon="▣"
            title="Giữ lịch hiện tại"
            secondary
            disabled={busy}
            onPress={async () => {
              if (await reject()) {
                router.replace('/adapt/result');
              }
            }}
          />
        </View>
      </View>
    </Page>
  );
}
