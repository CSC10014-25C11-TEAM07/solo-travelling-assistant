import {Stack,router,useSegments} from 'expo-router';
import {useEffect} from 'react';
import {PlanProvider} from '@/features/plan/state';
import {token} from '@/features/plan/api';
function SessionGuard(){
 const segments=useSegments();
 useEffect(()=>{let active=true;const page=String(segments[0]||'');
 if(!page||page==='login'||page==='register')return;
 token().then(t=>{if(active&&!t)router.replace('/login')}).catch(()=>{if(active)router.replace('/login')});
 return ()=>{active=false};
 },[segments]);
 return null;
}
export default function Layout(){return <PlanProvider><SessionGuard/><Stack screenOptions={{headerShown:false}}/></PlanProvider>}
