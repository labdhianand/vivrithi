import { getReportDownloadUrl } from "@/lib/api";

export function DownloadButtons({ reportId }: { reportId: string }) {
  return (
    <div className="flex gap-3">
      <a
        href={getReportDownloadUrl(reportId, "docx")}
        download
        className="rounded-lg bg-blue-600 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-700"
      >
        Download CAM Report
      </a>
      <a
        href={getReportDownloadUrl(reportId, "pdf")}
        download
        className="rounded-lg border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 transition-colors hover:bg-slate-50"
      >
        Download PDF
      </a>
    </div>
  );
}
