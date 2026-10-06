import { useCallback, useEffect, useState } from 'react'
import MapView from './components/MapView'
import { usePoiStore } from './stores/poiStore'

function App() {
  const { pois, loading, error, fetchPOIs } = usePoiStore()
  const [selectedId, setSelectedId] = useState<string | null>(null)

  useEffect(() => {
    fetchPOIs()
  }, [fetchPOIs])

  const chonPoi = useCallback((id: string) => setSelectedId(id), [])
  const dangChon = pois.find((p) => p.id === selectedId) ?? null

  return (
    <div>
      <h1>Hệ thống du lịch ẩm thực Quận 4</h1>
      <MapView pois={pois} selectedId={selectedId} onSelect={chonPoi} />
      {dangChon !== null && (
        <div>
          <h2>{dangChon.name}</h2>
          <p>{dangChon.description}</p>
        </div>
      )}
      {loading && <p>Đang tải quán...</p>}
      {error !== '' && <p>Bật backend chưa? (uvicorn app.main:app --reload). Lỗi: {error}</p>}
      {!loading && error === '' && pois.length === 0 && <p>Chưa có dữ liệu.</p>}
      <ul>
        {pois.map((poi) => (
          <li key={poi.id}>
            <button type="button" onClick={() => setSelectedId(poi.id)}>
              {poi.name}
            </button>{' '}
            — {poi.description}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default App
