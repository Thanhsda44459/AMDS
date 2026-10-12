import { useCallback, useEffect, useRef, useState } from 'react'
import MapView from './components/MapView'
import ConsentBanner from './components/ConsentBanner'
import LanguagePicker from './components/LanguagePicker'
import OfflinePacks from './components/OfflinePacks'
import { useMapPack } from './components/useMapPack'
import Settings from './components/Settings'
import AdminApp from './admin/AdminApp'
import OwnerApp from './admin/OwnerApp'
import { apiText } from './admin/api'
import { playWithFallback } from './audio/playback'
import { speak } from './geofence/audio'
import { useGeofence } from './geofence/useGeofence'
import { useViTri } from './geofence/useViTri'
import { chonPrefetch, tinhBackoff } from './geofence/prefetch'
import { useStartup } from './startup'
import { batDauAnalytics, ghiSuKien } from './analytics/service'
import { baoMau, batDauQuanSatVịTri } from './telemetry/location'
import { laySessionId, useConsentStore } from './stores/consentStore'
import { usePoiStore } from './stores/poiStore'

const TAB: { ma: 'kham-pha' | 'admin' | 'chu-quan' | 'goi-offline' | 'cai-dat'; ten: string }[] = [
  { ma: 'kham-pha', ten: 'Khám phá' },
  { ma: 'admin', ten: 'Admin' },
  { ma: 'chu-quan', ten: 'Chủ quán' },
  { ma: 'goi-offline', ten: 'Gói offline' },
  { ma: 'cai-dat', ten: 'Cài đặt' },
]

function App() {
  const { pois, loading, error, fetchPOIs, lang } = usePoiStore()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [dangDoc, setDangDoc] = useState<string | null>(null)
  const [tab, setTab] = useState<'kham-pha' | 'admin' | 'chu-quan' | 'goi-offline' | 'cai-dat'>('kham-pha')
  const pack = useMapPack()
  const khoiDong = useStartup()
  const viTri = useViTri()
  const trangThaiConsent = useConsentStore((s) => s.trangThai)
  const langRef = useRef(lang)
  useEffect(() => {
    langRef.current = lang
  })

  // ANA-001: chỉ khi đã đồng ý mới bật; thu hồi consent thì teardown ngay.
  useEffect(() => batDauAnalytics(), [trangThaiConsent])

  // ANA-005: lane runtime chẩn đoán, cố ý không phụ thuộc consent.
  useEffect(() => batDauQuanSatVịTri(laySessionId), [])

  useEffect(() => {
    if (viTri === null) return
    baoMau({ lat: viTri.lat, lng: viTri.lng, outcome: 'ok' })
  }, [viTri])

  // GEO-011: prefetch nền fallback trong 500m, 3/batch, 429 thì backoff.
  useEffect(() => {
    if (viTri === null || pois.length === 0) return
    let dung = false
    let thatBai = 0
    let henGio = 0
    const chay = async () => {
      if (dung) return
      for (const p of chonPrefetch(pois, viTri.lat, viTri.lng)) {
        try {
          const res = await apiText('/audio/on-demand', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ poi_id: p.id, lang: langRef.current }),
          })
          if (res.status === 429) {
            thatBai += 1
            henGio = window.setTimeout(chay, tinhBackoff(thatBai))
            return
          }
          thatBai = 0
        } catch {
          return
        }
      }
      henGio = window.setTimeout(chay, 60000)
    }
    henGio = window.setTimeout(chay, 5000)
    return () => {
      dung = true
      window.clearTimeout(henGio)
    }
  }, [viTri, pois])

  const chonPoi = useCallback((id: string) => setSelectedId(id), [])

  // GEO-004 + AUD-009: vào vòng thì phát 4 tầng, đổi ngôn ngữ thì bỏ cũ.
  const docPoi = useCallback(
    (id: string) => {
      const poi = pois.find((p) => p.id === id)
      if (poi === undefined) return
      setSelectedId(id)
      setDangDoc(poi.name)
      void ghiSuKien('poi_viewed', { poi_id: poi.id, lang: langRef.current })
      void playWithFallback({
        poiId: poi.id,
        lang: langRef.current,
        text: poi.description,
        audioUrl: poi.audio_url,
        isFallback: poi.is_fallback,
        uuTien: poi.audio_priority,
      }).then((tier) => {
        // Chỉ ghi khi thật sự có tiếng; 'bo' nghĩa là bị lượt mới hơn cắt ngang
        // thì tính vào số liệu sẽ làm sai tỉ lệ nghe.
        if (tier !== 'bo') {
          return ghiSuKien('audio_played', { poi_id: poi.id, lang: langRef.current, tier })
        }
      })
    },
    [pois],
  )

  useGeofence(pois, (poi) => docPoi(poi.id))
  const dangChon = pois.find((p) => p.id === selectedId) ?? null

  return (
    <div className="app">
      <header className="app__header">
        <div>
          <h1 className="app__title">Linh Ứng Guide</h1>
          <p className="app__subtitle">Khám phá ẩm thực Quận 4</p>
        </div>
      </header>

      <nav className="app__nav" aria-label="Điều hướng chính">
        {TAB.map((t) => (
          <button
            key={t.ma}
            type="button"
            className={`app__tab${tab === t.ma ? ' app__tab--active' : ''}`}
            onClick={() => setTab(t.ma)}
          >
            {t.ten}
          </button>
        ))}
      </nav>

      {!khoiDong.hoanTat && (
        <div className="notice notice--info">
          Đang khởi động… (nội dung {khoiDong.noiDungSanSang ? 'xong' : 'đang tải'}, giao diện {khoiDong.uiSanSang ? 'xong' : 'đang tải'})
        </div>
      )}
      {khoiDong.hoanTat && <div className="notice notice--ok">Đổi ngôn ngữ hoàn tất: cả hai làn sẵn sàng.</div>}

      <LanguagePicker />

      <ConsentBanner />

      {tab === 'admin' && <AdminApp onPoisChanged={fetchPOIs} />}
      {tab === 'chu-quan' && <OwnerApp />}
      {tab === 'goi-offline' && <OfflinePacks pack={pack} />}
      {tab === 'cai-dat' && <Settings />}
      {tab === 'kham-pha' && (
        <>
          <MapView
            pois={pois}
            selectedId={selectedId}
            onSelect={chonPoi}
            stylePack={(pack.cheDo === 'offline' || (pack.cheDo === 'hybrid' && pack.tamOffline)) ? pack.stylePack : null}
          />

          {dangChon !== null && (
            <section className="card" aria-label="Chi tiết điểm tham quan">
              <div className="spread">
                <h2 className="card__title">{dangChon.name}</h2>
                {dangChon.is_fallback && <span className="badge badge--warn">Nội dung thay thế</span>}
              </div>
              <p className="card__subtitle">{dangChon.description}</p>
              <button className="btn btn--accent" type="button" onClick={() => speak(dangChon.description, 'vi-VN')}>
                ▶ Nghe thuyết minh
              </button>
            </section>
          )}

          {dangDoc !== null && <div className="badge badge--accent mb">Đang đọc: {dangDoc}</div>}
          {loading && <div className="notice notice--info">Đang tải quán…</div>}
          {error !== '' && (
            <div className="notice notice--error">Bật backend chưa? (uvicorn app.main:app --reload). Lỗi: {error}</div>
          )}
          {!loading && error === '' && pois.length === 0 && (
            <div className="notice notice--warn">Chưa có dữ liệu.</div>
          )}

          <ul className="poi-list">
            {pois.map((poi) => (
              <li key={poi.id} className="poi-item">
                <button type="button" className="poi-btn" onClick={() => setSelectedId(poi.id)}>
                  <span className="poi-btn__name">{poi.name}</span>
                  <span className="poi-btn__arrow">›</span>
                  <span className="poi-btn__desc">{poi.description}</span>
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}

export default App
