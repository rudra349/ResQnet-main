"use client";

import dynamic from "next/dynamic";

const DynamicMap = dynamic(() => import("./LeafletMapInner"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[400px] bg-slate-900 rounded-xl border border-slate-800 flex items-center justify-center text-slate-500 font-mono text-xs animate-pulse">
      Loading Operations Center Map...
    </div>
  ),
});

export function Map(props: any) {
  return <DynamicMap {...props} />;
}
