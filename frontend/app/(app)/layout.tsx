import Sidebar from "@/components/layout/Sidebar";

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>
    <Sidebar/>
    <main className="main-shell min-h-screen pb-10 pt-16 lg:ml-[282px] lg:pt-0">
      <div className="mx-auto max-w-[1600px] p-4 sm:p-5 md:p-8 lg:p-9 xl:p-10">{children}</div>
    </main>
  </>;
}
