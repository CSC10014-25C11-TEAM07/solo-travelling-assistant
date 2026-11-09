import React from 'react';
import {Text,TextInput,View} from 'react-native';
import {Action,Page,Header,styles,palette} from '@/features/plan/shared-ui';
export {Action,Page,Header,styles,palette};
export function Field({label,value,onChangeText,secure=false,placeholder}: {label:string;value:string;onChangeText:(v:string)=>void;secure?:boolean;placeholder?:string}){return <View style={{gap:5}}><Text style={styles.heading}>{label}</Text><TextInput autoCapitalize={secure?'none':'none'} secureTextEntry={secure} placeholder={placeholder||label} value={value} onChangeText={onChangeText} style={styles.input}/></View>}
export function Note({children}:{children:React.ReactNode}){return <Text style={styles.muted}>{children}</Text>}
