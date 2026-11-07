import {Stack} from 'expo-router';
import {PlanProvider} from '@/features/plan/state';
export default function Layout(){return <PlanProvider><Stack screenOptions={{headerShown:false}}/></PlanProvider>}
