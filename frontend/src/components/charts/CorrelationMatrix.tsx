import type { CSSProperties } from 'react'
import type { CorrelationResponse } from '../../types/analytics'

interface CorrelationMatrixProps {
  correlation: CorrelationResponse
}

function getCellStyle(value: number | null): CSSProperties {
  if (value === null || Number.isNaN(value)) {
    return { background: 'rgba(148, 163, 184, 0.12)', color: 'var(--muted-foreground)' }
  }

  const intensity = Math.min(1, Math.abs(value))
  const alpha = 0.12 + intensity * 0.72
  const background = value >= 0 ? `rgba(14, 116, 144, ${alpha})` : `rgba(180, 83, 9, ${alpha})`

  return {
    background,
    color: intensity > 0.55 ? '#ffffff' : 'var(--text)',
    borderColor: value >= 0 ? 'rgba(14, 116, 144, 0.35)' : 'rgba(180, 83, 9, 0.35)',
  }
}

export function CorrelationMatrix({ correlation }: CorrelationMatrixProps) {
  if (!correlation.columns.length) {
    return <p className="inline-note">Correlation requires at least two numeric columns.</p>
  }

  if (!correlation.matrix.length) {
    return <p className="inline-note">{correlation.message || 'Correlation data is not available for this dataset.'}</p>
  }

  return (
    <div className="matrix-scroll">
      <table className="matrix-table">
        <thead>
          <tr>
            <th />
            {correlation.columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {correlation.matrix.map((row, rowIndex) => (
            <tr key={correlation.columns[rowIndex] ?? rowIndex}>
              <th>{correlation.columns[rowIndex] ?? `Column ${rowIndex + 1}`}</th>
              {row.map((value, columnIndex) => (
                <td key={`${rowIndex}-${columnIndex}`} style={getCellStyle(value)}>
                  {value === null ? '—' : value.toFixed(2)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}