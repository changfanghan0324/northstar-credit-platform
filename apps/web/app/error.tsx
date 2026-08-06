"use client";
import { useEffect } from "react";
export default function ErrorPage({error,reset}:{error:Error&{digest?:string};reset:()=>void}){useEffect(()=>{console.error(error);},[error]);return <main className="center-state"><h1>Unable to load Northstar</h1><p>The service may be temporarily unavailable. Your unsaved browser input may still be present.</p><button className="button primary" onClick={reset}>Retry</button></main>;}
