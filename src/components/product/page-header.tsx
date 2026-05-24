import type { ReactNode } from "react";

type PageHeaderProps = {
  eyebrow: string;
  title: string;
  description: string;
  action?: ReactNode;
};

export function PageHeader({ eyebrow, title, description, action }: PageHeaderProps) {
  return (
    <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
      <div className="max-w-2xl">
        <div className="mb-3 inline-flex rounded-full border border-civic-cyan/20 bg-civic-cyan/10 px-3 py-1.5 text-xs font-semibold text-civic-cyan">
          {eyebrow}
        </div>
        <h1 className="text-balance text-3xl font-semibold tracking-normal text-white sm:text-5xl">{title}</h1>
        <p className="mt-3 text-pretty text-base leading-7 text-slate-300">{description}</p>
      </div>
      {action}
    </div>
  );
}
