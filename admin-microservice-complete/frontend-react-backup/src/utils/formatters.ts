import { format, formatDistanceToNow, parseISO } from 'date-fns';

export const formatDate = (d:string|Date) => { try { return format(typeof d==='string'?parseISO(d):d,'dd MMM yyyy'); } catch { return '-'; } };
export const formatDateTime = (d:string|Date) => { try { return format(typeof d==='string'?parseISO(d):d,'dd MMM yyyy, hh:mm a'); } catch { return '-'; } };
export const timeAgo = (d:string|Date) => { try { return formatDistanceToNow(typeof d==='string'?parseISO(d):d,{addSuffix:true}); } catch { return '-'; } };
export const formatCurrency = (n:number) => `₹${n.toLocaleString('en-IN')}`;
export const formatNumber = (n:number) => n>=1000000?`${(n/1000000).toFixed(1)}M`:n>=1000?`${(n/1000).toFixed(1)}K`:n.toString();
export const truncate = (s:string,len=80) => s.length>len?`${s.substring(0,len)}...`:s;
