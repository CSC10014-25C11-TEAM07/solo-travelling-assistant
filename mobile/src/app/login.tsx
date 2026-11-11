import {useState} from 'react';
import {router} from 'expo-router';
import {Text,View,Pressable} from 'react-native';
import {Action,Field,Page,styles} from '@/features/plan/ui';
import {usePlan} from '@/features/plan/state';
import {login} from '@/features/plan/api';
export default function Login(){const {setAccount}=usePlan();
 const [u,U]=useState('');const [p,P]=useState('');const [show,S]=useState(false);const [err,E]=useState('');const [busy,B]=useState(false);
 async function submit(){E('');if(!/^[a-z0-9_]{3,30}$/.test(u.trim().toLowerCase()))return E('Tên đăng nhập gồm 3–30 ký tự: a–z, số hoặc _.');if(Array.from(p).length<4||Array.from(p).length>128)return E('Mật khẩu cần 4–128 ký tự.');B(true);try{await login(u,p);setAccount(u.trim().toLowerCase());router.replace('/plan')}catch(e){E(e instanceof Error?e.message:'Không thể đăng nhập.')}finally{B(false)}}
 return <Page>
 <View style={{alignItems:'center',paddingTop:22,gap:12,backgroundColor:'rgba(9,48,39,.95)',borderRadius:26,padding:20,borderWidth:1,borderColor:'rgba(255,255,255,.5)'}}><Text style={{fontSize:15,color:'#123b32',fontWeight:'900',backgroundColor:'#f7f9e6',paddingHorizontal:18,paddingVertical:7,borderRadius:25}}>✦ SOLO TRAVELLING ASSISTANT</Text><Text style={{fontSize:34,fontWeight:'900',color:'#ffffff',textAlign:'center',textShadowColor:'#061f19',textShadowRadius:12,textShadowOffset:{width:0,height:3}}}>Đà Lạt đang chờ bạn khám phá</Text><Text style={{fontSize:17,fontWeight:'700',color:'#163c30',textAlign:'center',backgroundColor:'rgba(255,255,255,.96)',borderRadius:15,padding:9}}>Một mình trên xe máy · Tự do trên mỗi cung đường</Text></View>
 <View style={[styles.card,{marginTop:25,padding:24,backgroundColor:'rgba(255,253,246,0.97)',gap:17}]}>
 <Text style={{fontSize:29,fontWeight:'900',color:'#173d2d',textAlign:'center'}}>Chào mừng trở lại</Text><Text style={{textAlign:'center',color:'#3c584b',fontSize:15,lineHeight:23}}>Đăng nhập để tiếp tục hành trình khám phá, ăn uống và lưu lại lịch trình của riêng bạn.</Text>
 <Field label="Tên đăng nhập" value={u} onChangeText={U} placeholder="Nhập tên đăng nhập"/>
 <Field label="Mật khẩu" secure={!show} value={p} onChangeText={P} placeholder="Nhập mật khẩu"/>
 <Pressable onPress={()=>S(!show)} accessibilityRole="button"><Text style={{color:'#245b45',fontWeight:'800',textAlign:'right'}}>{show?'Ẩn mật khẩu':'👁  Hiện mật khẩu'}</Text></Pressable>
 {!!err&&<Text style={styles.error}>{err}</Text>}
 <Action title={busy?'Đang đăng nhập…':'Đăng nhập  →'} disabled={busy} onPress={submit}/>
 <Action title="Chưa có tài khoản? Đăng ký ngay" secondary onPress={()=>router.push('/register')}/>

 </View></Page>;
}
