export default function LoadingIndicator({ busy, status }) {
  return <div className="status" role="status" aria-live="polite">
    {busy && <span className="spinner" aria-hidden="true" />}{status}
  </div>;
}
