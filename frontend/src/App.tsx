import { useEffect, useState } from "react";
import "./styles.css";
type Result = {
  analysisId: string;
  riskLevel: string;
  title: string;
  summary: string;
  actionRequirement: string;
  recommendedActions: { type: string; label: string }[];
  safetyGuidance?: string[];
  originalText?: string;
  originalFile?: { mediaType: string; filename: string } | null;
};
type Api = {
  analyze: (input: string | File) => Promise<Result>;
  history?: () => Promise<Result[]>;
};
const defaultApi = {
  analyze: async (input: string | File): Promise<Result> => {
    const isFile = input instanceof File;
    const r = await fetch("http://localhost:8000/v1/analyses", {
      method: "POST",
      headers: isFile ? undefined : { "content-type": "application/json" },
      body: isFile
        ? (() => {
            const form = new FormData();
            form.append("file", input);
            return form;
          })()
        : JSON.stringify({ text: input }),
    });
    if (!r.ok) throw Error("I couldn't read this right now. Please try again.");
    return r.json();
  },
  history: async (): Promise<Result[]> => {
    const r = await fetch("http://localhost:8000/v1/analyses");
    return r.ok ? r.json() : [];
  },
};
export function App({ api = defaultApi }: { api?: Api }) {
  const [screen, setScreen] = useState<
      "home" | "paste" | "upload" | "reading" | "result" | "history"
    >("home"),
    [text, setText] = useState(""),
    [file, setFile] = useState<File | null>(null),
    [result, setResult] = useState<Result | null>(null),
    [showOriginal, setShowOriginal] = useState(false),
    [history, setHistory] = useState<Result[]>([]),
    [notice, setNotice] = useState(""),
    [pending, setPending] = useState("");
  useEffect(() => {
    if (screen === "history") api.history?.().then(setHistory);
  }, [screen, api]);
  async function submit() {
    setNotice("");
    setScreen("reading");
    try {
      setResult(await api.analyze(file || text));
      setScreen("result");
    } catch (e) {
      setNotice(e instanceof Error ? e.message : "Please try again.");
      setScreen(file ? "upload" : "paste");
    }
  }
  const risk =
    result?.riskLevel === "red"
      ? "Stop and verify before responding."
      : result?.riskLevel === "yellow"
        ? "Please check before acting."
        : "No obvious warning signs.";
  return (
    <main>
      <header>
        <button className="brand" onClick={() => setScreen("home")}>
          What’s this about?
        </button>
      </header>
      {screen === "home" && (
        <section>
          <h1>What’s this about?</h1>
          <p>Choose one to get started.</p>
          <button onClick={() => setScreen("paste")}>Paste a message</button>
          <button disabled>
            Take a picture <small>Coming soon</small>
          </button>
          <button onClick={() => setScreen("upload")}>Upload a document</button>
        </section>
      )}
      {screen === "paste" && (
        <section>
          <h1>Paste a message</h1>
          {notice && <p role="alert">{notice}</p>}
          <label>
            Message
            <textarea value={text} onChange={(e) => setText(e.target.value)} />
          </label>
          <button disabled={!text.trim()} onClick={submit}>
            Continue
          </button>
          <button className="secondary" onClick={() => setScreen("home")}>
            Go back
          </button>
        </section>
      )}
      {screen === "upload" && (
        <section>
          <h1>Upload a document</h1>
          {notice && <p role="alert">{notice}</p>}
          {!file ? (
            <>
              <label htmlFor="document-upload">Choose a file</label>
              <input
                id="document-upload"
                className="file-picker"
                aria-label="Choose a document"
                type="file"
                accept="application/pdf,image/jpeg,image/png,image/webp"
                onChange={(event) => {
                  setNotice("");
                  setFile(event.target.files?.[0] || null);
                }}
              />
              <p>PDF, JPEG, PNG, or WebP. Up to 10 MB.</p>
            </>
          ) : (
            <div className="file-review">
              <strong>{file.name}</strong>
              <p>
                {file.type || "Document"} · {Math.ceil(file.size / 1024)} KB
              </p>
              <button className="secondary" onClick={() => setFile(null)}>
                Remove document
              </button>
            </div>
          )}
          <button disabled={!file} onClick={submit}>
            Continue
          </button>
          <button
            className="secondary"
            onClick={() => {
              setFile(null);
              setScreen("home");
            }}
          >
            Go back
          </button>
        </section>
      )}
      {screen === "reading" && (
        <section aria-live="polite">
          <div className="reading-mark" aria-hidden="true" />
          <h1>I’m reading this…</h1>
          <p>Give me a moment.</p>
        </section>
      )}
      {screen === "result" && result && (
        <section>
          <div className={"risk " + result.riskLevel}>
            <strong>{risk}</strong>
          </div>
          <h1>{result.title}</h1>
          <p>{result.summary}</p>
          <h2>Do I need to do anything?</h2>
          <p>
            {result.actionRequirement === "verify_before_acting"
              ? "Don’t reply or click a link. Verify independently."
              : "No action needed."}
          </p>
          {result.safetyGuidance?.length ? (
            <div className="safety-guidance">
              <h2>What to be careful about</h2>
              <ul>
                {result.safetyGuidance.map((guidance) => (
                  <li key={guidance}>{guidance}</li>
                ))}
              </ul>
            </div>
          ) : null}
          <div>
            {result.recommendedActions.map((a) => (
              <button key={a.type} onClick={() => setPending(a.label)}>
                {a.label}
              </button>
            ))}
          </div>
          {pending && (
            <div role="dialog" aria-label="Confirm action">
              <h2>Confirm {pending}</h2>
              <p>
                This is a practice action. Nothing will be sent outside this
                app.
              </p>
              <button
                onClick={() => {
                  setNotice(
                    `This would ${pending.toLowerCase()}. Nothing was sent outside this app.`,
                  );
                  setPending("");
                }}
              >
                Confirm
              </button>
              <button className="secondary" onClick={() => setPending("")}>
                Cancel
              </button>
            </div>
          )}
          {notice && <p role="status">{notice}</p>}
          <button
            className="secondary"
            onClick={() => setShowOriginal(!showOriginal)}
          >
            {showOriginal
              ? "Hide original"
              : result.originalFile
                ? "Show original document"
                : "Show original message"}
          </button>
          {showOriginal && <pre>{result.originalText}</pre>}
          {showOriginal &&
            result.originalFile &&
            (result.originalFile.mediaType.startsWith("image/") ? (
              <img
                className="original-viewer"
                src={`http://localhost:8000/v1/analyses/${result.analysisId}/original`}
                alt={`Original ${result.originalFile.filename}`}
              />
            ) : (
              <iframe
                className="original-viewer"
                title={`Original ${result.originalFile.filename}`}
                src={`http://localhost:8000/v1/analyses/${result.analysisId}/original`}
              />
            ))}
        </section>
      )}
      {screen === "history" && (
        <section>
          <h1>History</h1>
          {history.length ? (
            history.map((item) => (
              <button
                key={item.analysisId}
                onClick={() => {
                  setResult(item);
                  setScreen("result");
                }}
              >
                {item.title}
              </button>
            ))
          ) : (
            <p>Nothing saved yet.</p>
          )}
        </section>
      )}
      <nav>
        <button onClick={() => setScreen("home")}>Home</button>
        <button onClick={() => setScreen("history")}>History</button>
      </nav>
    </main>
  );
}
