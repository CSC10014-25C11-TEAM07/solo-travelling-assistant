import * as SecureStore from 'expo-secure-store';
import {Platform} from 'react-native';
const store={getItemAsync:async(k:string)=>Platform.OS==='web'?(typeof localStorage==='undefined'?null:localStorage.getItem(k)):SecureStore.getItemAsync(k),setItemAsync:async(k:string,v:string)=>{if(Platform.OS==='web'){if(typeof localStorage!=='undefined')localStorage.setItem(k,v)}else await SecureStore.setItemAsync(k,v)},deleteItemAsync:async(k:string)=>{if(Platform.OS==='web'){if(typeof localStorage!=='undefined')localStorage.removeItem(k)}else await SecureStore.deleteItemAsync(k)}};
const BASE = (process.env.EXPO_PUBLIC_API_URL || '').trim().replace(/\/$/, '');
export const configured = !!BASE;
export type Place = {place_id:string;name:string;image_url:string|null;reason:string};
export type Activity = {activity_id:string;type:'TRAVEL'|'REST'|'VISIT';name:string;start_time:string;end_time:string;status:'PENDING'|'DONE'|'DROPPED'|'REPLACED';place_id?:string|null};
export type TripDay = {day_id:string;day_number:number;date:string;end_deadline?:string;activities:Activity[]};
export type Trip = {itinerary_id:string;status:'DRAFT'|'CURRENT';version:number;departure_date:string;return_date:string;itinerary_days?:TripDay[];days?:TripDay[]};
export type FormData = {departure_date:string;return_date:string;departure_time:string;min_rest_minutes:string;interests:string[]};
export async function clearSavedTrip(){await store.deleteItemAsync('han_demo_trip')}
export async function clearToken(){await store.deleteItemAsync('access_token')}
export async function token(){try{return await store.getItemAsync('access_token')}catch{return null}}
export async function request(path:string,options:RequestInit={},requiresAuth=true){
 if(!BASE)throw Error('Không thể kết nối dịch vụ. Vui lòng thử lại sau.');
 const t=requiresAuth?await token():null;
 if(requiresAuth&&!t)throw Error('Vui lòng đăng nhập để tiếp tục.');
 const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),15000);
 try{const res=await fetch(BASE+path,{...options,signal:controller.signal,headers:{'Content-Type':'application/json',...(t?{Authorization:`Bearer ${t}`}:{ }),...options.headers}});
 const data=await res.json().catch(()=>({}));if(!res.ok){const error=new Error(data.message||data.detail||`HTTP ${res.status}`) as Error & {status?:number};error.status=res.status;throw error;}return data;
 }catch(e){if(e instanceof Error&&e.name==='AbortError')throw Error('Máy chủ phản hồi quá lâu. Vui lòng thử lại.');throw e}finally{clearTimeout(timeout)}
}
export async function register(username:string,password:string){return request('/api/v1/auth/register',{method:'POST',body:JSON.stringify({username:username.trim().toLowerCase(),password})},false)}
export async function login(username:string,password:string){const data=await request('/api/v1/auth/login',{method:'POST',body:JSON.stringify({username:username.trim().toLowerCase(),password})},false);await store.setItemAsync('access_token',data.access_token);return data}
export async function me(){return request('/api/v1/auth/me')}
export async function logout():Promise<void>{
 // Only a successful response or a confirmed invalid session may end the local session.
 // Network failures, timeouts, and 5xx errors must preserve the saved token.
 try { await request('/api/v1/auth/logout',{method:'POST'}); }
 catch (error) { if ((error as {status?:number}).status !== 401) throw error; }
 await clearToken();
}

export async function recommendations(interests:string[]):Promise<Place[]>{const qs=interests.map(i=>'interests='+encodeURIComponent(i)).join('&');const data=await request('/api/v1/places/recommendations?'+qs);return Array.isArray(data.places)?data.places.slice(0,3):[]}
export async function markDone(tripId:string,activityId:string,version:number):Promise<Trip>{return request(`/api/v1/itineraries/${encodeURIComponent(tripId)}/activities/${encodeURIComponent(activityId)}`,{method:'PATCH',body:JSON.stringify({status:'DONE',base_version:version})})}
// F02/F03: endpoints dự kiến; phải đối chiếu hợp đồng backend trước khi triển khai production.
export async function createDraft(input:FormData):Promise<Trip>{return request('/api/v1/itineraries/draft',{method:'POST',body:JSON.stringify({...input,min_rest_minutes:Number(input.min_rest_minutes)})})}
export async function confirmDraft(id:string):Promise<Trip>{return request(`/api/v1/itineraries/${encodeURIComponent(id)}/confirm`,{method:'POST'})}
export async function latestTrip():Promise<Trip>{return request('/api/v1/itineraries/current')}
