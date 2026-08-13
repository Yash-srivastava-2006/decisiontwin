import { qualityTone } from '../../utils/format'

interface QualityMeterProps {
  score: number
  label: string
}

export function QualityMeter({ score, label }: QualityMeterProps) {
  const tone = qualityTone(score)
  const width = Math.max(0, Math.min(100, score))

  return (
    <div className={`quality-meter quality-meter--${tone}`}>
      <div className="quality-meter__header">
        <div>
          <span className="section-eyebrow">Quality score</span>
          <h3>{score} / 100</h3>
        </div>
        <span className="quality-meter__label">{label}</span>
      </div>
      <div className="quality-meter__track" aria-hidden="true">
        <div className="quality-meter__fill" style={{ width: `${width}%` }} />
      </div>
    </div>
  )
}