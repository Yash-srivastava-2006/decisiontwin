import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'
import { useDatasets } from '../hooks/useDataset'
import type { DatasetListItem } from '../types/dataset'

interface ActiveDatasetContextValue {
  activeDatasetId?: string
  activeDataset?: DatasetListItem
  setActiveDatasetId: (datasetId?: string) => void
}

const ActiveDatasetContext = createContext<ActiveDatasetContextValue | undefined>(undefined)
const storageKey = 'decisiontwin.activeDatasetId'

export function ActiveDatasetProvider({ children }: { children: ReactNode }) {
  const datasetsQuery = useDatasets()
  const datasets = datasetsQuery.data || []
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | undefined>(() => localStorage.getItem(storageKey) || undefined)
  const activeDataset = datasets.find((dataset) => dataset.id === selectedDatasetId) || datasets[0]
  const setActiveDatasetId = useCallback((datasetId?: string) => {
    setSelectedDatasetId(datasetId)
    if (datasetId) localStorage.setItem(storageKey, datasetId)
    else localStorage.removeItem(storageKey)
  }, [])
  const value = useMemo(() => ({ activeDatasetId: activeDataset?.id, activeDataset, setActiveDatasetId }), [activeDataset, setActiveDatasetId])
  return <ActiveDatasetContext.Provider value={value}>{children}</ActiveDatasetContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useActiveDataset() {
  const context = useContext(ActiveDatasetContext)
  if (!context) throw new Error('useActiveDataset must be used within ActiveDatasetProvider')
  return context
}
