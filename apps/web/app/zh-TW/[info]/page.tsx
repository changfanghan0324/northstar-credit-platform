import { InfoPage } from "@/components/InfoPage";
export default async function Page({params}:{params:Promise<{info:string}>}){const {info}=await params;return <InfoPage language="zh-TW" page={info}/>;}
