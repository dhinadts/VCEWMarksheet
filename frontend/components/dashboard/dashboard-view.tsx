import Link from "next/link";
import { ArrowUpRight, BookOpenCheck, ClipboardCheck, School, UsersRound } from "lucide-react";

type Stat = { label: string; value: number | string; hint: string; icon: "users" | "school" | "books" | "checks" };
type QuickLink = { label: string; href: string; description: string };

export function DashboardView({ eyebrow, title, subtitle, stats, links }: { eyebrow: string; title: string; subtitle: string; stats: Stat[]; links: QuickLink[] }) {
  const icons = { users: UsersRound, school: School, books: BookOpenCheck, checks: ClipboardCheck };
  return <><div className="page-heading"><div><p className="eyebrow navy">{eyebrow}</p><h1>{title}</h1><p>{subtitle}</p></div></div><section className="stat-grid">{stats.map(stat => { const Icon = icons[stat.icon]; return <article className="stat-card" key={stat.label}><div className="stat-icon"><Icon /></div><span>{stat.label}</span><strong>{stat.value}</strong><small>{stat.hint}</small></article>; })}</section><section className="content-card"><div className="section-heading"><div><h2>Quick access</h2><p>Continue with the most common academic tasks.</p></div></div><div className="quick-grid">{links.map(link => <Link href={link.href} key={link.href} className="quick-link"><div><strong>{link.label}</strong><span>{link.description}</span></div><ArrowUpRight /></Link>)}</div></section></>;
}
