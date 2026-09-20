const TONE_BY_VALUE = {
  'Client Confidential': 'critical',
  Confidential: 'critical',
  Internal: 'warning',
  Public: 'good',
}

export default function SensitivityPill({ value }) {
  if (!value) return null
  const tone = TONE_BY_VALUE[value] || 'muted'
  return <span className={`pill pill-${tone}`}>{value}</span>
}
