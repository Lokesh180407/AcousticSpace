import { useState } from "react";
import "./index.css";
import UploadPage from "./pages/UploadPage";
import HistoryPage from "./pages/HistoryPage";

type Page = "upload" | "history";

export default function App() {
  const [page, setPage] = useState<Page>("upload");

  return (
    <main>
      {page === "upload" ? (
        <UploadPage onNavigateToHistory={() => setPage("history")} />
      ) : (
        <HistoryPage onNavigateToUpload={() => setPage("upload")} />
      )}
    </main>
  );
}
