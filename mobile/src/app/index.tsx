import {useEffect,useState} from 'react';
import {router} from 'expo-router';
import {Text,View} from 'react-native';
import {Action,Page,styles} from '@/features/plan/ui';
import {me,token,logout,clearToken} from '@/features/plan/api';
import {usePlan} from '@/features/plan/state';
export default function Home(){
 const [info,setInfo]=useState('Đang kiểm tra phiên…');const [signed,S]=useState(false);const [busy,B]=useState(false);const {clearSession,setAccount}=usePlan();
 useEffect(()=>{let active=true;(async()=>{const t=await token();if(!active)return;if(!t){router.replace('/login');return}try{await me();if(active){S(true);setAccount('Đã đăng nhập');setInfo('Đã đăng nhập');router.replace('/plan')}}catch(e){if(!active)return;if((e as {status?:number}).status===401){await clearToken();await clearSession();router.replace('/login')}else {setInfo('Không có kết nối. Phiên của bạn vẫn được giữ.');router.replace('/plan')}}})();return()=>{active=false}},[]);
 async function signOut(){B(true);setInfo('');try{await logout();await clearSession();S(false);router.replace('/login')}catch(e){setInfo(e instanceof Error?e.message:'Không thể đăng xuất. Vui lòng thử lại.')}finally{B(false)}}
 return <Page><View style={styles.card}><Text style={styles.title}>Solo Travelling Assistant</Text><Text style={styles.muted}>{info}</Text><Action title="Lên kế hoạch chuyến đi" onPress={()=>router.push('/plan')}/><Action title="Xem lịch đã lưu" secondary onPress={()=>router.push('/current')}/>{signed?<Action title={busy?'Đang đăng xuất…':'Đăng xuất'} disabled={busy} secondary onPress={signOut}/>:<Action title="Đăng nhập" onPress={()=>router.push('/login')}/>}</View></Page>
}
