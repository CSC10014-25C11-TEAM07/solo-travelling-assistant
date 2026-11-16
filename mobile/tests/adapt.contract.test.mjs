/** Run: cd mobile && node --test tests/adapt.contract.test.mjs */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const ts = require('typescript');
const dir = path.resolve('src/features/adapt');
function loadFile(name) {
  const input = fs.readFileSync(path.join(dir, name), 'utf8');
  const output = ts.transpileModule(input, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
  const exports = {};
  const module = { exports };
  // These two model/adapter modules contain type-only imports, no runtime dependencies.
  new Function('module', 'exports', 'require', output)(module, exports, require);
  return module.exports;
}
const adapter = loadFile('adapter.ts');
const model = loadFile('model.ts');
const mockTrip = {
  itinerary_id: 'I-TEST', status: 'CURRENT', version: 2,
  departure_date: '2026-12-10', return_date: '2026-12-12',
  days: [
    { day_id:'D1', day_number:1, date:'2026-12-10', end_deadline:'17:00', activities:[
      { activity_id:'REST1', type:'REST', name:'Nghỉ tại hồ', place_id:'P1', start_time:'13:00', end_time:'14:00', status:'PENDING' },
      { activity_id:'V1', type:'VISIT', name:'Hồ Tuyền Lâm', place_id:'P1', start_time:'14:15', end_time:'15:00', status:'DONE' },
      { activity_id:'V2', type:'VISIT', name:'Vườn hoa', place_id:'P2', start_time:'15:10', end_time:'16:00', status:'PENDING' },
      { activity_id:'T2', type:'TRAVEL', name:'Hồ → vườn hoa', place_id:null, start_time:'15:00', end_time:'15:10', status:'PENDING' },
    ] },
  ],
};
test('map real itinerary IDs, version, day and rest', () => {
  const trip = adapter.fromItinerary(mockTrip);
  assert.equal(trip.id, 'I-TEST');
  assert.equal(trip.version, 2);
  assert.equal(trip.restActivityId, 'REST1');
  assert.equal(trip.placeNames.P1, 'Hồ Tuyền Lâm');
  assert.equal(trip.activities.find(x => x.id === 'V1').status, 'DONE');
  assert.equal(trip.activities.find(x => x.id === 'V2').status, 'TODO');
  assert.equal(model.restPlaceName(trip), 'Hồ Tuyền Lâm');
});
test('map 0 options and exact conflict from F05', () => {
  const value = adapter.mapProposalResponse({
    proposal_id: 'PR1', itinerary_id: 'I-TEST', type:'EXTEND_REST',base_version:2,
    options:[],no_option_reason:'Không đủ thời gian di chuyển',
  });
  assert.equal(value.proposals.length, 0);
  assert.equal(value.conflict, 'Không đủ thời gian di chuyển');
  assert.equal(value.proposalId, 'PR1');
});
test('preserve actual option_id and show before/after', () => {
  const before=mockTrip.days[0].activities[0];
  const after={...before,end_time:'15:00'};
  const value=adapter.mapProposalResponse({
    proposal_id:'PR2', itinerary_id:'I-TEST',type:'EXTEND_REST',base_version:2,
    no_option_reason:null,
    options:[{ option_id:'SERVER-OPT-42', reason:'Đủ giờ',tradeoff:'Bỏ điểm A',estimated_end_time:'16:15',
      proposed_days:mockTrip.days,
      changes:[{activity_id:'REST1',change_type:'EXTEND_REST',before,after}] }],
  });
  assert.equal(value.proposals[0].id,'SERVER-OPT-42');
  assert.equal(value.proposals[0].restUntil,'15:00');
  assert.match(value.proposals[0].summary,/13:00/);
});
test('reject inconsistent F05 payloads', () => {
  assert.throws(()=>adapter.mapProposalResponse({options:[]}));
  assert.throws(()=>adapter.mapProposalResponse({proposal_id:'X',base_version:2,options:[{option_id:'A'}]}));
});
