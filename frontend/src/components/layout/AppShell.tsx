import type { ReactNode } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { BarChart3, ChevronDown, LayoutDashboard, Sparkles, Table2, Upload } from 'lucide-react'
import { useDatasets } from '../../hooks/useDataset'
import { useActiveDataset } from '../../context/ActiveDatasetContext'
import { formatDateTime, formatInteger } from '../../utils/format'

interface AppShellProps { children: ReactNode }
const navigation = [
  { label: 'Overview', to: '/', icon: LayoutDashboard },
  { label: 'Datasets', to: '/datasets', icon: Table2 },
  { label: 'Analytics', to: '/analytics', icon: BarChart3 },
  { label: 'Insights', to: '/insights', icon: Sparkles },
]

export function AppShell({ children }: AppShellProps) {
  const { data: datasets = [] } = useDatasets()
  const { activeDataset, setActiveDatasetId } = useActiveDataset()
  const navigate = useNavigate()
  return <div className="app-shell"><aside className="sidebar"><Link to="/" className="brand"><span className="brand__mark">DT</span><span><strong>DecisionTwin AI</strong><small>Analytics dashboard</small></span></Link><nav className="sidebar-nav" aria-label="Primary">{navigation.map((item) => { const Icon = item.icon; return <NavLink key={item.label} to={item.to} className={({ isActive }) => `sidebar-nav__item ${isActive ? 'is-active' : ''}`} end={item.to === '/'}><Icon size={18} /><span>{item.label}</span></NavLink> })}</nav><div className="sidebar-panel"><div className="sidebar-panel__title">Recent datasets</div>{datasets.length ? <div className="sidebar-panel__list">{datasets.slice(0, 4).map((dataset) => <button key={dataset.id} type="button" className="dataset-chip" onClick={() => { setActiveDatasetId(dataset.id); navigate('/analytics') }}><span>{dataset.name}</span><small>{formatInteger(dataset.total_rows)} rows</small></button>)}</div> : <p className="sidebar-panel__empty">Upload your first CSV to populate the dashboard.</p>}</div></aside><div className="shell-main"><header className="topbar"><div className="topbar__dataset"><span className="topbar__label">Dataset</span><button type="button" className="dataset-picker" disabled={!activeDataset} onClick={() => document.getElementById('dataset-menu')?.classList.toggle('is-open')}><span>{activeDataset?.name || 'No dataset selected'}</span><ChevronDown size={16} /></button><div id="dataset-menu" className="dataset-menu" role="menu">{datasets.map((dataset) => <button key={dataset.id} type="button" role="menuitemradio" aria-checked={dataset.id === activeDataset?.id} className={`dataset-menu__item ${dataset.id === activeDataset?.id ? 'is-selected' : ''}`} onClick={() => { setActiveDatasetId(dataset.id); document.getElementById('dataset-menu')?.classList.remove('is-open') }}><span>{dataset.name}</span><small>{formatInteger(dataset.total_rows)} rows</small></button>)}</div>{activeDataset ? <span className="topbar__meta">{formatInteger(activeDataset.total_rows)} rows · {formatDateTime(activeDataset.uploaded_at)}</span> : null}</div><div className="topbar__actions"><Link to="/upload" className="button button--primary"><Upload size={16} />Upload Dataset</Link><button type="button" className="button button--ghost" onClick={() => navigate('/settings')}>Settings</button></div></header><main className="page-content">{children}</main></div></div>
}

