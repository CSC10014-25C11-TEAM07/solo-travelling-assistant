import {useEffect,useState} from 'react';
import {router} from 'expo-router';
import {Text,View,Image,Pressable,TextInput} from 'react-native';
import {Action,Field,Page,styles} from '@/features/plan/ui';
import {usePlan} from '@/features/plan/state';
import {configured,recommendations,createDraft,logout,Place} from '@/features/plan/api';
import {LOCAL_PLACES} from '@/features/plan/places';
const opts=[['nature','🌲 Thiên nhiên','Rừng thông · Hồ · Trekking nhẹ'],['coffee','☕ Cà phê','Quán view đẹp · Săn mây'],['culture','🏛 Văn hóa','Kiến trúc · Lịch sử · Nghệ thuật'],['food','🍜 Ẩm thực','Đặc sản · Chợ đêm · Quán địa phương']];
const extras=['🌷 Vườn hoa','📷 Chụp ảnh','🌅 Bình minh','🌇 Ngắm hoàng hôn','🧘 Thư giãn','🍓 Nông trại','🍰 Tiệm bánh','🏞 Thác nước','🛶 Hồ & chèo thuyền','🌿 Vườn thực vật'];
function dateToDisplay(iso:string){const m=/^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);return m?`${m[3]}-${m[2]}-${m[1]}`:iso}
function dateToISO(value:string){const m=/^(\d{2})-(\d{2})-(\d{4})$/.exec(value);if(!m)return null;const d=Number(m[1]),mo=Number(m[2]),y=Number(m[3]);const date=new Date(Date.UTC(y,mo-1,d));return date.getUTCFullYear()===y&&date.getUTCMonth()===mo-1&&date.getUTCDate()===d?`${m[3]}-${m[2]}-${m[1]}`:null}
function Choice({label,active,onPress,detail}:{label:string;active:boolean;onPress:()=>void;detail?:string}){return <Pressable accessibilityRole="checkbox" accessibilityState={{checked:active}} onPress={onPress} style={{flexGrow:1,flexBasis:175,minWidth:135,borderRadius:18,padding:13,gap:5,backgroundColor:active?'#e5f5b5':'#f8f8f0',borderWidth:active?2:1,borderColor:active?'#648b39':'#dce4d1'}}><Text style={{fontWeight:'900',fontSize:16,color:'#173e2e'}}>{active?'✓  ':''}{label}</Text>{detail?<Text style={{fontSize:12,lineHeight:18,color:'#476251'}}>{detail}</Text>:null}</Pressable>}
export default function Plan(){
 const {form,setForm,setTrip,selectedIds,setSelectedIds,clearSession}=usePlan();const [places,SP]=useState<Place[]>([]);const [err,E]=useState('');const [busy,B]=useState(false);const [loading,L]=useState(false);const [extra,SE]=useState<string[]>([]);const [avoid,SAvoid]=useState<string[]>([]);const [meal,SMeal]=useState('Ẩm thực địa phương');const [note,SNote]=useState('');const [departureDisplay,SD]=useState(dateToDisplay(form.departure_date));const [returnDisplay,SR]=useState(dateToDisplay(form.return_date));const [filter,SFilter]=useState('Tất cả');const [search,SSearch]=useState('');const [pace,SPace]=useState('Thư thả');const [budget,SBudget]=useState('Cân bằng');const [showCatalog,SShowCatalog]=useState(false);
 function change(key:keyof typeof form,value:any){setForm({...form,[key]:value})}
 function changeDates(dep:string,ret:string){setForm({...form,departure_date:dep,return_date:ret})}
 useEffect(()=>{let active=true;if(!form.interests.length){SP([]);return}L(true);recommendations(form.interests).then(p=>{if(active)SP(p.slice(0,3))}).catch(e=>{if(active)E(e instanceof Error?e.message:'Lỗi gợi ý')}).finally(()=>{if(active)L(false)});return()=>{active=false}},[form.interests.join(',')]);
 async function submit(){E('');const dep=dateToISO(departureDisplay),ret=dateToISO(returnDisplay);if(!dep||!ret)return E('Ngày không hợp lệ. Vui lòng nhập theo ngày-tháng-năm (DD-MM-YYYY).');changeDates(dep,ret);const a=Date.parse(dep),b=Date.parse(ret);if(!Number.isFinite(a)||!Number.isFinite(b)||b<a)return E('Ngày về phải bằng hoặc sau ngày đi.');const today=new Date();const localToday=new Date(today.getFullYear(),today.getMonth(),today.getDate()).getTime();if(a<localToday)return E('Ngày đi không được trước ngày hôm nay.');const n=Math.round((b-a)/86400000)+1;if(n!==3&&n!==4)return E('Vui lòng chọn chuyến đi kéo dài 3 hoặc 4 ngày.');if(!/^([01]\d|2[0-3]):[0-5]\d$/.test(form.departure_time))return E('Giờ xuất phát phải theo HH:mm.');if(!form.interests.length)return E('Hãy chọn ít nhất một sở thích.');if(!Number.isFinite(Number(form.min_rest_minutes))||Number(form.min_rest_minutes)<=0)return E('Thời gian nghỉ phải lớn hơn 0 phút.');B(true);try{const input={...form,departure_date:dep!,return_date:ret!};const trip=await createDraft(input);setTrip(trip);router.push('/draft')}catch(e){E(e instanceof Error?e.message:'Không tạo được lịch nháp')}finally{B(false)}}
 async function signOut(){B(true);E('');try{await logout();await clearSession();router.replace('/login')}catch(e){E(e instanceof Error?e.message:'Đăng xuất thất bại. Vui lòng thử lại.')}finally{B(false)}}
 return <Page>
 <Action title={busy?'Vui lòng đợi…':'Đăng xuất'} secondary disabled={busy} onPress={signOut}/>
 <View style={{backgroundColor:'rgba(7,35,31,.94)',padding:24,borderRadius:26,gap:9,borderWidth:1,borderColor:'rgba(255,255,255,.55)'}}>
 <Text style={{fontSize:13,fontWeight:'900',letterSpacing:2,color:'#e1f7a7'}}>✦ SOLO TRAVELLING ASSISTANT</Text>
 <Text style={{fontSize:32,lineHeight:42,fontWeight:'900',color:'#ffffff',textShadowColor:'#0a2b23',textShadowRadius:5}}>Đà Lạt, theo cách của bạn.</Text>
 <Text style={{fontSize:16,lineHeight:24,color:'#f1f9ee',fontWeight:'600'}}>Hành trình xe máy một mình, tập trung vào điểm đến và ẩm thực.</Text>
 </View>
 <View style={styles.card}><Text style={styles.heading}>01 · Thời gian chuyến đi</Text><Text style={styles.muted}>Lịch trình 3–4 ngày · Nhập ngày theo DD-MM-YYYY</Text>
 <View style={styles.row}><View style={{flex:1,minWidth:160}}><Field label="Ngày đi" value={departureDisplay} onChangeText={SD} placeholder="DD-MM-YYYY"/></View><View style={{flex:1,minWidth:160}}><Field label="Ngày về" value={returnDisplay} onChangeText={SR} placeholder="DD-MM-YYYY"/></View></View>
 <Text style={styles.heading}>Giờ xuất phát</Text><View style={styles.row}>{['05:00','06:00','07:00','08:00','09:00','10:00'].map(v=><View key={v} style={{flexGrow:1,minWidth:86}}><Action title={v} secondary={form.departure_time!==v} onPress={()=>change('departure_time',v)}/></View>)}</View><Field label="Hoặc nhập giờ khác" value={form.departure_time} onChangeText={v=>change('departure_time',v)} placeholder="HH:mm"/>
 </View>
 <View style={styles.card}><Text style={styles.heading}>02 · Sở thích của bạn</Text><Text style={styles.muted}>Có thể chọn nhiều sở thích.</Text>
 <View style={styles.row}>{opts.map(([id,label,detail])=><Choice key={id} label={label} detail={detail} active={form.interests.includes(id)} onPress={()=>change('interests',form.interests.includes(id)?form.interests.filter(x=>x!==id):[...form.interests,id])}/>)}</View>
 <Text style={[styles.heading,{fontSize:17,marginTop:9}]}>Trải nghiệm yêu thích</Text><View style={styles.row}>{extras.map(x=><Choice key={x} label={x} active={extra.includes(x)} onPress={()=>SE(extra.includes(x)?extra.filter(v=>v!==x):[...extra,x])}/>)}</View>
 <Text style={{fontSize:14,fontWeight:'900',color:'#174b34'}}>✓ {form.interests.length} sở thích · {extra.length} trải nghiệm</Text>
 </View>
 <View style={styles.card}><Text style={styles.heading}>03 · Thời gian nghỉ</Text>
 <Text style={styles.heading}>☁ Thời gian nghỉ tối thiểu</Text><View style={styles.row}>{['30','60','90','120'].map(v=><View key={v} style={{flexGrow:1,minWidth:85}}><Action title={v+' phút'} secondary={form.min_rest_minutes!==v} onPress={()=>change('min_rest_minutes',v)}/></View>)}</View><Field label="Nhập số phút nghỉ" value={form.min_rest_minutes} onChangeText={v=>change('min_rest_minutes',v)}/>
 
 </View>
 <View style={styles.card}><Text style={styles.heading}>04 · Điểm xuất phát</Text>
 <View style={{backgroundColor:'#edf5e6',padding:14,borderRadius:12}}><Text style={{color:'#163c30',fontWeight:'800'}}>TP. Hồ Chí Minh</Text><Text style={{color:'#476251',fontSize:12}}>Một mình · Xe máy · Không thể thay đổi điểm xuất phát</Text></View>
 </View>
 <View style={styles.card}><Text style={styles.heading}>05 · Khám phá Đà Lạt</Text>
 <Text style={styles.muted}>Khám phá các địa điểm tham quan, cà phê và ăn uống.</Text>
 {LOCAL_PLACES.filter(p=>form.interests.includes(p.category)).slice(0,6).map(p=><View key={p.id} style={{backgroundColor:'#f7f9f3',padding:13,borderRadius:14,gap:4}}><Text style={{color:'#143c2e',fontWeight:'900'}}>{p.name}</Text><Text style={{color:'#3d5a4b'}}>{p.area} · {p.description}</Text></View>)}
 <Text style={{color:'#4a6555',fontSize:12,lineHeight:18}}>Giờ mở cửa có thể thay đổi.</Text>
 </View>
 <View style={styles.card}>
 <Text style={styles.heading}>📍 Dành cho bạn</Text>
 <Text style={styles.muted}>3 địa điểm hợp sở thích.</Text>
 {loading?<Text style={styles.muted}>Đang tải gợi ý…</Text>:null}
 {places.slice(0,3).map(p=><View key={p.place_id} style={{gap:5,padding:12,borderRadius:14,backgroundColor:'#f0f6e8'}}>{p.image_url?<Image source={{uri:p.image_url}} style={{width:'100%',height:140,borderRadius:12}}/>:null}<Text style={styles.heading}>{p.name}</Text><Text style={styles.muted}>{p.reason}</Text></View>)}
 {!loading&&places.length===0?<Text style={styles.muted}>Chưa có gợi ý phù hợp.</Text>:null}
 </View>
 {!!err&&<Text style={styles.error}>{err}</Text>}
 <Action title={busy?'Đang tạo lịch…':'✦ Tạo hành trình của tôi'} disabled={busy} onPress={submit}/><Action title="Xem lịch đã lưu" secondary onPress={()=>router.push('/current')}/>
 </Page>;
}
