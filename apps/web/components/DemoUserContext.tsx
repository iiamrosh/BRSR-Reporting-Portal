"use client";
import { createContext, useContext, useEffect, useState } from "react";

const Context = createContext({ userKey:"admin", setUserKey:(_:string)=>{} });
export function DemoUserProvider({children}:{children:React.ReactNode}) {
  const [userKey,setState] = useState("admin");
  useEffect(()=>setState(window.localStorage.getItem("brsr-demo-user") ?? "admin"),[]);
  const setUserKey=(value:string)=>{setState(value);window.localStorage.setItem("brsr-demo-user",value);window.dispatchEvent(new Event("brsr-user-change"));};
  return <Context.Provider value={{userKey,setUserKey}}>{children}</Context.Provider>;
}
export const useDemoUser=()=>useContext(Context);
