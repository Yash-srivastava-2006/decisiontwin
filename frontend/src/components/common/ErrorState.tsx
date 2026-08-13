interface ErrorStateProps {
  title: string
  message: string
  actionLabel?: string
  onRetry?: () => void
}

export function ErrorState({ title, message, actionLabel = 'Retry', onRetry }: ErrorStateProps) {
  return (
    <div className="error-state" role="alert">
      <div className="error-state__icon">!</div>
      <div>
        <h3>{title}</h3>
        <p>{message}</p>
      </div>
      {onRetry ? (
        <button className="button button--secondary" type="button" onClick={onRetry}>
          {actionLabel}
        </button>
      ) : null}
    </div>
  )
}