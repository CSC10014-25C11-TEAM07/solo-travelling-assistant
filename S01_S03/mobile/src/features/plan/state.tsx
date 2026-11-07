import React,{createContext,useContext,useState,useEffect} from 'react';
import * as SecureStore from 'expo-secure-store';
import {FormData,Trip,Activity} from './api';
import {LOCAL_PLACES} from './places';
const sample:Activity[]=[{activity_id:'A01',type:'VISIT',name:'Ga Đà Lạt',start_time:'08:00',end_time:'09:30',status:'DONE'},{activity_id:'A02',type:'VISIT',name:'Thiền viện Trúc Lâm',start_time:'09:45',end_time:'12:00',status:'DONE'},{activity_id:'R01',type:'REST',name:'Nghỉ trưa',start_time:'13:00',end_time:'14:00',status:'PENDING'},{activity_id:'A03',type:'VISIT',name:'Hồ Xuân Hương',start_time:'14:15',end_time:'15:00',status:'PENDING'},{activity_id:'A04',type:'VISIT',name:'Vườn hoa Đà Lạt',start_time:'15:15',end_time:'16:00',status:'PENDING'}];
export function mockTrip(form:FormData,selectedIds:string[]=[]):Trip{
 const n=Math.max(1,Math.min(4,Math.round((Date.parse(form.return_date)-Date.parse(form.departure_date))/86400000)+1));
 const chosen=selectedIds.length?LOCAL_PLACES.filter(p=>selectedIds.includes(p.id)):LOCAL_PLACES.filter(p=>form.interests.includes(p.category));
 const pool=chosen.length?chosen:LOCAL_PLACES.slice(0,8);
 return {itinerary_id:'MOCK-PLAN-01',status:'DRAFT',version:1,departure_date:form.departure_date,return_date:form.return_date,itinerary_days:Array.from({length:n},(_,i)=>{
 const slots=i===0?['13:30','15:15']:i===n-1?['08:30']:['08:30','10:15','14:00','15:45'];
 const duration=(start:string,minutes:number)=>{const [h,m]=start.split(':').map(Number);const end=h*60+m+minutes;return String(Math.floor(end/60)).padStart(2,'0')+':'+String(end%60).padStart(2,'0')};
 const activities:Activity[]=[...(i===0?[{activity_id:'TRAVEL-0',type:'TRAVEL' as const,name:'Di chuyển đến Đà Lạt',start_time:form.departure_time,end_time:'12:30',status:'PENDING' as const}]:[]),...slots.map((t,j)=>{const p=pool[(i*3+j)%pool.length];return {activity_id:`VISIT-${i}-${j}`,type:'VISIT' as const,name:p.name,place_id:p.id,start_time:t,end_time:duration(t,75),status:'PENDING' as const}}),{activity_id:'REST-'+i,type:'REST' as const,name:'Nghỉ ngơi / ăn trưa',start_time:'12:30',end_time:'13:30',status:'PENDING' as const},...(i===n-1?[{activity_id:'TRAVEL-BACK',type:'TRAVEL' as const,name:'Di chuyển về',start_time:'16:30',end_time:'20:00',status:'PENDING' as const}]:[])];
 return {day_id:'MOCK-D'+(i+1),day_number:i+1,date:new Date(Date.parse(form.departure_date)+i*86400000).toISOString().slice(0,10),end_deadline:'20:00',activities};
 })};
}
type Context={ready:boolean;form:FormData;setForm:(f:FormData)=>void;trip:Trip|null;setTrip:(t:Trip|null)=>void;selectedIds:string[];setSelectedIds:(v:string[])=>void};
const C=createContext<Context|null>(null);
export function PlanProvider({children}:{children:React.ReactNode}){const [form,setForm]=useState<FormData>({departure_date:'2026-12-10',return_date:'2026-12-13',departure_time:'06:00',min_rest_minutes:'60',interests:['nature']});const [trip,setTrip]=useState<Trip|null>(null);const [selectedIds,setSelectedIds]=useState<string[]>([]);const [ready,setReady]=useState(false);useEffect(()=>{SecureStore.getItemAsync('han_demo_trip').then(v=>{if(v){try{const saved=JSON.parse(v) as Trip;if(saved&&saved.itinerary_id&&saved.status==='CURRENT')setTrip(saved)}catch{}}}).finally(()=>setReady(true))},[]);const updateTrip=(value:Trip|null)=>{setTrip(value);if(!process.env.EXPO_PUBLIC_API_URL){if(value?.status==='CURRENT')SecureStore.setItemAsync('han_demo_trip',JSON.stringify(value)).catch(()=>{});else if(value===null)SecureStore.deleteItemAsync('han_demo_trip').catch(()=>{})}};return <C.Provider value={{ready,form,setForm,trip,setTrip:updateTrip,selectedIds,setSelectedIds}}>{children}</C.Provider>}
export function usePlan(){const c=useContext(C);if(!c)throw Error('PlanProvider missing');return c}
export const tripDays=(t:Trip)=>t.itinerary_days||t.days||[];
