import {useEffect,useState} from 'react';
import {router} from 'expo-router';
import {Text,View,Image,Pressable,TextInput} from 'react-native';
import {Action,Field,Page,styles} from '@/features/plan/ui';
import {usePlan,mockTrip} from '@/features/plan/state';
import {configured,recommendations,createDraft,Place} from '@/features/plan/api';
import {LOCAL_PLACES} from '@/features/plan/places';
const opts=[['nature','🌲 Thiên nhiên','Rừng thông · Hồ · Trekking nhẹ'],['coffee','☕ Cà phê','Quán view đẹp · Săn mây'],['culture','🏛 Văn hóa','Kiến trúc · Lịch sử · Nghệ thuật'],['food','🍜 Ẩm thực','Đặc sản · Chợ đêm · Quán địa phương']];
const extras=['🌷 Vườn hoa','📷 Chụp ảnh','🌅 Bình minh','🌇 Ngắm hoàng hôn','🧘 Thư giãn','🍓 Nông trại','🏡 Homestay','🍰 Tiệm bánh','🏞 Thác nước','🛶 Hồ & chèo thuyền','🌿 Vườn thực vật'];
function Choice({label,active,onPress,detail}:{label:string;active:boolean;onPress:()=>void;detail?:string}){return <Pressable accessibilityRole="checkbox" accessibilityState={{checked:active}} onPress={onPress} style={{flexGrow:1,flexBasis:175,minWidth:135,borderRadius:18,padding:13,gap:5,backgroundColor:active?'#e5f5b5':'#f8f8f0',borderWidth:active?2:1,borderColor:active?'#648b39':'#dce4d1'}}><Text style={{fontWeight:'900',fontSize:16,color:'#173e2e'}}>{active?'✓  ':''}{label}</Text>{detail?<Text style={{fontSize:12,lineHeight:18,color:'#476251'}}>{detail}</Text>:null}</Pressable>}
export default function Plan(){
 const {form,setForm,setTrip,selectedIds,setSelectedIds}=usePlan();const [places,SP]=useState<Place[]>([]);const [err,E]=useState('');const [busy,B]=useState(false);const [loading,L]=useState(false);const [extra,SE]=useState<string[]>([]);const [avoid,SAvoid]=useState<string[]>([]);const [company,SCompany]=useState('Một mình');const [stay,SStay]=useState('Homestay');const [meal,SMeal]=useState('Ẩm thực địa phương');const [start,SStart]=useState('TP.HCM');const [note,SNote]=useState('');const [filter,SFilter]=useState('Tất cả');const [search,SSearch]=useState('');const [pace,SPace]=useState('Thư thả');const [budget,SBudget]=useState('Cân bằng');const [transport,STransport]=useState('Xe máy');const [showCatalog,SShowCatalog]=useState(false);
 function change(key:keyof typeof form,value:any){setForm({...form,[key]:value})}
 useEffect(()=>{let active=true;if(!configured||!form.interests.length){SP([]);return}L(true);recommendations(form.interests).then(p=>{if(active)SP(p.slice(0,3))}).catch(e=>{if(active)E(e instanceof Error?e.message:'Lỗi gợi ý')}).finally(()=>{if(active)L(false)});return()=>{active=false}},[form.interests.join(',')]);
 async function submit(){E('');if(!/^\d{4}-\d{2}-\d{2}$/.test(form.departure_date)||!/^\d{4}-\d{2}-\d{2}$/.test(form.return_date))return E('Nhập ngày theo YYYY-MM-DD.');const a=Date.parse(form.departure_date),b=Date.parse(form.return_date);if(!Number.isFinite(a)||!Number.isFinite(b)||b<a)return E('Ngày về phải bằng hoặc sau ngày đi.');const n=Math.round((b-a)/86400000)+1;if(n!==3&&n!==4)return E('Chuyến demo hỗ trợ 3 hoặc 4 ngày.');if(!/^([01]\d|2[0-3]):[0-5]\d$/.test(form.departure_time))return E('Giờ xuất phát phải theo HH:mm.');if(!form.interests.length)return E('Hãy chọn ít nhất một sở thích.');if(!Number.isFinite(Number(form.min_rest_minutes))||Number(form.min_rest_minutes)<=0)return E('Thời gian nghỉ phải lớn hơn 0 phút.');B(true);try{const trip=configured?await createDraft(form):mockTrip(form,selectedIds);setTrip(trip);router.push('/draft')}catch(e){E(e instanceof Error?e.message:'Không tạo được lịch nháp')}finally{B(false)}}
 return <Page>
 <View style={{backgroundColor:'rgba(7,35,31,.94)',padding:24,borderRadius:26,gap:9,borderWidth:1,borderColor:'rgba(255,255,255,.55)'}}>
 <Text style={{fontSize:13,fontWeight:'900',letterSpacing:2,color:'#e1f7a7'}}>✦ SOLO TRAVELLING ASSISTANT</Text>
 <Text style={{fontSize:32,lineHeight:42,fontWeight:'900',color:'#ffffff',textShadowColor:'#0a2b23',textShadowRadius:5}}>Đà Lạt, theo cách của bạn.</Text>
 <Text style={{fontSize:16,lineHeight:24,color:'#f1f9ee',fontWeight:'600'}}>Khám phá Đà Lạt theo sở thích của bạn.</Text>
 </View>
 <View style={styles.card}><Text style={styles.heading}>01 · Thời gian chuyến đi</Text><Text style={styles.muted}>Lịch trình 3–4 ngày</Text>
 <View style={styles.row}><View style={{flex:1,minWidth:160}}><Field label="Ngày đi" value={form.departure_date} onChangeText={v=>change('departure_date',v)} placeholder="YYYY-MM-DD"/></View><View style={{flex:1,minWidth:160}}><Field label="Ngày về" value={form.return_date} onChangeText={v=>change('return_date',v)} placeholder="YYYY-MM-DD"/></View></View>
 <Text style={styles.heading}>Giờ xuất phát</Text><View style={styles.row}>{['05:00','06:00','07:00','08:00','09:00','10:00'].map(v=><View key={v} style={{flexGrow:1,minWidth:86}}><Action title={v} secondary={form.departure_time!==v} onPress={()=>change('departure_time',v)}/></View>)}</View><Field label="Hoặc nhập giờ khác" value={form.departure_time} onChangeText={v=>change('departure_time',v)} placeholder="HH:mm"/>
 </View>
 <View style={styles.card}><Text style={styles.heading}>02 · Sở thích của bạn</Text><Text style={styles.muted}>Có thể chọn nhiều sở thích.</Text>
 <View style={styles.row}>{opts.map(([id,label,detail])=><Choice key={id} label={label} detail={detail} active={form.interests.includes(id)} onPress={()=>change('interests',form.interests.includes(id)?form.interests.filter(x=>x!==id):[...form.interests,id])}/>)}</View>
 <Text style={[styles.heading,{fontSize:17,marginTop:9}]}>Trải nghiệm yêu thích</Text><View style={styles.row}>{extras.map(x=><Choice key={x} label={x} active={extra.includes(x)} onPress={()=>SE(extra.includes(x)?extra.filter(v=>v!==x):[...extra,x])}/>)}</View>
 <Text style={{fontSize:14,fontWeight:'900',color:'#174b34'}}>✓ {form.interests.length} sở thích · {extra.length} trải nghiệm</Text>
 </View>
 <View style={styles.card}><Text style={styles.heading}>03 · Phong cách du lịch</Text>
 <Text style={{fontSize:15,fontWeight:'800',color:'#224c38'}}>Nhịp độ mong muốn</Text><View style={styles.row}>{['Thư thả','Cân bằng','Khám phá nhiều'].map(x=><View key={x} style={{flexGrow:1,minWidth:145}}><Action title={x} secondary={pace!==x} onPress={()=>SPace(x)}/></View>)}</View>
 <Text style={{fontSize:15,fontWeight:'800',color:'#224c38'}}>Ngân sách dự kiến</Text><View style={styles.row}>{['Tiết kiệm','Cân bằng','Thoải mái'].map(x=><View key={x} style={{flexGrow:1,minWidth:145}}><Action title={x} secondary={budget!==x} onPress={()=>SBudget(x)}/></View>)}</View>
 <Text style={{fontSize:15,fontWeight:'800',color:'#224c38'}}>Phương tiện ưu tiên</Text><View style={styles.row}>{['Xe khách','Ô tô','Xe máy'].map(x=><View key={x} style={{flexGrow:1,minWidth:145}}><Action title={x} secondary={transport!==x} onPress={()=>STransport(x)}/></View>)}</View>
 <Text style={styles.heading}>☁ Thời gian nghỉ tối thiểu</Text><View style={styles.row}>{['30','60','90','120'].map(v=><View key={v} style={{flexGrow:1,minWidth:85}}><Action title={v+' phút'} secondary={form.min_rest_minutes!==v} onPress={()=>change('min_rest_minutes',v)}/></View>)}</View><Field label="Nhập số phút nghỉ" value={form.min_rest_minutes} onChangeText={v=>change('min_rest_minutes',v)}/>
 <View style={{backgroundColor:'#edf5e1',padding:12,borderRadius:14}}><Text style={{color:'#345340',fontSize:12,lineHeight:19}}>Những lựa chọn này đang ở chế độ xem thử.</Text></View>
 </View>
 <View style={styles.card}>
 <Text style={styles.heading}>04 · Hành trình theo ý bạn</Text>
 
 <Text style={{fontSize:15,fontWeight:'900',color:'#163c30'}}>Bạn đi cùng ai?</Text>
 <View style={styles.row}>{['Một mình','Bạn bè','Gia đình','Cặp đôi'].map(x=><Choice key={x} label={x} active={company===x} onPress={()=>SCompany(x)}/>)}</View>
 <Text style={{fontSize:15,fontWeight:'900',color:'#163c30'}}>Chỗ ở</Text>
 <View style={styles.row}>{['Homestay','Khách sạn','Resort','Cắm trại'].map(x=><Choice key={x} label={x} active={stay===x} onPress={()=>SStay(x)}/>)}</View>
 <Text style={{fontSize:15,fontWeight:'900',color:'#163c30'}}>Ăn uống</Text>
 <View style={styles.row}>{['Ẩm thực địa phương','Ăn chay','Quán cà phê & bánh','Linh hoạt'].map(x=><Choice key={x} label={x} active={meal===x} onPress={()=>SMeal(x)}/>)}</View>
 <Text style={{fontSize:15,fontWeight:'900',color:'#163c30'}}>Muốn tránh</Text>
 <View style={styles.row}>{['Đông đúc','Đi bộ nhiều','Dậy quá sớm','Di chuyển xa','Lịch trình dày','Chi phí cao','Đường đèo','Hoạt động ngoài trời'].map(x=><Choice key={x} label={x} active={avoid.includes(x)} onPress={()=>SAvoid(avoid.includes(x)?avoid.filter(v=>v!==x):[...avoid,x])}/>)}</View>
 <Text style={{fontSize:15,fontWeight:'900',color:'#163c30'}}>Xuất phát từ</Text>
 <TextInput value={start} onChangeText={SStart} placeholder="Ví dụ: TP.HCM" placeholderTextColor="#687c70" style={styles.input}/>
 <Text style={{fontSize:15,fontWeight:'900',color:'#163c30'}}>Ghi chú riêng</Text>
 <TextInput value={note} onChangeText={SNote} multiline numberOfLines={3} placeholder="Ví dụ: thích ngắm hồ lúc sáng sớm, cần thời gian nghỉ dài..." placeholderTextColor="#687c70" style={[styles.input,{minHeight:95,textAlignVertical:'top'}]}/>
 <View style={{backgroundColor:'#e7f0df',padding:14,borderRadius:15,gap:5}}>
 <Text style={{fontSize:15,fontWeight:'900',color:'#173c30'}}>Lựa chọn của bạn</Text>
 <Text style={{color:'#254438',lineHeight:22,fontSize:14}}>{company} · {stay} · {meal} · {pace} · {budget} · {transport}</Text>
 <Text style={{color:'#254438',lineHeight:22,fontSize:14}}>Trải nghiệm: {extra.length} · Muốn hạn chế: {avoid.length}</Text>
 <Text style={{color:'#486054',lineHeight:19,fontSize:12}}>Tùy chọn mở rộng chưa áp dụng vào lịch tự động.</Text>
 </View>
 </View>
 <View style={styles.card}><Text style={styles.heading}>05 · Khám phá Đà Lạt</Text>
 <Text style={styles.muted}>Chọn tối đa 3 địa điểm yêu thích.</Text>
 <Action title={showCatalog?"Thu gọn danh mục":"Xem tất cả địa điểm"} secondary onPress={()=>SShowCatalog(!showCatalog)}/>
 {showCatalog&&<>
 <TextInput value={search} onChangeText={SSearch} placeholder="🔎 Tìm địa điểm, khu vực..." placeholderTextColor="#61756b" style={styles.input}/>
 <View style={styles.row}>{['Tất cả','Thiên nhiên','Văn hóa','Cà phê','Ẩm thực'].map(x=><Choice key={x} label={x} active={filter===x} onPress={()=>SFilter(x)}/>)}</View>
 <Text style={{color:'#174735',fontWeight:'900'}}>✓ Đã chọn {selectedIds.length}/3 địa điểm</Text>
 {LOCAL_PLACES.filter(p=>(filter==='Tất cả'||p.category===({'Thiên nhiên':'nature','Văn hóa':'culture','Cà phê':'coffee','Ẩm thực':'food'} as Record<string,string>)[filter])&&(`${p.name} ${p.area}`.toLocaleLowerCase('vi').includes(search.toLocaleLowerCase('vi')))).map(p=><Pressable key={p.id} onPress={()=>{if(selectedIds.includes(p.id))setSelectedIds(selectedIds.filter(id=>id!==p.id));else if(selectedIds.length<3)setSelectedIds([...selectedIds,p.id]);else E('Bạn có thể chọn tối đa 3 địa điểm.');}} accessibilityRole="checkbox" accessibilityState={{checked:selectedIds.includes(p.id)}} style={{backgroundColor:selectedIds.includes(p.id)?'#e5f4c8':'#f7f9f3',padding:15,borderRadius:17,borderWidth:2,borderColor:selectedIds.includes(p.id)?'#638e35':'#e0e8da',gap:5}}>
 <Text style={{color:'#143c2e',fontSize:17,fontWeight:'900'}}>{selectedIds.includes(p.id)?'☑':'☐'}  {p.name}</Text>
 <Text style={{color:'#3d5a4b',fontSize:13}}>{p.area} · {p.duration}</Text><Text style={{color:'#294b3c',fontSize:14}}>{p.description}</Text>
 </Pressable>)}
 </>}
 <Text style={{color:'#4a6555',fontSize:12,lineHeight:18}}>Giờ mở cửa có thể thay đổi.</Text>
 </View>
 <View style={styles.card}>
 <Text style={styles.heading}>📍 Dành cho bạn</Text>
 <Text style={styles.muted}>3 địa điểm hợp sở thích.</Text>
 {!configured?<Text style={styles.muted}>Gợi ý mẫu</Text>:loading?<Text style={styles.muted}>Đang tải gợi ý…</Text>:null}
 {(configured?places:LOCAL_PLACES.filter(p=>form.interests.includes(p.category)).slice(0,3).map(p=>({place_id:p.id,name:p.name,image_url:null,reason:`Có thể bạn sẽ thích` }))).slice(0,3).map(p=><View key={p.place_id} style={{gap:5,padding:12,borderRadius:14,backgroundColor:'#f0f6e8'}}>{p.image_url?<Image source={{uri:p.image_url}} style={{width:'100%',height:140,borderRadius:12}}/>:null}<Text style={styles.heading}>{p.name}</Text><Text style={styles.muted}>{p.reason}</Text></View>)}
 {configured&&!loading&&places.length===0?<Text style={styles.muted}>Chưa có gợi ý phù hợp.</Text>:null}
 </View>
 {!!err&&<Text style={styles.error}>{err}</Text>}
 <Action title={busy?'Đang tạo lịch…':'✦ Tạo hành trình của tôi'} disabled={busy} onPress={submit}/><Action title="Xem lịch đã lưu" secondary onPress={()=>router.push('/current')}/>
 </Page>;
}
