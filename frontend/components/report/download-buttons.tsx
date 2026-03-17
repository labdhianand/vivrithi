import { getReportDownloadUrl } from "@/lib/api";

export function DownloadButtons({ reportId }: { reportId: string }) {
  return (
    <div className="flex gap-3">
      <a
        href={getReportDownloadUrl(reportId, "docx")}
        download
        className="rounded-lg bg-[#e91e8c] px-4 py-2 font-medium text-white transition-colors hover:bg-[#c4187a]"
      >
        Download CAM Report
      </a>
      <a
        href={getReportDownloadUrl(reportId, "pdf")}
        download
        className="rounded-lg border border-[#7a2550] bg-[#3d1a2a] px-4 py-2 font-medium text-[#f48fb1] transition-colors hover:bg-[#4a1530]"
      >
        Download PDF
      </a>
    </div>
  );
}
