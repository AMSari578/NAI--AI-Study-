import Sidebar from "@/components/layout/Sidebar";

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>
    <Sidebar/>
    <main className="main-shell min-h-screen pb-10 pt-16 lg:ml-[268px] lg:pt-0">
      <div className="mx-auto max-w-[1540px] p-4 sm:p-5 md:p-8 lg:p-10 xl:p-12">{children}</div>
    </main>
  </>;
}
