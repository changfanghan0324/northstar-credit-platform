import { InfoPage } from "@/components/InfoPage";
import { notFound } from "next/navigation";
const routes=new Set(["methodology","technical-validation","about"]);
export default async function Page({params}:{params:Promise<{info:string}>}){const {info}=await params;if(!routes.has(info))notFound();return <InfoPage language="zh-TW" page={info}/>;}
