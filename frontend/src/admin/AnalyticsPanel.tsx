import { useEffect, useState } from 'react'
import { api } from './api'

interface TongQuan {
  metric_date: string
  today_views: number
  audio_plays: number
  searches: number
  page_engaged: number
  devices_today: number
  sessions_today: number
  tracked_online_users: number | null
  presence_available: boolean
  top_pois: { poi_id: string; name: string; views: number; audio_plays: number }[]
  top_searches: { query: string; count: number }[]
  daily: { metric_date: string; views: number; audio_plays: number; searches: number }[]
}

interface CuaSoRuntime {
  window: string
  hours: number
  samples: number
  cells: number
  outcomes: Record<string, number>
}

const CUA_SO: { ma: '24h' | '7d'; ten: string }[] = [
  { ma: '24h', ten: '24 giờ' },
  { ma: '7d', ten: '7 ngày' },
]

function o(a?: number, b?: number): number {
  if (a === undefined || b === undefined || a === 0) return 0
  return Math.round((b / a) * 100)
}

// ADM-005: hai nhóm số liệu tách bạch có chủ đích — analytics chỉ có dữ liệu
// của thiết bị đã consent, còn cửa sổ runtime là chẩn đoán vận hành.
export default function AnalyticsPanel() {
  const [tq, setTQ] = useState<TongQuan | null>(null)
  const [cuaSo, setCuaSo] = useState<'24h' | '7d'>('24h')
  const [runtime, setRuntime] = useState<CuaSoRuntime | null>(null)
  const [loi, setLoi] = useState('')

  useEffect(() => {
    api<TongQuan>('/admin/analytics/summary')
      .then(setTQ)
      .catch(() => setLoi('Không xem được analytics (cần quyền analytics:view)'))
  }, [])

  useEffect(() => {
    api<CuaSoRuntime>(`/admin/runtime-observability/location?window=${cuaSo}`)
      .then(setRuntime)
      .catch(() => setRuntime(null))
  }, [cuaSo])

  if (loi !== '') return <div className="card notice notice--warn">{loi}</div>
  if (tq === null) return <div className="card">Đang tải số liệu…</div>

  const lonNhat = Math.max(1, ...tq.daily.map((d) => d.views))

  return (
    <div>
      <div className="card">
        <h3 className="card__title">Analytics hôm nay ({tq.metric_date})</h3>
        <table className="table">
          <tbody>
            <tr>
              <td>Lượt xem trang</td>
              <td style={{ textAlign: 'right' }}><strong>{tq.today_views}</strong></td>
            </tr>
            <tr>
              <td>Lượt nghe thuyết minh</td>
              <td style={{ textAlign: 'right' }}>{tq.audio_plays}</td>
            </tr>
            <tr>
              <td>Lượt tìm kiếm</td>
              <td style={{ textAlign: 'right' }}>{tq.searches}</td>
            </tr>
            <tr>
              <td>Thiết bị đã consent hôm nay</td>
              <td style={{ textAlign: 'right' }}>{tq.devices_today}</td>
            </tr>
            <tr>
              <td>Phiên hôm nay</td>
              <td style={{ textAlign: 'right' }}>{tq.sessions_today}</td>
            </tr>
            <tr>
              <td>
                Đang online ngay
                <span className="muted"> (thiết bị đã consent, cửa sổ 5 phút)</span>
              </td>
              <td style={{ textAlign: 'right' }}>
                {tq.presence_available ? <strong>{tq.tracked_online_users}</strong> : <span className="muted">chưa có số liệu</span>}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3 className="card__title">Lượt xem 7 ngày gần nhất</h3>
        {tq.daily.length === 0 && <p className="muted">Chưa có dữ liệu.</p>}
        {tq.daily.map((d) => (
          <div key={d.metric_date} className="spread" style={{ marginTop: 6 }}>
            <span className="muted" style={{ minWidth: 96 }}>{d.metric_date.slice(5)}</span>
            <div className="progress" style={{ flex: 1 }}>
              <div className="progress__bar" style={{ width: `${(d.views / lonNhat) * 100}%` }} />
            </div>
            <span style={{ minWidth: 44, textAlign: 'right' }}>{d.views}</span>
          </div>
        ))}
      </div>

      <div className="card">
        <h3 className="card__title">Quán được xem nhiều nhất</h3>
        {tq.top_pois.length === 0 && <p className="muted">Chưa có dữ liệu.</p>}
        <table className="table">
          <tbody>
            {tq.top_pois.map((p) => (
              <tr key={p.poi_id}>
                <td>{p.name || p.poi_id}</td>
                <td style={{ textAlign: 'right' }}>
                  {p.views} xem · {p.audio_plays} nghe · {o(p.views, p.audio_plays)}% nghe
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {tq.top_searches.length > 0 && (
        <div className="card">
          <h3 className="card__title">Từ khoá tìm nhiều</h3>
          <div className="row">
            {tq.top_searches.map((s) => (
              <span key={s.query} className="badge badge--accent">
                {s.query} · {s.count}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <div className="spread">
          <h3 className="card__title">Quan sát vị trí runtime</h3>
          <div className="row">
            {CUA_SO.map((c) => (
              <button
                key={c.ma}
                type="button"
                className={`btn btn--sm${c.ma === cuaSo ? ' btn--primary' : ''}`}
                disabled={c.ma === cuaSo}
                onClick={() => setCuaSo(c.ma)}
              >
                {c.ten}
              </button>
            ))}
          </div>
        </div>
        <p className="muted" style={{ fontSize: '0.82rem', marginTop: 6 }}>
          Kênh chẩn đoán GPS, <strong>không</strong> phải số liệu hành vi khách — tách riêng khỏi analytics
          và không phụ thuộc consent.
        </p>
        {runtime === null ? (
          <p className="muted">Chưa có dữ liệu.</p>
        ) : (
          <table className="table">
            <tbody>
              <tr>
                <td>Mẫu vị trí</td>
                <td style={{ textAlign: 'right' }}>{runtime.samples}</td>
              </tr>
              <tr>
                <td>Ô lưới đã ghi</td>
                <td style={{ textAlign: 'right' }}>{runtime.cells}</td>
              </tr>
              {Object.entries(runtime.outcomes).map(([ten, so]) => (
                <tr key={ten}>
                  <td>Kết quả: {ten}</td>
                  <td style={{ textAlign: 'right' }}>{so}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}