/** API V1 -> ADAPT screen adapter. Backend remains the authority for changes. */
import type { Activity as ServerActivity, Trip, TripDay } from '@/features/plan/api';
import type { CurrentTrip, Proposal, ProposalResponse } from './model';

type RawChange = {
  activity_id: string;
  change_type: 'EXTEND_REST' | 'DROP' | 'REPLACE_LOCATION' | 'RESCHEDULE' | 'ADD';
  before: ServerActivity | null;
  after: ServerActivity | null;
};
type RawOption = {
  option_id: string;
  changes: RawChange[];
  proposed_days: TripDay[];
  reason: string;
  tradeoff: string;
  estimated_end_time: string;
};
type RawProposal = {
  proposal_id: string;
  itinerary_id: string;
  type: 'EXTEND_REST' | 'REPLACE_LOCATION';
  base_version: number;
  options: RawOption[];
  no_option_reason: string | null;
};
export type LiveTrip = CurrentTrip & { rawDays: TripDay[]; restActivityId?: string; placeNames: Record<string, string> };

export function fromItinerary(itinerary: Trip, selectedDay?: number): LiveTrip {
  const rawDays = itinerary.days ?? itinerary.itinerary_days ?? [];
  if (!rawDays.length) throw new Error('API current không trả đủ các ngày của lịch.');
  const day = rawDays.find(d => d.day_number === selectedDay)
    ?? rawDays.find(d => d.activities.some(a => a.type === 'REST' && a.status === 'PENDING'))
    ?? rawDays[0];
  const rest = day.activities.find(a => a.type === 'REST' && a.status === 'PENDING')
    ?? day.activities.find(a => a.type === 'REST');
  const placeNames: Record<string, string> = {};
  for (const d of rawDays) for (const a of d.activities) {
    if (a.type === 'VISIT' && a.place_id) placeNames[a.place_id] = a.name;
  }
  return {
    id: itinerary.itinerary_id, version: itinerary.version, day: day.day_number,
    restStart: rest?.start_time ?? '—', restEnd: rest?.end_time ?? '—',
    restPlaceId: rest?.place_id ?? undefined,
    restActivityId: rest?.status === 'PENDING' ? rest.activity_id : undefined,
    deadline: day.end_deadline ?? '—',
    activities: day.activities.filter(a => a.type === 'VISIT').map(a => ({
      id: a.activity_id, title: a.name, time: `${a.start_time}–${a.end_time}`,
      status: a.status === 'PENDING' ? 'TODO' as const : a.status,
      // The API Activity doesn't include environment. The server verifies RAIN eligibility.
      outdoor: false,
    })),
    travelLegs: [], rawDays, placeNames,
  };
}

export function liveDays(trip: CurrentTrip): number[] {
  return isLiveTrip(trip) ? trip.rawDays.map(d => d.day_number) : [trip.day];
}
export function isLiveTrip(trip: CurrentTrip): trip is LiveTrip {
  return 'rawDays' in trip && Array.isArray(trip.rawDays);
}
export function liveActivities(trip: CurrentTrip): ServerActivity[] {
  if (!isLiveTrip(trip)) return [];
  return trip.rawDays.find(d => d.day_number === trip.day)?.activities ?? [];
}
function describe(activity: ServerActivity | null): string {
  return activity ? `${activity.name} · ${activity.start_time}–${activity.end_time}` : 'Không có';
}
function describeChange(change: RawChange): string {
  const map = {
    EXTEND_REST: 'Kéo dài nghỉ', DROP: 'Bỏ hoạt động', REPLACE_LOCATION: 'Đổi địa điểm',
    RESCHEDULE: 'Đổi giờ', ADD: 'Thêm hoạt động',
  };
  return `${map[change.change_type] ?? change.change_type}: ${describe(change.before)} → ${describe(change.after)}`;
}
export function mapProposalResponse(value: unknown): ProposalResponse {
  const raw = value as RawProposal;
  if (!raw || typeof raw.proposal_id !== 'string' || !Array.isArray(raw.options)
    || raw.options.length > 2 || !Number.isInteger(raw.base_version)) {
    throw new Error('Phản hồi F05 sai cấu trúc (proposal_id, options hoặc base_version).');
  }
  const proposals: Proposal[] = raw.options.map((option, i) => {
    if (typeof option.option_id !== 'string' || !Array.isArray(option.changes)
      || !Array.isArray(option.proposed_days)) {
      throw new Error('Phản hồi F05 thiếu option_id, changes hoặc proposed_days.');
    }
    const restChange = option.changes.find(c => c.change_type === 'EXTEND_REST');
    const drop = option.changes.find(c => c.change_type === 'DROP');
    const replacement = option.changes.find(c => c.change_type === 'REPLACE_LOCATION');
    return {
      id: option.option_id, baseVersion: raw.base_version,
      kind: raw.type === 'EXTEND_REST' ? 'rest' : 'rain',
      title: `Phương án ${i === 0 ? 'A' : 'B'}`,
      summary: option.changes.map(describeChange).join('\n'),
      explanation: option.reason || 'Theo phương án backend trả về.',
      tradeoff: option.tradeoff || 'Xem chi tiết thay đổi ở dưới.',
      finish: option.estimated_end_time,
      removeId: drop?.before?.activity_id,
      replaceId: replacement?.before?.activity_id,
      replacement: replacement?.after?.name,
      restUntil: restChange?.after?.end_time,
      apiChanges: option.changes.map(describeChange),
      // Real TRAVEL Activity has no from/to pair: avoid inventing mock leg records.
      travelChanges: [],
    };
  });
  return {
    proposals, conflict: raw.no_option_reason ?? undefined,
    source: 'API', proposalId: raw.proposal_id,
  };
}
