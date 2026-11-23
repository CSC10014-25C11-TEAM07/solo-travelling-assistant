import type {TripDay} from './api';

export type ArrivalEstimate = {dayNumber: number; date: string; time: string};

export function arrivalEstimates(days: TripDay[]): ArrivalEstimate[] | null {
  if (!days.length) return null;
  const estimates: ArrivalEstimate[] = [];
  for (const day of days) {
    const activities = day.activities.filter(a => a.status === 'PENDING' || a.status === 'DONE');
    if (!activities.length) return null;
    let time = '';
    for (const activity of activities) {
      if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(activity.start_time)
        || !/^([01]\d|2[0-3]):[0-5]\d$/.test(activity.end_time)
        || activity.end_time <= activity.start_time) return null;
      if (activity.end_time > time) time = activity.end_time;
    }
    estimates.push({dayNumber: day.day_number, date: day.date, time});
  }
  return estimates;
}
