import type {Trip} from './api';
/** Dữ liệu bàn giao S03 -> S04; không triển khai UI ADAPT của Linh. */
export function buildAdaptHandoff(trip:Trip,activityId?:string){
 if(trip.status!=='CURRENT')throw new Error('Chỉ điều chỉnh lịch đã xác nhận');
 return {itinerary_id:trip.itinerary_id,version:trip.version,activity_id:activityId??null};
}
