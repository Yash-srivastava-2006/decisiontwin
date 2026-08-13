interface LoadingStateProps {
  label?: string
}

export function LoadingState({ label = 'Loading analytics...' }: LoadingStateProps) {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <div className="loading-state__spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  )
}