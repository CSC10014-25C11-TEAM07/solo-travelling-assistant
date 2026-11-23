import assert from 'node:assert/strict';
import {test} from 'node:test';
import {arrivalEstimates} from '../src/features/plan/arrival-review.ts';

const activity = (start, end, status = 'PENDING') => ({
  activity_id: `${start}-${end}`, type: 'TRAVEL', name: 'Chặng thử',
  start_time: start, end_time: end, status,
});
const day = activities => ({day_number: 1, date: '2026-11-24', activities});

test('shows the latest active arrival even when activities are unsorted', () => {
  assert.deepEqual(arrivalEstimates([day([
    activity('18:15', '19:38'), activity('07:00', '10:11'),
    activity('21:00', '23:00', 'REPLACED'), activity('22:00', '23:30', 'DROPPED'),
  ])]), [{dayNumber: 1, date: '2026-11-24', time: '19:38'}]);
});

test('shows a separate arrival for every day without changing the itinerary', () => {
  const days = [day([activity('19:15', '20:38')]),
    {...day([activity('17:00', '18:42')]), day_number: 2, date: '2026-11-25'}];
  const before = structuredClone(days);
  assert.deepEqual(arrivalEstimates(days), [
    {dayNumber: 1, date: '2026-11-24', time: '20:38'},
    {dayNumber: 2, date: '2026-11-25', time: '18:42'},
  ]);
  assert.deepEqual(days, before);
});

test('does not offer arrival approval when a day has no usable schedule', () => {
  for (const days of [[], [day([])], [day([activity('20:00', '25:00')])],
    [day([activity('23:00', '01:00')])], [day([activity('07:00', '08:00', 'REPLACED')])]]) {
    assert.equal(arrivalEstimates(days), null);
  }
});
